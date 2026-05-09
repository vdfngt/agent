import logging

from fastapi import FastAPI
import uvicorn
from api.Api import router as api_router
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 设置日志模版
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',filename='myapp.log',filemode='a',encoding='utf-8')
logging.getLogger("root").setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("应用启动")
    yield
    logging.info("应用关闭")

app = FastAPI(
    lifespan=lifespan
)

# 添加跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境建议指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)
# 注册API路由
app.include_router(api_router)

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)