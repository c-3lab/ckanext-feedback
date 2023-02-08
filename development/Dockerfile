FROM python:3.8.16-bullseye

LABEL maintainer="C3Lab <info.c3lab@gmail.com>"

# Set timezone
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Setting the locale
ENV LC_ALL=en_US.UTF-8       
RUN apt-get update
RUN apt-get install --no-install-recommends -y locales
RUN sed -i "/$LC_ALL/s/^# //g" /etc/locale.gen
RUN dpkg-reconfigure --frontend=noninteractive locales 
RUN update-locale LANG=${LC_ALL}

# Install required system packages
RUN apt-get -q -y update \
    && DEBIAN_FRONTEND=noninteractive apt-get -q -y upgrade \
    && apt-get -q -y install \
	libgeos-dev \
        postgresql-client \
        build-essential \
        git-core \
        vim \
    && apt-get -q clean

# Define CKAN environment variables
ENV CKAN_HOME=/usr/lib/ckan
ENV CKAN_VENV=$CKAN_HOME/venv
ENV CKAN_CONFIG=/etc/ckan
ENV CKAN_STORAGE_PATH=/var/lib/ckan

# Build-time variables specified by docker-compose.yml / .env
ARG CKAN_SITE_URL

# Setup virtual environment for CKAN
RUN mkdir -p $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH \
    && python3 -m venv $CKAN_VENV \
    && ln -s $CKAN_VENV/bin/pip3 /usr/local/bin/ckan-pip3 \
    && ln -s $CKAN_VENV/bin/ckan /usr/local/bin/ckan

# Virtual environment binaries/scripts to be used first
ENV PATH=${CKAN_VENV}/bin:${PATH} 

# Setup CKAN
ADD ./external/ckan $CKAN_VENV/src/ckan/
RUN ckan-pip3 install -U pip \
    && ckan-pip3 install -U future \
    && ckan-pip3 install --upgrade --no-cache-dir -r $CKAN_VENV/src/ckan/requirement-setuptools.txt \
    && ckan-pip3 install --upgrade --no-cache-dir -r $CKAN_VENV/src/ckan/requirements.txt \
    && ckan-pip3 install -e $CKAN_VENV/src/ckan/ \
    && ln -s $CKAN_VENV/src/ckan/ckan/config/who.ini $CKAN_CONFIG/who.ini \
    && cp -v $CKAN_VENV/src/ckan/contrib/docker/ckan-entrypoint.sh /ckan-entrypoint.sh \
    && chmod +x /ckan-entrypoint.sh \
    && chown -R root:root $CKAN_HOME $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH

ENTRYPOINT ["/ckan-entrypoint.sh"]

EXPOSE 5000

CMD ["ckan","-c","/etc/ckan/production.ini", "run", "--host", "0.0.0.0"]
