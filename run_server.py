"""
启动后端服务器
"""

import os
import sys
from pathlib import Path

# 设置工作目录
project_root = Path(__file__).parent
os.chdir(project_root)

# 加载 .env（数字人 API 需要 VOLC_ACCESS_KEY_ID / VOLC_SECRET_ACCESS_KEY）
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    pass

# 添加项目路径
sys.path.insert(0, str(project_root))

# 设置 Hugging Face 镜像
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🍽️  智能食谱 API 服务器")
    print("=" * 60)
    print()
    print("启动后端服务...")
    print("API 文档: http://localhost:8000/docs")
    print("健康检查: http://localhost:8000/health")
    print()
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )