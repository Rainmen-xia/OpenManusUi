# 导入补丁文件，修复six.moves导入问题
import six_patch  # 这行必须放在其他导入语句之前

import datetime
import json
import os
from pathlib import Path
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
from uuid import uuid4
from contextlib import asynccontextmanager
from pydantic import BaseModel

from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from app.agent.manus import Manus
from app.logger import logger

# 全局状态管理
active_tasks = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    yield
    # 关闭时清理所有任务
    for task_id in list(active_tasks.keys()):
        await stop_task(task_id)


# 请求数据模型
class ExecuteRequest(BaseModel):
    deploy_type: str  # local/cloud
    model_name: str
    api_key: Optional[str] = None
    prompt: str

app = FastAPI(lifespan=lifespan)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（添加在路由定义前）
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def redirect_to_index():
    return RedirectResponse(url="/static/index.html")


@app.post("/execute")
# @limiter.limit("10")
async def execute_request(request: ExecuteRequest):
    # 参数验证
    if request.deploy_type == "cloud" and not request.api_key:
        raise HTTPException(400, "API key required for cloud models")

    """启动执行任务并返回任务ID"""
    task_id = str(uuid4())
    queue = asyncio.Queue()

    # 创建后台任务
    task = asyncio.create_task(
        run_agent_task(task_id, request.model_name, request.api_key, request.prompt, queue)
    )

    # 存储任务状态
    active_tasks[task_id] = {
        "task": task,
        "queue": queue,
        "status": "running"
    }

    return {"task_id": task_id}


@app.get("/stream/{task_id}")
async def stream_results(task_id: str):
    """获取任务执行流"""
    if task_id not in active_tasks:
        raise HTTPException(404, "Task not found")

    queue = active_tasks[task_id]["queue"]

    async def event_generator():
        while active_tasks.get(task_id, {}).get("status") == "running" or active_tasks.get(task_id, {}).get("status") == "terminate":
            try:
                # # 非阻塞获取队列消息
                raw_message = await asyncio.wait_for(queue.get(), timeout=1.0)
                # yield {"data": message}
                # 包装为结构化数据
                message = jsonable_encoder({
                    "type": "log",  # 消息类型标识
                    "content": raw_message,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                # 严格遵循SSE格式
                yield f"data: {json.dumps(message)}\n\n"
                queue.task_done()
            except asyncio.TimeoutError:
                continue

        # 任务结束后的清理
        if task_id in active_tasks:
            del active_tasks[task_id]

    return EventSourceResponse(event_generator())


@app.post("/stop/{task_id}")
async def stop_execution(task_id: str):
    """停止正在执行的任务"""
    await stop_task(task_id)
    return {"status": "stopped"}


async def run_agent_task(task_id: str, model: str, api_key: str, prompt: str, queue: asyncio.Queue):
    """执行Agent任务的核心逻辑"""
    try:
        agent = Manus()
        agent.update_llm_config(model, api_key)

        # 重定向日志到队列
        original_info = logger.info
        def custom_log(msg):
            original_info(msg)
            queue.put_nowait(f"{msg}")
        logger.info = custom_log

        while True:
            # 检查终止信号
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=0.5)
                if msg.get("type") == "terminate":
                    queue.put_nowait(f"收到终止信号，退出任务 {task_id}")
                    logger.info(f"收到终止信号，退出任务 {task_id}")
                    return
            except asyncio.TimeoutError:
                pass

            result = await agent.run(prompt)
            await queue.put({
                "type": "progress",
                "content": f"处理进度: {result}"
            })
    except asyncio.CancelledError:
        logger.warning(f"任务 {task_id} 被强制取消")
        await queue.put({
            "type": "error",
            "content": "任务被用户终止"
        })
    finally:
        queue.task_done()
        logger.info = original_info  # 恢复原始日志


async def stop_task(task_id: str):
    """增强版任务终止函数"""
    if task_id not in active_tasks:
        return False

    task_data = active_tasks[task_id]

    try:
        # 发送终止信号到任务队列
        await task_data["queue"].put({"type": "terminate"})

        # 取消异步任务
        task_data["task"].cancel()

        # 等待任务完成清理
        await asyncio.wait_for(task_data["task"], timeout=5)

    except asyncio.CancelledError:
        logger.info(f"任务 {task_id} 已取消")
    except Exception as e:
        logger.error(f"终止任务异常: {str(e)}")
    finally:
        # 清理资源
        if task_id in active_tasks:
            del active_tasks[task_id]


# 文件系统相关模型
class FileItem(BaseModel):
    name: str
    path: str
    type: str  # "file" 或 "directory"
    size: Optional[int] = None
    last_modified: Optional[str] = None

@app.get("/api/workspace", response_model=List[FileItem])
async def list_workspace_files(path: str = ""):
    """获取workspace目录下的文件列表"""
    try:
        # 构建完整路径，确保不会访问到workspace之外的目录
        base_path = Path("workspace")
        target_path = base_path / path if path else base_path
        
        # 安全检查：确保目标路径是workspace的子目录
        if not str(target_path.resolve()).startswith(str(base_path.resolve())):
            raise HTTPException(403, "Access denied: Cannot access directories outside workspace")
        
        # 检查路径是否存在
        if not target_path.exists():
            raise HTTPException(404, f"Path not found: {path}")
        
        # 如果是文件而非目录，则返回文件信息
        if target_path.is_file():
            stats = target_path.stat()
            return [FileItem(
                name=target_path.name,
                path=str(target_path.relative_to(base_path)),
                type="file",
                size=stats.st_size,
                last_modified=datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
            )]
        
        # 获取目录内容
        result = []
        for item in target_path.iterdir():
            stats = item.stat()
            result.append(FileItem(
                name=item.name,
                path=str(item.relative_to(base_path)),
                type="directory" if item.is_dir() else "file",
                size=stats.st_size if item.is_file() else None,
                last_modified=datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
            ))
        
        # 按类型和名称排序：先目录后文件，每种类型内按名称排序
        result.sort(key=lambda x: (0 if x.type == "directory" else 1, x.name))
        return result
    
    except Exception as e:
        logger.error(f"Error listing workspace files: {str(e)}")
        raise HTTPException(500, f"Error listing files: {str(e)}")

@app.get("/api/file-content", response_class=PlainTextResponse)
async def get_file_content(path: str = ""):
    """获取文件内容"""
    try:
        # 构建完整路径，确保不会访问到workspace之外的目录
        base_path = Path("workspace")
        target_path = base_path / path if path else base_path
        
        # 安全检查：确保目标路径是workspace的子目录
        if not str(target_path.resolve()).startswith(str(base_path.resolve())):
            raise HTTPException(403, "Access denied: Cannot access files outside workspace")
        
        # 检查路径是否存在
        if not target_path.exists():
            raise HTTPException(404, f"File not found: {path}")
        
        # 检查是否是文件
        if not target_path.is_file():
            raise HTTPException(400, f"Not a file: {path}")
        
        # 读取文件内容
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            # 如果不是文本文件，返回错误
            raise HTTPException(400, "Cannot read binary file as text")
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error reading file content: {str(e)}")
        raise HTTPException(500, f"Error reading file: {str(e)}")
