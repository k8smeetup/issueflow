#!/bin/sh
# webhook 代码打包
set -x
WEBHOOK="./webhook"
mkdir -p $WEBHOOK

cp -Rf ../githubutil "$WEBHOOK"
cp ../config/workflow.yaml "$WEBHOOK/config.yaml"
cp flask-requirements.txt "$WEBHOOK/requirements.txt"
cp Dockerfile "$WEBHOOK/Dockerfile"
cp flask-entry.py "$WEBHOOK/flask-entry.py"

cd "$WEBHOOK"
find . -name __pycache__ -exec rm -Rf {} \;
find . -name *.pyc -exec rm -Rf {} \;