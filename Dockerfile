# docker build --no-cache -t reip_video_capture:0.1 .
# docker run -it --privileged reip_video_capture:0.1 sh
FROM alpine:3.9
MAINTAINER Charlie Mydlarz (cmydlarz@nyu.edu)

ENV PYTHONUNBUFFERED=1

RUN echo "**** install Python ****" && \
    apk add --no-cache python3-dev libc-dev alsa-lib-dev alsa-utils gcc portaudio-dev && \
    if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi && \
    ln -s /usr/include/locale.h /usr/include/xlocale.h && \
    \
    echo "**** install pip ****" && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --no-cache --upgrade pip setuptools wheel && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    pip install pyaudio

RUN mkdir /mnt/data