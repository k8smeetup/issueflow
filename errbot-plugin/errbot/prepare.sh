#!/bin/sh
set -xe
apk add git --update
apk add --virtual .build-deps \
    postgresql-dev python3-dev musl-dev gcc libffi-dev openssl-dev \
    libxml2-dev
# 设置时区
apk add -U tzdata
cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

pip3 install --upgrade pip
pip3 install  --no-cache-dir -r /tmp/requirements.txt
# apk del .build-deps

mkdir /errbot /errbot/data /errbot/plugins

cat >> /usr/local/bin/entry.sh << EOF
#!/bin/sh
if [ ! -f /errbot/config.py ]; then
    mkdir -p /errbot/data
    errbot --init
fi
errbot \$*
EOF

chmod a+x /usr/local/bin/entry.sh