# 部署指南

本文档提供了AI工作流平台的详细部署说明。

## 部署前准备

### 系统要求

- **操作系统**: Linux/Windows/macOS
- **Python**: 3.8或更高版本
- **内存**: 至少512MB可用内存
- **磁盘**: 至少1GB可用空间
- **网络**: 可访问互联网（用于Qwen API调用）

### 必要的第三方服务

1. **邮件服务**
   - SMTP服务器（推荐Gmail、腾讯企业邮箱等）
   - 应用专用密码

2. **Qwen API**
   - 阿里云账号
   - Qwen API密钥

## 快速部署

### 1. 使用Docker部署（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd web-ai-py

# 配置环境变量
cp .env.example .env
nano .env  # 填写必要配置

# 配置用户
nano config/users.yaml

# 使用Docker Compose启动
docker-compose up -d
```

### 2. 手动部署

```bash
# 克隆项目
git clone <repository-url>
cd web-ai-py

# 安装Python依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env
nano .env

# 配置用户
nano config/users.yaml

# 启动服务
python start.py
```

## 详细配置

### 环境变量配置 (.env)

```env
# 基础配置
DEBUG=false
SECRET_KEY=your-very-secure-secret-key-change-this

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 邮件配置（必填）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Qwen API配置（必填）
QWEN_API_KEY=your-qwen-api-key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# 安全配置
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:8000","https://yourdomain.com"]
```

### 用户配置 (config/users.yaml)

```yaml
users:
  admin:
    email: "admin@yourdomain.com"
    role: "admin"
    enabled: true
    
  user1:
    email: "user1@yourdomain.com"
    role: "user"
    enabled: true
    
  user2:
    email: "user2@yourdomain.com"
    role: "user"
    enabled: true
```

## 生产环境部署

### 1. 使用Gunicorn + Nginx

#### 安装Gunicorn
```bash
pip install gunicorn
```

#### 创建Gunicorn配置文件 (gunicorn.conf.py)
```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
```

#### 启动Gunicorn
```bash
gunicorn -c gunicorn.conf.py backend.app:app
```

#### Nginx配置
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL证书配置
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # 反向代理配置
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件缓存
    location /static/ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # 安全配置
    location ~ /\. {
        deny all;
    }
}
```

### 2. 使用Systemd服务

#### 创建服务文件 (/etc/systemd/system/web-ai-py.service)
```ini
[Unit]
Description=AI Workflow Platform
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/web-ai-py
Environment=PATH=/var/www/web-ai-py/venv/bin
ExecStart=/var/www/web-ai-py/venv/bin/gunicorn -c gunicorn.conf.py backend.app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 启用服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable web-ai-py
sudo systemctl start web-ai-py
sudo systemctl status web-ai-py
```

### 3. Docker生产部署

#### Dockerfile优化
```dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p data logs config

# 复制配置文件
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 设置权限
RUN chown -R www-data:www-data /app

# 暴露端口
EXPOSE 80

# 启动supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

#### Docker Compose生产配置
```yaml
version: '3.8'

services:
  web-ai-py:
    build: .
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
      - ./ssl:/app/ssl
      - ./.env:/app/.env
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  # 可选：添加Redis用于会话存储
  redis:
    image: redis:alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    
  # 可选：添加监控
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  redis_data:
```

## 安全配置

### 1. 防火墙配置

```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. SSL证书配置

#### 使用Let's Encrypt
```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com

# 自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. 数据库备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/web-ai-py"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份SQLite数据库
cp /var/www/web-ai-py/data/app.db $BACKUP_DIR/app_$DATE.db

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /var/www/web-ai-py/config/

# 清理7天前的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

## 监控和维护

### 1. 日志轮转

```bash
# /etc/logrotate.d/web-ai-py
/var/www/web-ai-py/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    postrotate
        systemctl reload web-ai-py
    endscript
}
```

### 2. 健康检查脚本

```bash
#!/bin/bash
# health_check.sh

URL="http://localhost:8000/"
EXPECTED_CODE=200

response=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $response -eq $EXPECTED_CODE ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $response)"
    # 可以添加重启逻辑
    systemctl restart web-ai-py
    exit 1
fi
```

### 3. 性能监控

使用Prometheus + Grafana进行监控：

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'web-ai-py'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## 故障排除

### 常见问题

1. **服务无法启动**
   - 检查端口是否被占用：`netstat -tulpn | grep 8000`
   - 检查权限：确保用户有读写权限
   - 查看日志：`tail -f logs/app.log`

2. **邮件发送失败**
   - 验证SMTP配置
   - 检查防火墙设置
   - 确认邮箱密码为应用专用密码

3. **API调用失败**
   - 检查网络连接
   - 验证API密钥
   - 查看Qwen API使用限制

4. **数据库锁定**
   - 重启服务
   - 检查磁盘空间
   - 启用WAL模式

### 调试命令

```bash
# 查看服务状态
systemctl status web-ai-py

# 查看实时日志
tail -f /var/www/web-ai-py/logs/app.log

# 测试API连接
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","daily_code":"123456"}'

# 检查数据库
sqlite3 /var/www/web-ai-py/data/app.db ".tables"
```

## 更新和维护

### 应用更新
```bash
# 停止服务
sudo systemctl stop web-ai-py

# 备份数据
cp -r /var/www/web-ai-py/data /backup/

# 更新代码
cd /var/www/web-ai-py
git pull origin main

# 更新依赖
pip install -r requirements.txt

# 启动服务
sudo systemctl start web-ai-py
```

### 数据库迁移
```bash
# 如果有数据库结构变更
python -c "
import asyncio
from database.models import init_database
asyncio.run(init_database())
"
```

这样就完成了一个完整的、安全的、可扩展的AI工作流平台的部署指南。
