# 翻译工程本地构建

此项目贡献者: 崔秀龙

`issueflow` 项目基于 Chatops 理念，使用 `errbot` + `slack` 实现任务的交互管理， 基于 `Github` 的 `issue` 功能实现翻译任务的管理分发。

本文讲解如何基于此项目，构建本地镜像包, 用于本地的开发调试环境搭建。

## Step1 Errbot 构建

进入 `errbot-plugin` 目录，构建 errbot:v1 镜像

### errbot 代码打包

```bash
➜  issueflow git:(master) ✗ cd errbot-plugin && ./errbot-unpack.sh
+ DEST=./errbot
+ rm -Rf ./errbot
+ mkdir -p ./errbot
+ cp config.py ./errbot/
+ cp Dockerfile ./errbot/
+ cp prepare.sh ./errbot/
+ cp requirements.txt ./errbot/
+ cp -Rf transbot ./errbot/
+ cp -Rf ../githubutil ./errbot/transbot/githubutil
+ cp -Rf ../gitutil ./errbot/transbot/gitutil
+ cp -Rf ../transutil ./errbot/transbot/transutil
➜  errbot-plugin git:(master) ✗ tree -L 2 ./errbot
./errbot # 生成的 errbot 代码文件
├── Dockerfile
├── config.py
├── prepare.sh
├── requirements.txt
└── transbot
    ├── githubutil
    ├── gitutil
    ├── transbot.plug
    ├── transbot.py
    └── transutil

4 directories, 6 files
```

### 构建 errbot:v1 镜像

```bash
➜  errbot-plugin git:(master) ✗ docker build -t errbot:v1 ./errbot
Sending build context to Docker daemon  62.98kB
Step 1/9 : FROM alpine
 ---> cdf98d1859c1
Step 2/9 : COPY prepare.sh /usr/local/bin
 ---> Using cache
 ---> cbad20c37640
Step 3/9 : COPY requirements.txt /tmp/requirements.txt
 ---> Using cache
 ---> c682461c9470
Step 4/9 : RUN /usr/local/bin/prepare.sh
 ---> Using cache
 ---> 67925e8b8b4a
Step 5/9 : COPY config.py /errbot/
 ---> Using cache
 ---> 55ef46b8aba9
Step 6/9 : COPY transbot /errbot/plugins/transbot
 ---> Using cache
 ---> 3f83e5c59b51
Step 7/9 : WORKDIR /errbot
 ---> Using cache
 ---> 7ca47611d52a
Step 8/9 : VOLUME ["/errbot/data", "/errbot/config", "/errbot/repository"]
 ---> Using cache
 ---> 450e3429b87e
Step 9/9 : CMD ["/usr/local/bin/entry.sh"]
 ---> Using cache
 ---> 4baad3d048a9
Successfully built 4baad3d048a9
Successfully tagged errbot:v1
```

## Step2. WebHook 构建

进入 `flask` 目录，构建 webhook 镜像

### Webhook 代码打包

```bash
➜  issueflow git:(master) ✗ cd flask && ./webhook-unpack.sh
+ WEBHOOK=./webhook
+ mkdir -p ./webhook
+ cp -Rf ../githubutil ./webhook
+ cp ../config/workflow.yaml ./webhook/config.yaml
+ cp flask-requirements.txt ./webhook/requirements.txt
+ cp Dockerfile ./webhook/Dockerfile
+ cp flask-entry.py ./webhook/flask-entry.py
+ cd ./webhook
+ find . -name __pycache__ -exec rm -Rf '{}' ';'
+ find . -name '*.pyc' -exec rm -Rf '{}' ';'
➜  flask git:(master) ✗ tree -L 2 webhook
webhook # 生成的 webhook 代码文件
├── Dockerfile
├── config.yaml
├── flask-entry.py
├── githubutil
│   ├── __init__.py
│   ├── action.py
│   ├── configure.py
│   └── github.py
└── requirements.txt

1 directory, 8 files
```

### 构建 webhook:v1 镜像

```bash
➜  flask git:(master) ✗ docker build -t webhook:v1 ./webhook
Sending build context to Docker daemon  31.23kB
Step 1/16 : FROM python:3.7.3-alpine3.9
 ---> 96c5c39abbb6
Step 2/16 : LABEL author=xiaolong@caicloud.io
 ---> Using cache
 ---> 86031bcedd96
Step 3/16 : ENV LOG_LEVEL=""
 ---> Using cache
 ---> 447920b5088b
Step 4/16 : ENV PORT="80"
 ---> Using cache
 ---> 13099ce1eaed
Step 5/16 : ENV GITHUB_TOKEN=""
 ---> Using cache
 ---> de293486d2b6
Step 6/16 : ENV WORKFLOW=""
 ---> Using cache
 ---> 788d2b0a581c
Step 7/16 : ENV ADMINS=""
 ---> Using cache
 ---> bba61126080d
Step 8/16 : WORKDIR /webhook
 ---> Using cache
 ---> 3a995f424bbe
Step 9/16 : COPY requirements.txt .
 ---> d53c5f54c318
Step 10/16 : RUN pip3 install --upgrade pip && pip3 install  --no-cache-dir -r ./requirements.txt
 ---> Running in b666b0b41394
Requirement already up-to-date: pip in /usr/local/lib/python3.7/site-packages (19.0.3)
Collecting github-webhook (from -r ./requirements.txt (line 1))
  Downloading https://files.pythonhosted.org/packages/48/e9/9ae6b74259857a78860a677bcd95c00b0fd70a10c7a84c3a5ebfdaefdca4/github_webhook-1.0.2-py2.py3-none-any.whl
Collecting PyGithub (from -r ./requirements.txt (line 2))
  Downloading https://files.pythonhosted.org/packages/7f/25/8d539a2c7e4b32ec94d4e8e22bfeb7afaef43e6c8983548461ec9a7bcda7/PyGithub-1.43.6.tar.gz (2.9MB)
Collecting PyYAML (from -r ./requirements.txt (line 3))
  Downloading https://files.pythonhosted.org/packages/9f/2c/9417b5c774792634834e730932745bc09a7d36754ca00acf1ccd1ac2594d/PyYAML-5.1.tar.gz (274kB)
Collecting Flask (from -r ./requirements.txt (line 4))
  Downloading https://files.pythonhosted.org/packages/7f/e7/08578774ed4536d3242b14dacb4696386634607af824ea997202cd0edb4b/Flask-1.0.2-py2.py3-none-any.whl (91kB)
Collecting six (from github-webhook->-r ./requirements.txt (line 1))
  Downloading https://files.pythonhosted.org/packages/73/fb/00a976f728d0d1fecfe898238ce23f502a721c0ac0ecfedb80e0d88c64e9/six-1.12.0-py2.py3-none-any.whl
Collecting deprecated (from PyGithub->-r ./requirements.txt (line 2))
  Downloading https://files.pythonhosted.org/packages/9f/7a/003fa432f1e45625626549726c2fbb7a29baa764e9d1fdb2323a5d779f8a/Deprecated-1.2.5-py2.py3-none-any.whl
Collecting pyjwt (from PyGithub->-r ./requirements.txt (line 2))
  Downloading https://files.pythonhosted.org/packages/87/8b/6a9f14b5f781697e51259d81657e6048fd31a113229cf346880bb7545565/PyJWT-1.7.1-py2.py3-none-any.whl
Collecting requests>=2.14.0 (from PyGithub->-r ./requirements.txt (line 2))
  Downloading https://files.pythonhosted.org/packages/7d/e3/20f3d364d6c8e5d2353c72a67778eb189176f08e873c9900e10c0287b84b/requests-2.21.0-py2.py3-none-any.whl (57kB)
Collecting itsdangerous>=0.24 (from Flask->-r ./requirements.txt (line 4))
  Downloading https://files.pythonhosted.org/packages/76/ae/44b03b253d6fade317f32c24d100b3b35c2239807046a4c953c7b89fa49e/itsdangerous-1.1.0-py2.py3-none-any.whl
Collecting click>=5.1 (from Flask->-r ./requirements.txt (line 4))
  Downloading https://files.pythonhosted.org/packages/fa/37/45185cb5abbc30d7257104c434fe0b07e5a195a6847506c074527aa599ec/Click-7.0-py2.py3-none-any.whl (81kB)
Collecting Werkzeug>=0.14 (from Flask->-r ./requirements.txt (line 4))
  Downloading https://files.pythonhosted.org/packages/18/79/84f02539cc181cdbf5ff5a41b9f52cae870b6f632767e43ba6ac70132e92/Werkzeug-0.15.2-py2.py3-none-any.whl (328kB)
Collecting Jinja2>=2.10 (from Flask->-r ./requirements.txt (line 4))
  Downloading https://files.pythonhosted.org/packages/1d/e7/fd8b501e7a6dfe492a433deb7b9d833d39ca74916fa8bc63dd1a4947a671/Jinja2-2.10.1-py2.py3-none-any.whl (124kB)
Collecting wrapt<2,>=1 (from deprecated->PyGithub->-r ./requirements.txt (line 2))
  Downloading https://files.pythonhosted.org/packages/67/b2/0f71ca90b0ade7fad27e3d20327c996c6252a2ffe88f50a95bba7434eda9/wrapt-1.11.1.tar.gz
Collecting chardet<3.1.0,>=3.0.2 (from requests>=2.14.0->PyGithub->-r ./requirements.txt (line 2))
  Downloading https://files.pythonhosted.org/packages/bc/a9/01ffebfb562e4274b6487b4bb1ddec7ca55ec7510b22e4c51f14098443b8/chardet-3.0.4-py2.py3-none-any.whl (133kB)
Collecting certifi>=2017.4.17 (from requests>=2.14.0->PyGithub->-r ./requirements.txt (line 2))
  Downloading https://files.pythonhosted.org/packages/60/75/f692a584e85b7eaba0e03827b3d51f45f571c2e793dd731e598828d380aa/certifi-2019.3.9-py2.py3-none-any.whl (158kB)
Collecting idna<2.9,>=2.5 (from requests>=2.14.0->PyGithub->-r ./requirements.txt (line 2))
  Downloading https://files.pythonhosted.org/packages/14/2c/cd551d81dbe15200be1cf41cd03869a46fe7226e7450af7a6545bfc474c9/idna-2.8-py2.py3-none-any.whl (58kB)
Collecting urllib3<1.25,>=1.21.1 (from requests>=2.14.0->PyGithub->-r ./requirements.txt (line 2))
  Downloading https://files.pythonhosted.org/packages/62/00/ee1d7de624db8ba7090d1226aebefab96a2c71cd5cfa7629d6ad3f61b79e/urllib3-1.24.1-py2.py3-none-any.whl (118kB)
Collecting MarkupSafe>=0.23 (from Jinja2>=2.10->Flask->-r ./requirements.txt (line 4))
  Downloading https://files.pythonhosted.org/packages/b9/2e/64db92e53b86efccfaea71321f597fa2e1b2bd3853d8ce658568f7a13094/MarkupSafe-1.1.1.tar.gz
Installing collected packages: six, itsdangerous, click, Werkzeug, MarkupSafe, Jinja2, Flask, github-webhook, wrapt, deprecated, pyjwt, chardet, certifi, idna, urllib3, requests, PyGithub, PyYAML
  Running setup.py install for MarkupSafe: started
    Running setup.py install for MarkupSafe: finished with status 'done'
  Running setup.py install for wrapt: started
    Running setup.py install for wrapt: finished with status 'done'
  Running setup.py install for PyGithub: started
    Running setup.py install for PyGithub: finished with status 'done'
  Running setup.py install for PyYAML: started
    Running setup.py install for PyYAML: finished with status 'done'
Successfully installed Flask-1.0.2 Jinja2-2.10.1 MarkupSafe-1.1.1 PyGithub-1.43.6 PyYAML-5.1 Werkzeug-0.15.2 certifi-2019.3.9 chardet-3.0.4 click-7.0 deprecated-1.2.5 github-webhook-1.0.2 idna-2.8 itsdangerous-1.1.0 pyjwt-1.7.1 requests-2.21.0 six-1.12.0 urllib3-1.24.1 wrapt-1.11.1
Removing intermediate container b666b0b41394
 ---> 31e3129fa21e
Step 11/16 : COPY githubutil .
 ---> d9d0fce7d8a1
Step 12/16 : COPY config.yaml .
 ---> 96e08db04ea8
Step 13/16 : COPY flask-entry.py .
 ---> fd67a979c755
Step 14/16 : EXPOSE $PORT
 ---> Running in a2d2ca5a1bb4
Removing intermediate container a2d2ca5a1bb4
 ---> 3801f896fe8c
Step 15/16 : VOLUME /webhook
 ---> Running in d67f1bf11d4a
Removing intermediate container d67f1bf11d4a
 ---> 7ebf2b193b03
Step 16/16 : CMD ["python","flask-entry.py"]
 ---> Running in bdd1d7117264
Removing intermediate container bdd1d7117264
 ---> 73c40bee947f
Successfully built 73c40bee947f
Successfully tagged webhook:v1
```


## Step3. 挂载本地代码进行调试

errbot 调试配置
```bash
docker run -d --name=errbot \
        --restart=always \
        -e BOT_LOG_LEVEL=INFO \ # 日志输出级别
        -e BOT_ADMINS=@markthink \ # 管理员的 Slack 名称
        -e REPOSITORY="kubernetes" \ # 配置文件中的 Repository 名称
        -e REPOSITORY_CONFIG_FILE="/errbot/config/repository.yaml" \ # 配置文件名称
        -e MAX_RESULT=10 \ # 单次最大输出数量
        -e MAX_WRITE=30 \ # 单次最大写入数量
        -e TARGET_LANG="zh" \ # 翻译语种名称
        -e BOT_TOKEN="xoxb-" \ # Slack Bot 的 Token
        -e BACKEND="Slack" \ # 指定使用 Slack 后端
        -e CRITICAL_COMMANDS="find_new_files_in,find_updated_files_in,cache_issue" \ # 关键命令列表
        -e OPERATORS="@markthink" \ # 可以执行关键命令的操作员
        -e PRIVATE_COMMANDS="whatsnew,github_bind,github_whoami" \ # 仅能在私聊窗口中使用的命令
        -v $(pwd)/gitutil:/errbot/plugins/transbot/gitutil \ # git 脚手架
        -v $(pwd)/githubutil:/errbot/plugins/transbot/githubutil \ # github 脚手架
        -v $(pwd)/transutil:/errbot/plugins/transbot/transutil \ # 翻译脚手架
        -v $(pwd)/errbot-plugin/transbot/transbot.py:/errbot/plugins/transbot/transbot.py \ # 翻译助手
        -v $(pwd)/errbot-plugin/config.py:/errbot/config.py \ # errbot 配置项
        -v $(pwd)/data:/errbot/data \ # Bot 的存储路径
        -v $(pwd)/config:/errbot/config \ # Bot 的配置路径
        -v $(pwd)/repository:/errbot/repository \ # 代码库路径
        errbot:v1 # 镜像名称
```

webhook 调试配置

```bash
docker run -d --name=webhook -p 80:80 \
        -e LOG_LEVEL=""
        -e PORT="80"
        -e GITHUB_TOKEN=""
        -e WORKFLOW=""
        -e ADMINS="markthink"
        -v $(pwd)/githubutil:/webhook/githubutil \ # github 脚手架
        -v $(pwd)/config/workflow.yaml:/webhook/config.yaml \ # 工作流配置
        -v $(pwd)/flask/flask-entry.py:/webhook/flask-entry.py \
        webhook:v1
```

```bash
docker run -d -p 8000:80 \
  -e LOG_LEVEL=""
  -e PORT="80"
  -e GITHUB_TOKEN=""
  -e WORKFLOW=""
  -e ADMINS="markthink"
  -v $(pwd)/githubutil:/webhook/githubutil \
  -v $(pwd)/config/workflow.yaml:/webhook/config.yaml \
  -v $(pwd)/flask/flask-entry.py:/webhook/flask-entry.py \
  webhook:v1
```
