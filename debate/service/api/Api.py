import asyncio
import io
import logging
import time
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
import dotenv
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel
from fastapi.responses import StreamingResponse, FileResponse
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from config import Settings
from model.model import RunRequest
dotenv.load_dotenv()

# 创建路由实例
router = APIRouter(prefix="/api", tags=["模型接口"])


from agent.DebateManager import DebateManager, MessageContent
config = Settings()
debate_manager = DebateManager(config)

@router.post("/streaming", response_class=EventSourceResponse)
async def streaming(param: RunRequest):
    print(param)
    content = ""
    # for token in ['我', '要', '质询', '小道', '。', '观xx','点']:
    for token, metadata in debate_manager.streaming(param):
        c = token.content
        content += c
        yield ServerSentEvent(data=c, event="token")
    yield ServerSentEvent(data="end", event="token")
    print(f"current content: {content}")
    debate_manager.memory_manager.append(MessageContent(name=param.to_name, text=content, role="assistant"))

@router.get("/listDebaterRoles")
async def listDebaterRoles():
    return debate_manager.listDebaterRoles()

@router.get("/resetMemory")
async def resetMemory():
    """重置对话记忆"""
    debate_manager.memory_manager.clear()
    return {"status": "success", "message": "对话记忆已重置"}

@router.get("/saveMemory")
async def saveMemory():
    """保存对话记忆到文件并返回下载（文件名含日期）"""
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debate_memory_{date_str}.txt"
    debate_manager.memory_manager.write(filename)
    return FileResponse(
        path=filename,
        filename=filename,
        media_type='text/plain',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )