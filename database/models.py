"""
数据库模型和初始化
使用SQLite确保并发安全
"""

import sqlite3
import asyncio
import threading
import os
from contextlib import contextmanager
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

# 数据库文件路径
DB_PATH = "data/app.db"

# 数据库连接池（线程安全）
_local = threading.local()

@contextmanager
def get_db_connection():
    """获取数据库连接（线程安全）"""
    if not hasattr(_local, 'connection'):
        _local.connection = sqlite3.connect(
            DB_PATH,
            check_same_thread=False,
            timeout=30.0  # 30秒超时
        )
        _local.connection.execute("PRAGMA journal_mode=WAL")  # 启用WAL模式提高并发性能
        _local.connection.execute("PRAGMA synchronous=NORMAL")
        _local.connection.execute("PRAGMA cache_size=10000")
        _local.connection.execute("PRAGMA temp_store=memory")
    
    try:
        yield _local.connection
    except Exception as e:
        _local.connection.rollback()
        raise e

async def init_database():
    """初始化数据库表"""
    os.makedirs("data", exist_ok=True)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 创建用户活动日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT
            )
        """)
        
        # 创建工作流执行记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                workflow_type TEXT NOT NULL,
                inputs TEXT,
                outputs TEXT,
                status TEXT DEFAULT 'success',
                execution_time_ms INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT
            )
        """)
        
        # 创建系统配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建用户会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # 创建API调用统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER,
                response_time_ms INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引优化查询性能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_activity_logs_username_timestamp 
            ON activity_logs(username, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_workflow_executions_username_timestamp 
            ON workflow_executions(username, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_username 
            ON user_sessions(username)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_usage_stats_username_timestamp 
            ON api_usage_stats(username, timestamp)
        """)
        
        conn.commit()

class ActivityLogger:
    """活动日志记录器"""
    
    @staticmethod
    async def log_activity(
        username: str,
        activity_type: str,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """记录用户活动"""
        try:
            details_json = json.dumps(details or {}, ensure_ascii=False)
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO activity_logs 
                    (username, activity_type, details, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, activity_type, details_json, ip_address, user_agent))
                conn.commit()
                
        except Exception as e:
            print(f"记录活动日志失败: {e}")
    
    @staticmethod
    async def get_recent_activities(username: str = None, limit: int = 100) -> List[Dict]:
        """获取最近的活动记录"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if username:
                    cursor.execute("""
                        SELECT username, activity_type, details, timestamp, ip_address
                        FROM activity_logs
                        WHERE username = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (username, limit))
                else:
                    cursor.execute("""
                        SELECT username, activity_type, details, timestamp, ip_address
                        FROM activity_logs
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))
                
                activities = []
                for row in cursor.fetchall():
                    activities.append({
                        "username": row[0],
                        "activity_type": row[1],
                        "details": json.loads(row[2]) if row[2] else {},
                        "timestamp": row[3],
                        "ip_address": row[4]
                    })
                
                return activities
                
        except Exception as e:
            print(f"获取活动记录失败: {e}")
            return []

class WorkflowLogger:
    """工作流执行日志记录器"""
    
    @staticmethod
    async def log_execution(
        username: str,
        workflow_type: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any] = None,
        status: str = "success",
        execution_time_ms: int = 0,
        error_message: str = None
    ):
        """记录工作流执行"""
        try:
            inputs_json = json.dumps(inputs, ensure_ascii=False)
            outputs_json = json.dumps(outputs or {}, ensure_ascii=False)
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO workflow_executions 
                    (username, workflow_type, inputs, outputs, status, execution_time_ms, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (username, workflow_type, inputs_json, outputs_json, status, execution_time_ms, error_message))
                conn.commit()
                
        except Exception as e:
            print(f"记录工作流执行失败: {e}")
    
    @staticmethod
    async def get_execution_stats(username: str = None) -> Dict[str, Any]:
        """获取执行统计信息"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 基础查询条件
                where_clause = "WHERE username = ?" if username else ""
                params = (username,) if username else ()
                
                # 总执行次数
                cursor.execute(f"""
                    SELECT COUNT(*) FROM workflow_executions {where_clause}
                """, params)
                total_executions = cursor.fetchone()[0]
                
                # 成功率
                cursor.execute(f"""
                    SELECT COUNT(*) FROM workflow_executions 
                    {where_clause} {"AND" if username else "WHERE"} status = 'success'
                """, params)
                successful_executions = cursor.fetchone()[0]
                
                # 按工作流类型统计
                cursor.execute(f"""
                    SELECT workflow_type, COUNT(*) 
                    FROM workflow_executions {where_clause}
                    GROUP BY workflow_type
                """, params)
                workflow_stats = dict(cursor.fetchall())
                
                # 平均执行时间
                cursor.execute(f"""
                    SELECT AVG(execution_time_ms) 
                    FROM workflow_executions 
                    {where_clause} {"AND" if username else "WHERE"} status = 'success'
                """, params)
                avg_execution_time = cursor.fetchone()[0] or 0
                
                return {
                    "total_executions": total_executions,
                    "successful_executions": successful_executions,
                    "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
                    "workflow_stats": workflow_stats,
                    "avg_execution_time_ms": round(avg_execution_time, 2)
                }
                
        except Exception as e:
            print(f"获取执行统计失败: {e}")
            return {}

class SessionManager:
    """会话管理器"""
    
    @staticmethod
    async def create_session(token: str, username: str):
        """创建用户会话"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO user_sessions (token, username)
                    VALUES (?, ?)
                """, (token, username))
                conn.commit()
                
        except Exception as e:
            print(f"创建会话失败: {e}")
    
    @staticmethod
    async def validate_session(token: str) -> Optional[str]:
        """验证会话并返回用户名"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT username FROM user_sessions
                    WHERE token = ? AND is_active = TRUE
                    AND datetime(created_at, '+1 day') > datetime('now')
                """, (token,))
                
                result = cursor.fetchone()
                if result:
                    # 更新最后活动时间
                    cursor.execute("""
                        UPDATE user_sessions 
                        SET last_active = CURRENT_TIMESTAMP
                        WHERE token = ?
                    """, (token,))
                    conn.commit()
                    return result[0]
                
                return None
                
        except Exception as e:
            print(f"验证会话失败: {e}")
            return None
    
    @staticmethod
    async def invalidate_session(token: str):
        """使会话失效"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_sessions 
                    SET is_active = FALSE
                    WHERE token = ?
                """, (token,))
                conn.commit()
                
        except Exception as e:
            print(f"使会话失效失败: {e}")
    
    @staticmethod
    async def cleanup_expired_sessions():
        """清理过期会话"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM user_sessions
                    WHERE datetime(created_at, '+1 day') <= datetime('now')
                """)
                conn.commit()
                
        except Exception as e:
            print(f"清理过期会话失败: {e}")

# 导出主要类和函数
__all__ = [
    'init_database',
    'ActivityLogger', 
    'WorkflowLogger',
    'SessionManager',
    'get_db_connection'
]
