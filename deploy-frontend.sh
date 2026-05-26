#!/bin/bash

# 前端自动部署脚本
# 使用方法：在本地项目根目录运行 ./deploy-frontend.sh

set -e

echo "🚀 开始部署前端..."

# 配置
SERVER_USER="root"
SERVER_HOST="47.100.74.186"
SERVER_PATH="/opt/VP/frontend/dist"
LOCAL_DIST="frontend/dist"

# 1. 构建前端
echo "📦 正在构建前端..."
cd frontend
npm run build
cd ..

# 2. 推送到服务器
echo "📤 正在推送到服务器..."
rsync -avz --delete ${LOCAL_DIST}/ ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/

# 3. 重启 Nginx
echo "🔄 重启 Nginx..."
ssh ${SERVER_USER}@${SERVER_HOST} "sudo nginx -s reload"

echo "✅ 部署完成！"
echo "🌐 访问地址: http://www.montageai.eu.cc"
