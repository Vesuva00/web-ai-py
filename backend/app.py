"""
安全网页服务后端主程序
基于FastAPI的前后端分离架构，支持每日验证码和大模型工作流
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
import secrets
import hashlib
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiofiles
import httpx
import uuid
from contextlib import asynccontextmanager

from config.settings import Settings
from database.models import init_database
from workflows.base import WorkflowManager
from workflows.poem_generator import PoemWorkflow
from utils.logger import setup_logger

# 配置日志
logger = setup_logger(__name__)

# 初始化配置
settings = Settings()

# 数据模型
class LoginRequest(BaseModel):
    username: str
    daily_code: str

class WorkflowRequest(BaseModel):
    workflow_type: str
    inputs: Dict[str, Any]

class UserInfo(BaseModel):
    username: str
    email: EmailStr

# 安全中间件
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await init_database()
    logger.info("数据库初始化完成")
    
    # 启动每日验证码生成任务
    asyncio.create_task(daily_code_generator())
    logger.info("每日验证码生成任务启动")
    
    yield
    
    # 关闭时清理
    logger.info("应用关闭")

# 创建FastAPI应用
app = FastAPI(
    title="安全AI工作流服务",
    description="基于每日验证码的安全AI工作流平台",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# 工作流管理器
workflow_manager = WorkflowManager()
workflow_manager.register_workflow("poem", PoemWorkflow())

# 注册文本分析工作流
from workflows.text_analyzer import TextAnalyzerWorkflow
workflow_manager.register_workflow("text_analyzer", TextAnalyzerWorkflow())

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """验证当前用户token"""
    try:
        token = credentials.credentials
        username = await verify_token(token)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的访问令牌"
            )
        return username
    except Exception as e:
        logger.error(f"用户验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="身份验证失败"
        )

async def verify_token(token: str) -> Optional[str]:
    """验证访问令牌"""
    try:
        async with aiofiles.open("data/active_tokens.json", "r", encoding="utf-8") as f:
            content = await f.read()
            tokens = json.loads(content) if content else {}
        
        if token in tokens:
            token_info = tokens[token]
            # 检查token是否过期（24小时有效期）
            issued_time = datetime.fromisoformat(token_info["issued_at"])
            if datetime.now() - issued_time < timedelta(hours=24):
                return token_info["username"]
        
        return None
    except Exception as e:
        logger.error(f"Token验证错误: {e}")
        return None

async def daily_code_generator():
    """每日验证码生成和发送任务"""
    while True:
        try:
            # 每天凌晨00:01生成新的验证码
            now = datetime.now()
            tomorrow = now.replace(hour=0, minute=1, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (tomorrow - now).total_seconds()
            
            if sleep_seconds > 0:
                await asyncio.sleep(sleep_seconds)
            
            await generate_and_send_daily_codes()
            logger.info("每日验证码生成并发送完成")
            
        except Exception as e:
            logger.error(f"每日验证码生成任务错误: {e}")
            await asyncio.sleep(60)  # 出错后等待1分钟重试

async def generate_and_send_daily_codes():
    """生成并发送每日验证码"""
    try:
        # 读取用户配置
        users = settings.get_users()
        daily_codes = {}
        
        for username, user_info in users.items():
            # 为每个用户生成唯一的6位数字验证码
            code = secrets.randbelow(900000) + 100000
            daily_codes[username] = {
                "code": str(code),
                "generated_at": datetime.now().isoformat(),
                "email": user_info["email"]
            }
            
            # 发送邮件
            await send_daily_code_email(user_info["email"], username, str(code))
        
        # 保存验证码
        async with aiofiles.open("data/daily_codes.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(daily_codes, ensure_ascii=False, indent=2))
        
        logger.info(f"为 {len(users)} 个用户生成并发送了每日验证码")
        
    except Exception as e:
        logger.error(f"生成每日验证码失败: {e}")
        raise

async def send_daily_code_email(email: str, username: str, code: str):
    """发送每日验证码邮件"""
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = f"AI工作流平台每日登录码 - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
        尊敬的 {username}，
        
        您的今日登录验证码是：{code}
        
        此验证码有效期为24小时，请及时使用。
        
        祝您使用愉快！
        AI工作流平台
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 异步发送邮件
        await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: _send_email_sync(msg, email)
        )
        
        logger.info(f"每日验证码邮件已发送至: {email}")
        
    except Exception as e:
        logger.error(f"发送邮件失败 ({email}): {e}")
        raise

def _send_email_sync(msg: MIMEMultipart, email: str):
    """同步发送邮件"""
    server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
    server.starttls()
    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()

# API路由

@app.get("/")
async def read_root():
    """根路径，返回前端页面"""
    return {"message": "AI工作流平台后端服务正在运行"}

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """用户登录接口"""
    try:
        # 验证用户名和验证码
        if not await verify_daily_code(request.username, request.daily_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或验证码错误"
            )
        
        # 生成访问令牌
        token = secrets.token_urlsafe(32)
        
        # 保存token
        await save_access_token(token, request.username)
        
        # 记录登录日志
        await log_user_activity(request.username, "login", {"success": True})
        
        logger.info(f"用户 {request.username} 登录成功")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": request.username
        }
        
    except HTTPException:
        await log_user_activity(request.username, "login", {"success": False})
        raise
    except Exception as e:
        logger.error(f"登录处理错误: {e}")
        await log_user_activity(request.username, "login", {"success": False, "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录处理失败"
        )

async def verify_daily_code(username: str, code: str) -> bool:
    """验证每日验证码"""
    try:
        # 检查用户是否存在
        users = settings.get_users()
        if username not in users:
            return False
        
        # 读取当日验证码
        async with aiofiles.open("data/daily_codes.json", "r", encoding="utf-8") as f:
            content = await f.read()
            daily_codes = json.loads(content) if content else {}
        
        if username not in daily_codes:
            return False
        
        user_code_info = daily_codes[username]
        generated_time = datetime.fromisoformat(user_code_info["generated_at"])
        
        # 检查验证码是否在有效期内（24小时）
        if datetime.now() - generated_time > timedelta(hours=24):
            return False
        
        return user_code_info["code"] == code
        
    except Exception as e:
        logger.error(f"验证码验证错误: {e}")
        return False

async def save_access_token(token: str, username: str):
    """保存访问令牌"""
    try:
        # 读取现有token
        try:
            async with aiofiles.open("data/active_tokens.json", "r", encoding="utf-8") as f:
                content = await f.read()
                tokens = json.loads(content) if content else {}
        except FileNotFoundError:
            tokens = {}
        
        # 添加新token
        tokens[token] = {
            "username": username,
            "issued_at": datetime.now().isoformat()
        }
        
        # 清理过期token
        current_time = datetime.now()
        expired_tokens = []
        for t, info in tokens.items():
            issued_time = datetime.fromisoformat(info["issued_at"])
            if current_time - issued_time > timedelta(hours=24):
                expired_tokens.append(t)
        
        for t in expired_tokens:
            del tokens[t]
        
        # 保存token
        async with aiofiles.open("data/active_tokens.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(tokens, ensure_ascii=False, indent=2))
            
    except Exception as e:
        logger.error(f"保存访问令牌失败: {e}")
        raise

@app.get("/api/auth/me")
async def get_current_user_info(current_user: str = Depends(get_current_user)):
    """获取当前用户信息"""
    users = settings.get_users()
    if current_user in users:
        return {
            "username": current_user,
            "email": users[current_user]["email"]
        }
    raise HTTPException(status_code=404, detail="用户信息未找到")

@app.get("/api/workflows")
async def get_available_workflows(current_user: str = Depends(get_current_user)):
    """获取可用的工作流列表"""
    return {
        "workflows": workflow_manager.get_available_workflows()
    }

@app.post("/api/workflows/execute")
async def execute_workflow(
    request: WorkflowRequest,
    current_user: str = Depends(get_current_user)
):
    """执行工作流"""
    try:
        # 记录请求日志
        await log_user_activity(
            current_user, 
            "workflow_execute", 
            {
                "workflow_type": request.workflow_type,
                "inputs": request.inputs
            }
        )
        
        # 执行工作流
        result = await workflow_manager.execute_workflow(
            request.workflow_type,
            request.inputs,
            current_user
        )
        
        logger.info(f"用户 {current_user} 执行工作流 {request.workflow_type} 成功")
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"工作流执行失败: {e}")
        await log_user_activity(
            current_user,
            "workflow_execute_error",
            {
                "workflow_type": request.workflow_type,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"工作流执行失败: {str(e)}"
        )

async def log_user_activity(username: str, activity_type: str, details: Dict[str, Any]):
    """记录用户活动日志"""
    try:
        conn = sqlite3.connect("data/activity_logs.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO activity_logs (username, activity_type, details)
            VALUES (?, ?, ?)
        """, (username, activity_type, json.dumps(details, ensure_ascii=False)))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"记录用户活动失败: {e}")

@app.get("/api/admin/logs")
async def get_activity_logs(
    current_user: str = Depends(get_current_user),
    limit: int = 100
):
    """获取活动日志（管理员功能）"""
    try:
        conn = sqlite3.connect("data/activity_logs.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, activity_type, details, timestamp
            FROM activity_logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                "username": row[0],
                "activity_type": row[1],
                "details": json.loads(row[2]) if row[2] else {},
                "timestamp": row[3]
            })
        
        conn.close()
        return {"logs": logs}
        
    except Exception as e:
        logger.error(f"获取活动日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取日志失败"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
