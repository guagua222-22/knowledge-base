"""
万象智识库 API 服务

这是一个精简的FastAPI接口，用于连接前端和后端服务。
提供聊天和会话管理功能。
"""
import os
import sys
import json
from typing import Dict, Optional, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 将项目根目录添加到Python路径中
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入主服务模块
from output.main_service import get_response, clear_session_memory

# 创建FastAPI应用
app = FastAPI(
    title="万象智识库 API",
    description="企业知识库智能问答系统API",
    version="1.0.0"
)

# 添加CORS中间件，允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class ChatRequest(BaseModel):
    question: str
    session_id: str

class ClearMemoryRequest(BaseModel):
    session_id: str

# API路由
@app.get("/")
async def root():
    """API状态检查"""
    return {"status": "online", "message": "万象智识库API服务正常运行"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """处理聊天请求，返回完整回答"""
    try:
        # 收集流式结果为完整回答
        full_answer = ""
        metadata = {}
        
        async for chunk in get_response(request.question, request.session_id):
            if chunk["type"] == "content":
                full_answer += chunk["data"]
            elif chunk["type"] == "metadata":
                metadata = chunk["data"]
            elif chunk["type"] == "end" and "metadata" in chunk["data"]:
                metadata.update(chunk["data"]["metadata"])
        
        return {
            "answer": full_answer,
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")

@app.get("/api/chat/stream")
async def chat_stream(question: str, session_id: str):
    """处理流式聊天请求，返回SSE流"""
    
    async def generate_stream():
        try:
            # 直接使用流式处理器
            async for chunk in get_response(question, session_id):
                # 直接转发流式数据
                yield f"data: {json.dumps(chunk)}\n\n"
            
        except Exception as e:
            error_msg = str(e)
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': error_msg}})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )

@app.post("/api/memory/clear")
async def clear_memory(request: ClearMemoryRequest):
    """清除指定会话的记忆"""
    try:
        clear_session_memory(request.session_id)
        return {"status": "success", "message": f"会话 {request.session_id} 的记忆已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除记忆时出错: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 