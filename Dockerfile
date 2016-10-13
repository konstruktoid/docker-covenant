FROM konstruktoid/alpine

LABEL org.label-schema.name="docker-covenant" \
      org.label-schema.vcs-url="git@github.com:konstruktoid/docker-covenant.git"

COPY ./* /

RUN apk update && \
    apk upgrade && \
    apk --update add py-pip && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm -rf /var/cache/apk/

CMD ["/usr/bin/python","/docker-covenant.py"]
