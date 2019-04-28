# Webhook 配置指南

## Step1. 需要配置仓库 issue 的 Label

(welcome/pending 标签会在初始化时间创建)
(translating/pushed/finished) 三个标签不会自动创建，需要手动添加

- "welcome"
- "pending"
- "translating"
- "pushed"
- "finished

## Step2. 启动服务器

调试模式运行

```bash
cd /root/issueflow/flask/webhook
docker run -p 8000:80 \
  -p 9000:9000 \
  -e LOG_LEVEL=0 \
  -e PORT="80" \
  -e GITHUB_TOKEN="07afc4ef418f0a7c2026b3ca0e55fa6320da466c" \
  -e WORKFLOW="kubernetes" \
  -e ADMINS="markthink" \
  -v $(pwd)/githubutil:/webhook/githubutil \
  -v $(pwd)/config.yaml:/webhook/config.yaml \
  -v $(pwd)/flask-entry.py:/webhook/flask-entry.py \
  -v $(pwd)/github:/usr/local/lib/python3.7/site-packages/github \
  -v $(pwd)/github:/webhook/github \
  -ti webhook:v1 sh
  # /webhook/ python flask-entry.py
```

生产模式运行

```bash
cd /root/issueflow/flask/webhook
docker run -p 8000:80 \
  -p 9000:9000 \
  -e LOG_LEVEL=0 \
  -e PORT="80" \
  -e GITHUB_TOKEN="07afc4ef418f0a7c2026b3ca0e55fa6320da466c" \
  -e WORKFLOW="kubernetes" \
  -e ADMINS="markthink" \
  -v $(pwd)/config.yaml:/webhook/config.yaml \
  -v $(pwd)/flask-entry.py:/webhook/flask-entry.py \
  -d webhook:v1
  # /webhook/ python flask-entry.py
```

Centos 安装字体
```bash
# https://github.com/powerline/fonts
yum install fontconfig
fc-cache -vf
```