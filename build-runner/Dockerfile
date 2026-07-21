# syntax=docker/dockerfile:1.7
FROM ubuntu:24.04 AS builder

# === Build-time configuration ===
ENV DEBIAN_FRONTEND=noninteractive \
    ZEPHYR_VERSION=v4.0.0 \
    ZEPHYR_SDK_VERSION=0.17.0 \
    ZEPHYR_TOOLCHAIN_VARIANT=zephyr

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    python3-venv \
    python3-setuptools \
    wget \
    curl \
    xz-utils \
    file \
    libsdl2-dev \
    && rm -rf /var/lib/apt/lists/*

# Git optimizations for large repos
RUN git config --global http.postBuffer 524288000 && \
    git config --global http.maxRequestSize 524288000 && \
    git config --global core.compression 0

# Install West
RUN pip3 install --break-system-packages west

WORKDIR /workspace

# Initialize Zephyr project (stable version)
RUN west init -m https://github.com/zephyrproject-rtos/zephyr --mr ${ZEPHYR_VERSION} -o=--depth=1 zephyrproject

WORKDIR /workspace/zephyrproject
RUN west update --narrow -o=--depth=1 && \
    west zephyr-export

# Python dependencies
RUN pip3 install --break-system-packages -r zephyr/scripts/requirements.txt && \
    pip3 install --break-system-packages esptool

# === Zephyr SDK (self-contained download) ===
WORKDIR /opt
RUN wget -q https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZEPHYR_SDK_VERSION}/zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_minimal.tar.xz -O sdk.tar.xz && \
    tar -xvf sdk.tar.xz && \
    rm sdk.tar.xz && \
    cd zephyr-sdk-${ZEPHYR_SDK_VERSION} && \
    ./setup.sh -t arm-zephyr-eabi -t xtensa-espressif_esp32_zephyr-elf -t riscv64-zephyr-elf -c

# Final lightweight runtime stage
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    ZEPHYR_TOOLCHAIN_VARIANT=zephyr \
    ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk-0.17.0 \
    ZEPHYR_BASE=/workspace/zephyrproject/zephyr \
    PATH="/opt/zephyr-sdk-0.17.0/arm-zephyr-eabi/bin:${PATH}"

# Runtime dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    git \
    cmake \
    ninja-build \
    && rm -rf /var/lib/apt/lists/* && \
    pip3 install --break-system-packages west

# Copy built artifacts from builder stage
COPY --from=builder /workspace/zephyrproject /workspace/zephyrproject
COPY --from=builder /opt/zephyr-sdk-0.17.0 /opt/zephyr-sdk-0.17.0

WORKDIR /workspace

# Copy project overlay / config helpers
COPY app.overlay /workspace/app.overlay

# Flexible entrypoint: supports `west build` or custom commands
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["build", "-b", "esp32_devkitc_wroom/esp32/procpu"]