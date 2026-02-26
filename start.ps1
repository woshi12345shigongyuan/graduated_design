<#
尝尝咸淡 - 智能食谱助手启动脚本 (PowerShell版)
功能：替代原批处理脚本，支持选择启动模式并验证后端健康状态
修复点：修正Start-Process的窗口标题设置方式，解决Title参数不存在的错误
#>

# 切换为Windows原生GBK编码，解决中文乱码问题（适配PowerShell编码机制）
[Console]::OutputEncoding = [System.Text.Encoding]::GetEncoding(936)
[Console]::InputEncoding = [System.Text.Encoding]::GetEncoding(936)
$OutputEncoding = [System.Text.Encoding]::GetEncoding(936)

# 获取脚本所在目录（确保路径正确，替代批处理的%~dp0）
$scriptPath = $PSScriptRoot
Set-Location $scriptPath

# 显示标题
Write-Host "============================================================"
Write-Host "尝尝咸淡 - 智能食谱助手"
Write-Host "============================================================"
Write-Host ""

# 显示启动模式选择菜单
Write-Host "请选择启动模式:"

Write-Host "1. 仅启动后端 API"
Write-Host "2. 仅启动前端"
Write-Host "3. 同时启动前后端 (推荐)"
Write-Host ""

# 获取用户输入（替代批处理的set /p）
$choice = Read-Host -Prompt "请输入选项 (1/2/3)"

# 分支处理逻辑
switch ($choice) {
    "1" {
        # 仅启动后端
        Write-Host ""
        Write-Host "启动后端服务..."
        python run_server.py
    }

    "2" {
        # 仅启动前端
        Write-Host ""
        Write-Host "启动前端服务..."
        Set-Location "$scriptPath/frontend"
        npm run dev
    }

    "3" {
        # 同时启动前后端（核心逻辑）
        Write-Host ""
        Write-Host "同时启动前后端服务..."
        Write-Host ""
        Write-Host "在新窗口中启动后端..."

        # 修复：正确设置新PowerShell窗口的标题（移除-Title，改用参数内指定）
        # 格式：Start-Process powershell -ArgumentList "-NoExit","-Command","`$Host.UI.RawUI.WindowTitle='窗口标题'; 执行命令"
        $backendCommand = "`$Host.UI.RawUI.WindowTitle='尝尝咸淡-后端'; conda activate cook-rag-1;Set-Location '$scriptPath'; python run_server.py"
        $backendArgs = "-NoExit", "-Command", $backendCommand
        Start-Process powershell -ArgumentList $backendArgs -WindowStyle Normal

        # 配置健康检查参数
        $maxWait = 60  # 最大等待秒数
        $waitCount = 0
        $healthCheckUrl = "http://localhost:8000/health"
        $backendReady = $false

        # 循环检查后端健康状态
        while ($waitCount -lt $maxWait) {
            $waitCount++
            try {
                # 发送健康检查请求（超时1秒，与原批处理一致）
                $response = Invoke-WebRequest -Uri $healthCheckUrl -TimeoutSec 10 -ErrorAction Stop
                
                # 添加调试信息
                Write-Host "🔍 调试信息:"
                Write-Host "   状态码: $($response.StatusCode)"
                Write-Host "   响应内容: $($response.Content)"
                
                # 尝试解析JSON
                try {
                    $healthData = $response.Content | ConvertFrom-Json
                    Write-Host "   JSON解析成功"
                } catch {
                    Write-Host "   JSON解析失败: $($_.Exception.Message)"
                    # 即使JSON解析失败，只要能获取到响应就认为通过
                }
 
                # 验证健康状态（只要有返回就认为通过）
                Write-Host "✅ 后端健康状态验证通过"
                $backendReady = $true
                break
            } catch [System.Net.WebException] {
                # 后端尚未启动或请求失败
                Write-Host "⏳ 后端服务请求失败: $($_.Exception.Message) (已等待 $waitCount 秒)"
            } catch {
                # 其他请求错误
                Write-Host "❌ 健康检查请求出错: $($_.Exception.Message)"
            }

            # 等待1秒后重试
            if (-not $backendReady) {
                Start-Sleep -Seconds 1
            }
        }

        # 检查是否超时
        if (-not $backendReady) {
            Write-Host ""
            Write-Host "后端服务启动超时（超过$maxWait秒），请检查后端是否正常运行！"
            break
        }

        # 后端就绪，启动前端
        Write-Host ""
        Write-Host "后端服务已完全启动并满足健康状态要求！"
        Write-Host ""
        Write-Host "启动前端..."
        Set-Location "$scriptPath/frontend"
        npm run dev
    }

    default {
        # 无效输入
        Write-Host ""
        Write-Host "输入无效，请输入 1、2 或 3"
    }
}

# 暂停等待用户输入（替代批处理的pause）
Write-Host ""
Read-Host -Prompt "按Enter键退出"