"""
知识库文档上传/删除与列表接口
"""

import logging
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from ..services.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = (PROJECT_ROOT / rag_service.config.data_path / "user_uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB
SAFE_FILENAME_PATTERN = re.compile(r"[^\w\-.]+")


class KnowledgeDocument(BaseModel):
    filename: str
    size: int
    updated_at: str


class KnowledgeDocumentListResponse(BaseModel):
    documents: List[KnowledgeDocument]
    total: int


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=400, detail="文件编码不受支持，请使用 UTF-8 或 GBK 编码")


def _normalize_upload_filename(filename: str) -> Tuple[str, str]:
    raw_name = (filename or "").strip()
    if not raw_name:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    source_ext = Path(raw_name).suffix.lower()
    if source_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持上传 .md/.txt/.pdf/.docx 文件")

    stem = Path(raw_name).stem.strip()
    safe_stem = SAFE_FILENAME_PATTERN.sub("_", stem).strip("._")
    if not safe_stem:
        safe_stem = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 统一转成 .md，确保能被现有 Markdown 预处理逻辑稳定读取
    return source_ext, f"{safe_stem}.md"


def _safe_document_path(filename: str) -> Path:
    normalized_name = Path(filename).name
    if normalized_name != filename:
        raise HTTPException(status_code=400, detail="非法文件名")

    file_path = (UPLOAD_DIR / normalized_name).resolve()
    if file_path.parent != UPLOAD_DIR:
        raise HTTPException(status_code=400, detail="非法文件路径")
    if file_path.suffix.lower() != ".md":
        raise HTTPException(status_code=400, detail="仅支持删除 .md 文档")

    return file_path


def _build_markdown_content(source_ext: str, source_filename: str, text_content: str) -> str:
    title = Path(source_filename).stem.strip() or "上传文档"
    normalized_text = text_content.strip()

    if not normalized_text:
        raise HTTPException(status_code=400, detail="文档内容为空")

    if source_ext in {".txt", ".pdf", ".docx"}:
        return f"# {title}\n\n{normalized_text}\n"

    # Markdown 文件如果缺少标题，自动补一级标题，提升分块效果
    if not normalized_text.lstrip().startswith("#"):
        return f"# {title}\n\n{normalized_text}\n"
    return f"{normalized_text}\n"


def _extract_text_from_binary_document(data: bytes, source_ext: str) -> str:
    temp_path = None
    try:
        try:
            from unstructured.partition.auto import partition
        except ImportError as e:
            logger.exception("缺少 unstructured 依赖: %s", e)
            raise HTTPException(status_code=500, detail="服务端缺少文档解析依赖，请联系管理员安装 unstructured")

        with tempfile.NamedTemporaryFile(delete=False, suffix=source_ext) as temp_file:
            temp_file.write(data)
            temp_path = temp_file.name

        elements = partition(filename=temp_path)
        text_blocks = []
        for element in elements:
            text = getattr(element, "text", "")
            if text:
                cleaned = text.strip()
                if cleaned:
                    text_blocks.append(cleaned)

        merged_text = "\n\n".join(text_blocks).strip()
        if not merged_text:
            raise HTTPException(status_code=400, detail="无法从该文档提取文本内容，请检查文件是否可读")
        return merged_text
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("解析文档失败: %s", e)
        raise HTTPException(status_code=400, detail=f"文档解析失败：{e}")
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning("清理临时文件失败: %s", e)


def _rebuild_if_ready():
    if not rag_service.is_ready:
        return {
            "status": "skipped",
            "message": "RAG 系统尚未初始化，文档将在初始化后自动生效"
        }
    return rag_service.rebuild_knowledge_base()


@router.get("/documents", response_model=KnowledgeDocumentListResponse)
async def list_documents():
    """获取已上传的知识库文档列表"""
    documents = []
    for path in sorted(UPLOAD_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = path.stat()
        documents.append(KnowledgeDocument(
            filename=path.name,
            size=stat.st_size,
            updated_at=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
        ))

    return KnowledgeDocumentListResponse(documents=documents, total=len(documents))


@router.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    """上传文档到知识库（支持 .md / .txt / .pdf / .docx）"""
    source_ext, target_filename = _normalize_upload_filename(file.filename or "")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="上传文件为空")
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 15MB")

    if source_ext in {".md", ".txt"}:
        text_content = _decode_text(data)
    else:
        text_content = _extract_text_from_binary_document(data, source_ext)
    markdown_content = _build_markdown_content(source_ext, file.filename or target_filename, text_content)

    save_path = _safe_document_path(target_filename)
    save_path.write_text(markdown_content, encoding="utf-8")

    rebuild_result = await run_in_threadpool(_rebuild_if_ready)
    response_status = "success"
    response_message = "文档上传成功"

    if rebuild_result.get("status") == "success":
        response_message = "文档上传成功，知识库已更新"
    elif rebuild_result.get("status") == "error":
        response_status = "warning"
        response_message = f"文档已上传，但知识库更新失败：{rebuild_result.get('message', '未知错误')}"

    return {
        "status": response_status,
        "message": response_message,
        "filename": target_filename,
        "rebuild": rebuild_result
    }


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """删除已上传的知识库文档"""
    file_path = _safe_document_path(filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文档不存在")

    try:
        file_path.unlink()
    except Exception as e:
        logger.exception("删除文档失败: %s", e)
        raise HTTPException(status_code=500, detail="删除文档失败")

    rebuild_result = await run_in_threadpool(_rebuild_if_ready)
    response_status = "success"
    response_message = "文档删除成功"

    if rebuild_result.get("status") == "success":
        response_message = "文档删除成功，知识库已更新"
    elif rebuild_result.get("status") == "error":
        response_status = "warning"
        response_message = f"文档已删除，但知识库更新失败：{rebuild_result.get('message', '未知错误')}"

    return {
        "status": response_status,
        "message": response_message,
        "filename": file_path.name,
        "rebuild": rebuild_result
    }
