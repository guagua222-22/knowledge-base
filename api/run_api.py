"""
API服务启动脚本

运行此脚本启动万象智识库API服务
"""
import uvicorn

if __name__ == "__main__":
    print("正在启动万象智识库API服务...")
    uvicorn.run("main:app", 
                host="0.0.0.0", 
                port=8000, 
                reload=True,
                log_level="info") 