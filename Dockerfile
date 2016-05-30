FROM konstruktoid/alpine

COPY ./* /

RUN apk update && \
    apk upgrade && \
    apk --update add py-pip && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm -rf /var/cache/apk/

CMD ["/usr/bin/python","/docker-covenant.py"]
