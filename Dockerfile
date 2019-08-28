FROM konstruktoid/alpine

LABEL org.label-schema.name="docker-covenant" \
      org.label-schema.vcs-url="git@github.com:konstruktoid/docker-covenant.git"

COPY ./* /

RUN apk update && \
    apk upgrade && \
    apk --update add python3 py-pip && \
    pip3 install --upgrade pip && \
    pip3 install -r requirements.txt && \
    apk del --purge py-pip && \
    rm -rf /var/cache/apk/

CMD ["/usr/bin/python3","/docker-covenant.py"]
