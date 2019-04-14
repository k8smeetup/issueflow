FROM python:3.7.3-alpine3.9
COPY prepare.sh /usr/local/bin
COPY requirements.txt /tmp/requirements.txt
RUN /usr/local/bin/prepare.sh
COPY config.py /errbot/
COPY plugins /errbot/plugins
WORKDIR /errbot
VOLUME ["/errbot/config", "/errbot/repository"]
CMD ["/usr/local/bin/entry.sh"]
