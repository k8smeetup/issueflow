FROM python:3.7.3-alpine3.9

LABEL author=xiaolong@caicloud.io

ENV LOG_LEVEL=""
ENV PORT="80"
ENV GITHUB_TOKEN=""
ENV WORKFLOW=""
ENV ADMINS=""

WORKDIR /webhook

COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install  --no-cache-dir -r ./requirements.txt

COPY githubutil .
COPY config.yaml .
COPY flask-entry.py .

EXPOSE $PORT

VOLUME /webhook
CMD ["python","flask-entry.py"]


