# 本地调试代码

PostgreSQL 数据库

```bash
docker run -e POSTGRES_DB=website   -e POSTGRES_USER=k8smeetup   -e POSTGRES_PASSWORD=caicloud.io   -v `pwd`/pgdata:/var/lib/postgresql/data   -p 5432:5432   -d postgres:11.2-alpine

docker run -d -p 8080:80 -e "PGADMIN_DEFAULT_EMAIL=xiaolong@caicloud.io" -e "PGADMIN_DEFAULT_PASSWORD=admin" dpage/pgadmin4
```

调试运行模式

```bash
docker run --rm -p 5678:5678 \
  -e BOT_LOG_LEVEL=INFO \
  -e BOT_ADMINS=@xiaolong \
  -e REPOSITORY="kubernetes" \
  -e REPOSITORY_CONFIG_FILE="/errbot/config/repository.yaml" \
  -e MAX_RESULT=10 -e MAX_WRITE=5000 -e TARGET_LANG="zh" \
  -e BOT_TOKEN="xoxb-480833052976-492872057856-c8u61HcVBnA4yEMRl9Pg8w4d" \
  -e BACKEND="Slack" \
  -e CRITICAL_COMMANDS="find_new_files_in,find_updated_files_in,cache_issue" \
  -e OPERATORS=@xiaolong \
  -e PRIVATE_COMMANDS="whatsnew,github_bind,github_whoami" \
  -v $(pwd)/config.py:/errbot/config.py \
  -v $(pwd)/plugins:/errbot/plugins \
  -v $(pwd)/repository.yaml:/errbot/config/repository.yaml \
  -v $(pwd)/repository/website:/errbot/repository/website \
  -v $(pwd)/data:/errbot/data \
  -v $(pwd)/github:/usr/local/lib/python3.7/site-packages/github \
  -v $(pwd)/github:/errbot/github \
  -ti errbot:v2 sh
```

生产运行模式
```bash
cd /root/issueflow/errbot-plugin/errbot
docker run --rm -p 5678:5678 \
  -e BOT_LOG_LEVEL=INFO \
  -e BOT_ADMINS=@xiaolong \
  -e REPOSITORY="kubernetes" \
  -e REPOSITORY_CONFIG_FILE="/errbot/config/repository.yaml" \
  -e MAX_RESULT=10 -e MAX_WRITE=5000 -e TARGET_LANG="zh" \
  -e BOT_TOKEN="xoxb-xxx" \
  -e BACKEND="Slack" \
  -e CRITICAL_COMMANDS="find_new_files_in,find_updated_files_in,cache_issue" \
  -e OPERATORS=@xiaolong \
  -e PRIVATE_COMMANDS="whatsnew,github_bind,github_whoami" \
  -v $(pwd)/config.py:/errbot/config.py \
  -v $(pwd)/repository.yaml:/errbot/config/repository.yaml \
  -v /root/website:/errbot/repository/website \
  -d errbot:v1
```

报表 Bot

https://k8s-zh.slack.com/services/616471826150?updated=1

```bash
docker run --rm -p 5678:5678 \
  -e BOT_LOG_LEVEL=INFO \
  -e BOT_ADMINS=@xiaolong \
  -e REPOSITORY="kubernetes" \
  -e REPOSITORY_CONFIG_FILE="/errbot/config/repository.yaml" \
  -e MAX_RESULT=10 -e MAX_WRITE=5000 -e TARGET_LANG="zh" \
  -e BOT_TOKEN="xoxb-xxx" \
  -e BACKEND="Slack" \
  -e CRITICAL_COMMANDS="find_new_files_in,find_updated_files_in,cache_issue" \
  -e OPERATORS=@xiaolong \
  -e PRIVATE_COMMANDS="whatsnew,github_bind,github_whoami" \
  -v $(pwd)/config.py:/errbot/config.py \
  -v $(pwd)/plugins:/errbot/plugins \
  -v $(pwd)/repository.yaml:/errbot/config/repository.yaml \
  -v $(pwd)/repository/website:/errbot/repository/website \
  -v $(pwd)/data:/errbot/data \
  -v $(pwd)/github:/usr/local/lib/python3.7/site-packages/github \
  -v $(pwd)/github:/errbot/github \
  -ti errbot:v2 sh
```


## 配置 Github 的 token

```bash
!github bind 07afc4ef418f0a7c2026b3ca0e55fa6320da466c
!github whoami
```

## Step1. 创建 issue

```bash
# 指定版本的 files 添加至数据库任务表
!init files 1.10
!init files 1.11
!init files 1.12
!init files 1.13
!init files 1.14

# 创建 issue
!init issue 1.10 --create_issue=1
!init issue 1.11 --create_issue=1
!init issue 1.12 --create_issue=1
!init issue 1.13 --create_issue=1
!init issue 1.14 --create_issue=1
```
这里由于是调用 Github 的 issue api，因此速度比较慢，需要耐心等待...

## Step2. 更新 issue

```bash
# 指定版本的 files 更新至数据库任务表
!update files 1.10
!update files 1.11
!update files 1.12
!update files 1.13
!update files 1.14

# 更新 issue
!update issue 1.10 --update_issue=1
!update issue 1.11 --update_issue=1
!update issue 1.12 --update_issue=1
!update issue 1.13 --update_issue=1
!update issue 1.14 --update_issue=1
```

## Step3. 批量确定 issue 状态

```bash
# 批量确认 issue 状态
!batch comment issue  --comment=/confirm
# 确认指定 issue 的状态
!comment issue 250 --comment=/confirm
```

## 其他命令

```bash
# 查看 GITHUB API 调用限制数
!show limit

# issue 查重 - 列出重复的 issue 
!find dupe issues

# 查看当前配置文件对应的所有翻译版本
!list branches

# 在当前仓库的 issue 里搜索 issue
!search issues blog

# 显示ID号为 280 的 issue
!show issue 280

# 搜索所有标签 label:welcome 状态为 open 的 issue
!whatsnew

# 缓存所有 open 状态的 issue 至 /errbot/config/open_cache.txt 文件
!cache issue

# 刷新所有的分支 - 已废弃
!refresh repositories
```

webhook

```bash
https://webhook.rays.xyz/postreceive
```
https://api.github.com/repos/kubernetes/website/pulls/13828/reviews


docker run -p 443:443 -p 80:80 \
  -v /root/nginx/conf.d:/etc/nginx/conf.d \
  -v /root/nginx/ssl:/etc/nginx/ssl \
  -v /root/nginx/web:/usr/share/nginx/html \
  -d nginx:alpine
