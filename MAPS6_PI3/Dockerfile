FROM debian:latest


RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-rpi.gpio \
    libtiff5-dev \ 
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libfreetype6-dev \ 
    liblcms2-dev \ 
    libwebp-dev \
    python3-setuptools \
    iputils-ping

RUN pip3 install --no-binary Pillow requests
RUN pip3 install Adafruit_SSD1306 pyserial
RUN pip3 install Pillow
RUN pip3 install six

RUN mkdir /home/MAPS6_NBIOT
RUN mkdir /mnt/SD

COPY . /home/MAPS6_NBIOT/
COPY ARIALUNI.TTF /home/

WORKDIR /home/MAPS6_NBIOT


CMD python3 main.py
