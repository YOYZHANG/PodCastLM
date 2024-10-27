#!/bin/sh

# 替换配置文件中的占位符
envsubst '$BACKEND_API' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# 启动 Nginx
nginx -g 'daemon off;'
