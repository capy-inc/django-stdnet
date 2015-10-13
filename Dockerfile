FROM ubuntu:trusty

MAINTAINER Yusuke MURAOKA <yusuke@jbking.org>

# RUN locale-gen en_US.UTF-8 && /usr/sbin/update-locale LANG=en_US.UTF-8
# ENV LANG en_US.UTF-8

RUN apt-get update \
    && apt-get -y install \
       python-software-properties software-properties-common \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN add-apt-repository -y ppa:fkrull/deadsnakes

RUN apt-get update \
    && apt-get -y install \
       git python-pip \
       python2.7 python3.2 python3.3 python3.4 \
       python2.7-dev python3.2-dev python3.3-dev python3.4-dev \
    && apt-get clean \
    && pip install tox \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app
VOLUME /src

ADD requirements*.txt tox.ini /app/
RUN TOXBUILD=true tox

CMD cp -rT /src/ /app/ && tox
