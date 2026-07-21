FROM ubuntu:24.04

# Désactiver les invites interactives d'apt
ENV DEBIAN_FRONTEND=noninteractive

# Installation des dépendances système complètes
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    cmake \
    ninja-build \
    gperf \
    ccache \
    dfu-util \
    device-tree-compiler \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-venv \
    wget \
    curl \
    xz-utils \
    file \
    libsdl2-dev \
    && rm -rf /var/lib/apt/lists/*

# Configuration Git pour éviter les interruptions sur les gros dépôts
RUN git config --global http.postBuffer 524288000 && \
    git config --global http.maxRequestSize 524288000 && \
    git config --global core.compression 0

# Installation de West
RUN pip3 install west --break-system-packages

WORKDIR /workspace

# --- CORRECTION ICI : On cible la version stable v4.0.0 au lieu de main ---
RUN west init -m https://github.com/zephyrproject-rtos/zephyr --mr v4.0.0 -o=--depth=1 zephyrproject

WORKDIR /workspace/zephyrproject
RUN west update --narrow -o=--depth=1
RUN west zephyr-export

# Installation des dépendances Python indispensables
RUN pip3 install -r zephyr/scripts/requirements.txt --break-system-packages && \
    pip3 install esptool --break-system-packages

# --- CONFIGURATION DU SDK ZEPHYR MINIMAL LOCAL ---
ENV ZEPHYR_SDK_VERSION=0.17.0
WORKDIR /opt

# On copie le fichier minimal depuis ton dossier Windows (D:)
COPY zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_minimal.tar.xz .

# Extraction
RUN tar -xvf zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_minimal.tar.xz && \
    rm zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_minimal.tar.xz

# On demande au setup d'installer les toolchains nécessaires
RUN cd zephyr-sdk-${ZEPHYR_SDK_VERSION} && \
    ./setup.sh -t arm-zephyr-eabi -t xtensa-espressif_esp32_zephyr-elf -t riscv64-zephyr-elf -c

# --- VARIABLES D'ENVIRONNEMENT FIXES POUR CMAKE ---
ENV ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ENV ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk-0.17.0

WORKDIR /workspace
ENTRYPOINT ["west", "build"]