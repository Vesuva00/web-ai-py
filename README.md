# AI工作流平台

一个安全的前后端分离网页服务，支持基于每日验证码的用户认证和可扩展的大模型工作流。

## 特性

- 🔐 **安全认证**: 每日生成独立验证码，邮件发送
- 🎨 **美观界面**: 现代化的渐变玻璃效果设计
- 🔧 **可扩展**: 模块化工作流架构，易于添加新功能
- 📝 **诗歌生成**: 基于Qwen API的主题诗歌创作
- 📊 **完整日志**: 详细的用户活动和系统监控日志
- 🗄️ **SQLite数据库**: 轻量级，自动处理并发安全
- ⚙️ **配置管理**: 通过YAML文件管理用户权限

## 快速开始

### 环境要求

- Python 3.8+
- 现代浏览器

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd web-ai-py
```

2. **配置环境**
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件，填写必要信息
nano .env
```

3. **配置用户**
```bash
# 编辑用户配置文件
nano config/users.yaml
```

4. **启动服务**
```bash
# 使用启动脚本（推荐）
python start.py

# 或手动启动
pip install -r requirements.txt
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

5. **访问服务**
打开浏览器访问：http://localhost:8000

## 配置说明

### 环境配置 (.env)

```env
# 邮件配置（必填）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Qwen API配置（必填）
QWEN_API_KEY=your-qwen-api-key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# 安全配置
SECRET_KEY=your-very-secure-secret-key
```

### 用户配置 (config/users.yaml)

```yaml
users:
  admin:
    email: "admin@example.com"
    role: "admin"
    enabled: true
    
  user1:
    email: "user1@example.com"
    role: "user"
    enabled: true
```

## 工作流系统

### 内置工作流

#### 1. 诗歌生成 (poem)
- **输入**: 主题、风格、长度
- **输出**: 诗歌内容、标题、创作说明
- **支持风格**: 现代诗、古典诗、自由诗、律诗、绝句

### 添加新工作流

1. **创建工作流类**
```python
# workflows/your_workflow.py
from workflows.base import BaseWorkflow

class YourWorkflow(BaseWorkflow):
    def get_input_schema(self):
        return {
            "type": "object",
            "properties": {
                "input_field": {"type": "string"}
            },
            "required": ["input_field"]
        }
    
    async def execute(self, inputs, username):
        # 实现你的逻辑
        return {"output": "result"}
```

2. **注册工作流**
```python
# backend/app.py
from workflows.your_workflow import YourWorkflow

workflow_manager.register_workflow("your_workflow", YourWorkflow())
```

## API文档

### 认证接口

- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 工作流接口

- `GET /api/workflows` - 获取可用工作流列表
- `POST /api/workflows/execute` - 执行工作流

### 管理接口

- `GET /api/admin/logs` - 获取系统日志

## 安全特性

- **每日验证码**: 自动生成6位数字验证码
- **Token认证**: 24小时有效期的JWT令牌
- **活动日志**: 完整的用户行为记录
- **并发安全**: SQLite WAL模式，防止数据竞争
- **输入验证**: 严格的参数校验和过滤
- **CORS保护**: 限制跨域访问

## 项目结构

```
web-ai-py/
├── backend/              # 后端服务
│   └── app.py           # FastAPI主应用
├── frontend/            # 前端界面
│   ├── index.html       # 主页面
│   └── app.js          # JavaScript逻辑
├── workflows/           # 工作流模块
│   ├── base.py         # 基础工作流类
│   └── poem_generator.py # 诗歌生成工作流
├── database/            # 数据库模块
│   └── models.py       # 数据模型
├── utils/              # 工具模块
│   └── logger.py       # 日志系统
├── config/             # 配置文件
│   ├── settings.py     # 配置管理
│   └── users.yaml      # 用户配置
├── data/               # 数据目录
├── logs/               # 日志目录
├── requirements.txt    # Python依赖
├── start.py           # 启动脚本
└── README.md          # 项目文档
```

## 部署

### 开发环境
```bash
python start.py
```

### 生产环境

1. **使用Gunicorn**
```bash
pip install gunicorn
gunicorn backend.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. **使用Docker**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "start.py"]
```

3. **Nginx反向代理**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 监控和维护

### 日志文件

- `logs/app.log` - 应用主日志
- `logs/api.log` - API访问日志
- `logs/workflows.log` - 工作流执行日志
- `logs/security.log` - 安全事件日志
- `logs/errors.log` - 错误日志

### 数据库维护

```python
# 清理过期会话
from database.models import SessionManager
await SessionManager.cleanup_expired_sessions()

# 查看统计信息
from database.models import WorkflowLogger
stats = await WorkflowLogger.get_execution_stats()
```

## 故障排除

### 常见问题

1. **验证码未收到**
   - 检查SMTP配置
   - 确认邮箱地址正确
   - 查看logs/security.log

2. **Qwen API调用失败**
   - 检查API密钥配置
   - 确认网络连接
   - 查看logs/workflows.log

3. **数据库锁定**
   - 重启服务自动恢复
   - 检查磁盘空间
   - 查看logs/errors.log

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 许可证

MIT License

## 技术支持

如有问题，请创建Issue或联系维护团队。