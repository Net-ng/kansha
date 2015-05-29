FROM bcroq/stackless:2.7.9

RUN apt-get update && \
    apt-get install -y build-essential libxml2-dev libxslt1-dev zlib1g-dev
    
COPY . /tmp/kansha
RUN cd /tmp/kansha && \
    /opt/stackless/bin/pip install -e . --allow-external PEAK-Rules --allow-unverified PEAK-Rules --find-links http://www.nagare.org/snapshots --trusted-host www.nagare.org

RUN /opt/stackless/bin/nagare-admin create-db kansha && \
    /opt/stackless/bin/nagare-admin create-index kansha

EXPOSE 8080

ENTRYPOINT ["/opt/stackless/bin/nagare-admin"]
CMD ["serve", "--host", "0.0.0.0", "kansha"]