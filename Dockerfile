# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.9

FROM python:${PYTHON_VERSION} AS panda3d-builder

ENV LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bison \
        build-essential \
        flex \
        fakeroot \
        git \
        libassimp-dev \
        libbullet-dev \
        libeigen3-dev \
        libfreetype6-dev \
        libgl1-mesa-dev \
        libgtk-3-dev \
        libjpeg-dev \
        libopenal-dev \
        libopenexr-dev \
        libode-dev \
        libpng-dev \
        libssl-dev \
        libtiff-dev \
        libvorbis-dev \
        libx11-dev \
        libxcursor-dev \
        libxrandr-dev \
        libxxf86dga-dev \
        locales \
        patchelf \
        pkg-config \
        python3-dev \
        zlib1g-dev \
    && locale-gen C.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN git clone --depth=1 https://github.com/open-toontown/panda3d.git panda3d \
    && cd panda3d \
    && python makepanda/makepanda.py \
        --installer \
        --wheel \
        --no-egl \
        --no-gles \
        --no-gles2 \
        --no-opencv \
        --no-ffmpeg \
        --no-bullet \
        --no-vision \
        --no-pandatool \
    && mkdir /out \
    && find . -type f -name '*.whl' -exec cp {} /out/ \;

FROM python:${PYTHON_VERSION} AS astron-builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        libboost-all-dev \
        libssl-dev \
        libuv1-dev \
        libyaml-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN git clone --depth=1 https://github.com/Astron/Astron.git astron \
    && cmake -S astron -B astron/linux -DCMAKE_BUILD_TYPE=Release \
    && cmake --build astron/linux --parallel \
    && strip astron/linux/astrond

FROM alpine:3.20 AS resources-builder

RUN apk add --no-cache git \
    && git clone --depth=1 \
        https://github.com/open-toontown/resources.git \
        /resources \
    && rm -rf /resources/.git

FROM python:${PYTHON_VERSION}-slim AS runtime

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libassimp-dev \
        libboost-system-dev \
        libfftw3-double3 \
        libfreetype6 \
        libgl1 \
        libgl1-mesa-dri \
        libglx-mesa0 \
        libharfbuzz0b \
        libopenal1 \
        libopenexr-dev \
        libode-dev \
        libssl3 \
        libtiff6 \
        libuv1 \
        libvorbisfile3 \
        libyaml-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=panda3d-builder /out/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl \
    && rm -f /tmp/*.whl

COPY --from=astron-builder /build/astron/linux/astrond /app/astron/linux/astrond
COPY --from=resources-builder /resources /app/resources
COPY . /app
COPY run.sh /app/run.sh

RUN chmod -R +rwx /app/*

EXPOSE 7199 7198 7197

STOPSIGNAL SIGTERM
ENTRYPOINT ["/app/run.sh"]
