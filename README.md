# AI工作流系统

一个安全的前后端分离Web服务，提供基于大模型的多种工作流功能，通过每日验证码进行访问控制。

## 主要特性

- 🔐 **安全认证**: 基于每日验证码的访问控制
- 🤖 **AI工作流**: 可扩展的大模型工作流框架
- 📧 **邮件通知**: 自动发送每日验证码到管理员邮箱
- 📊 **完整日志**: 记录所有用户操作和系统事件
- 🎨 **现代UI**: 响应式的美观前端界面
- 🐳 **容器化**: 支持Docker一键部署
- 🛡️ **生产就绪**: 完整的安全配置和监控

## 架构设计

### 后端技术栈
- **Flask**: Web框架
- **SQLite**: 数据库（支持并发安全）
- **JWT**: 身份验证
- **SQLAlchemy**: ORM
- **Gunicorn**: WSGI服务器

### 前端技术栈
- **原生JavaScript**: 核心逻辑
- **Bootstrap 5**: UI框架
- **Particles.js**: 动效背景

### 安全特性
- HTTPS强制跳转
- 安全HTTP头配置
- 请求频率限制
- SQL注入防护
- XSS防护
- CSRF防护

## 快速开始

### 1. 环境准备

```bash
git clone <repository-url>
cd web-ai-py
```

### 2. 配置环境变量

复制环境变量模板：
```bash
cp .env.example .env
```

编辑`.env`文件，填入真实配置：
```bash
# 应用配置
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=False

# 邮件配置
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@example.com

# API配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 3. 部署方式

#### 方式一：Docker部署（推荐）

```bash
# 执行部署脚本
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

#### 方式二：手动部署

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
cd backend
python init_db.py

# 启动后端服务
gunicorn --bind 0.0.0.0:5000 app:app

# 启动前端服务（使用nginx或其他静态文件服务器）
```

### 4. 配置每日验证码

设置定时任务（crontab），每日自动生成验证码：

```bash
# 编辑定时任务
crontab -e

# 添加以下行（每日凌晨0点执行）
0 0 * * * /path/to/web-ai-py/scripts/generate_daily_code.py
```

### 5. SSL证书配置

将SSL证书文件放置到`ssl/`目录：
- `ssl/cert.pem` - 证书文件
- `ssl/key.pem` - 私钥文件

## 使用说明

### 用户注册与登录

1. 访问系统首页
2. 新用户点击"立即注册"创建账号
3. 使用用户名、密码和每日验证码登录

### 工作流使用

#### 诗歌生成器
- 输入主题和诗歌风格
- 系统生成相应的诗歌作品

#### 文本摘要
- 输入需要摘要的文本
- 设置摘要长度
- 获取智能摘要结果

### 查看历史记录

登录后在"调用历史"页面可以查看：
- 所有工作流调用记录
- 执行时间和状态
- Token使用情况

## 扩展开发

### 添加新的工作流

1. 在`backend/workflows.py`中创建新的工作流类：

```python
class NewWorkflow(BaseWorkflow):
    def validate_input(self, input_data):
        # 验证输入逻辑
        pass
    
    def process(self, input_data):
        # 处理逻辑
        pass
```

2. 在`WORKFLOW_REGISTRY`中注册：

```python
WORKFLOW_REGISTRY = {
    'new_workflow': NewWorkflow,
    # ... 其他工作流
}
```

3. 在前端`app.js`中添加UI配置：

```javascript
const workflowConfigs = {
    new_workflow: {
        title: '新工作流',
        description: '描述',
        icon: 'fas fa-icon',
        color: 'primary'
    }
};
```

## 监控与维护

### 日志查看

```bash
# 查看应用日志
docker-compose logs -f web-ai-py

# 查看Nginx日志
docker-compose logs -f nginx

# 查看应用运行日志
tail -f logs/app.log
```

### 数据库维护

```bash
# 备份数据库
cp data/app.db data/app_backup_$(date +%Y%m%d).db

# 查看数据库状态
sqlite3 data/app.db ".schema"
```

### 性能监控

系统提供以下监控端点：
- `/health` - 健康检查
- 完整的访问日志记录
- 错误日志自动记录

## 安全建议

1. **定期更新密钥**: 更换SECRET_KEY和API密钥
2. **监控访问日志**: 检查异常访问模式
3. **备份数据**: 定期备份数据库和配置
4. **SSL证书**: 确保证书及时续期
5. **系统更新**: 保持依赖包和系统的最新版本

## 常见问题

### Q: 每日验证码无法发送？
A: 检查邮件配置，确保SMTP设置正确，可能需要应用专用密码。

### Q: API调用失败？
A: 检查OpenAI API密钥是否有效，网络是否可达。

### Q: 前端无法连接后端？
A: 检查CORS配置和防火墙设置。

### Q: Docker容器启动失败？
A: 检查端口占用情况和环境变量配置。

## 技术支持

如有问题，请检查：
1. 系统日志文件
2. Docker容器状态
3. 网络连接情况
4. 配置文件语法

## 许可证

MIT License

## 更新日志

### v1.0.0
- 初始版本发布
- 支持诗歌生成和文本摘要工作流
- 完整的用户认证和权限管理
- Docker化部署支持