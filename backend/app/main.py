from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.api import auth, conversations, messages
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("正在初始化数据库...")
    try:
        # 创建所有表（如果不存在）
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库初始化完成")
        
        # 打印已创建的表
        print("数据库表：")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
    except Exception as e:
        print(f"❌ 数据库初始化失败：{str(e)}")
    
    yield
    
    # 关闭时执行（如果需要清理资源）
    print("应用正在关闭...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 FastAPI 的多用户 AI 对话系统",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://39.106.139.34:3000"],  # 允许前端地址访问
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(messages.router)


@app.get("/")
def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"} 