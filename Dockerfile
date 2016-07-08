FROM python:3.4

ENV PHANTOMJS_VERSION 1.9.7

# https://hub.docker.com/r/cmfatih/phantomjs/~/dockerfile/
RUN \
  mkdir -p /srv/var && \
  wget -q --no-check-certificate -O /tmp/phantomjs-$PHANTOMJS_VERSION-linux-x86_64.tar.bz2 https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-$PHANTOMJS_VERSION-linux-x86_64.tar.bz2 && \
  tar -xjf /tmp/phantomjs-$PHANTOMJS_VERSION-linux-x86_64.tar.bz2 -C /tmp && \
  rm -f /tmp/phantomjs-$PHANTOMJS_VERSION-linux-x86_64.tar.bz2 && \
  mv /tmp/phantomjs-$PHANTOMJS_VERSION-linux-x86_64/ /srv/var/phantomjs && \
  ln -s /srv/var/phantomjs/bin/phantomjs /usr/bin/phantomjs

RUN curl -sL https://deb.nodesource.com/setup_5.x | bash -

RUN apt-get update && \
  apt-get install -y nodejs

COPY requirements.txt /calc/

RUN pip install -r /calc/requirements.txt
