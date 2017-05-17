FROM bcroq/stackless:2.7.9

RUN apt-get update && \
    apt-get install -y gcc make libxml2-dev libxslt1-dev zlib1g-dev libjpeg-dev libfreetype6-dev --no-install-recommends

COPY . /tmp/kansha
WORKDIR /tmp/kansha
RUN /opt/stackless/bin/easy_install  .

RUN /opt/stackless/bin/python setup.py compile_catalog && \
    /opt/stackless/bin/nagare-admin create-db kansha && \
    /opt/stackless/bin/kansha-admin create-demo && \
    /opt/stackless/bin/kansha-admin create-index

EXPOSE 8080

ENTRYPOINT ["/opt/stackless/bin/nagare-admin"]
CMD ["serve", "--host", "0.0.0.0", "kansha"]