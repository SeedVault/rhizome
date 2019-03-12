FROM debian:stretch-slim

ADD scripts/run.sh /scripts/run.sh

RUN apt-get update \
&& apt-get install -y --no-install-recommends ca-certificates curl wget unzip \
&& apt-get remove --purge \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/* \
&& wget https://github.com/ChatScript/ChatScript/archive/master.zip \
&& unzip master.zip ChatScript-master/BINARIES/LinuxChatScript64 -d /opt \
&& unzip master.zip ChatScript-master/DICT/* -d /opt \
&& unzip master.zip ChatScript-master/RAWDATA/* -d /opt \
&& unzip master.zip ChatScript-master/SRC/* -d /opt \
&& unzip master.zip ChatScript-master/TOPIC/* -d /opt \
&& chmod a+x /opt/ChatScript-master/BINARIES/LinuxChatScript64 \
&& chmod a+x /scripts/run.sh

EXPOSE 1024

ENTRYPOINT ["/scripts/run.sh"]
