#!/bin/bash

# 生产环境部署脚本
set -e

echo "开始部署AI工作流系统..."

# 检查环境变量
if [ ! -f .env ]; then
    echo "错误: 未找到.env文件，请先配置环境变量"
    exit 1
fi

# 加载环境变量
source .env

# 检查必要的环境变量
required_vars=("SECRET_KEY" "MAIL_SERVER" "MAIL_USERNAME" "MAIL_PASSWORD" "ADMIN_EMAIL" "OPENAI_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "错误: 环境变量 $var 未设置"
        exit 1
    fi
done

# 创建必要的目录
mkdir -p data logs ssl

# 构建Docker镜像
echo "构建Docker镜像..."
docker-compose build

# 初始化数据库（首次部署）
if [ ! -f data/app.db ]; then
    echo "初始化数据库..."
    docker-compose run --rm web-ai-py python init_db.py
fi

# 启动服务
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 健康检查
echo "进行健康检查..."
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    docker-compose logs web-ai-py
    exit 1
fi

if curl -f http://localhost:80 > /dev/null 2>&1; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败"
    docker-compose logs nginx
    exit 1
fi

echo "🎉 部署完成！"
echo "请确保："
echo "1. 配置SSL证书到ssl/目录"
echo "2. 更新nginx.conf中的域名"
echo "3. 设置定时任务生成每日验证码"
echo "4. 配置防火墙规则"

# 显示服务状态
docker-compose ps
