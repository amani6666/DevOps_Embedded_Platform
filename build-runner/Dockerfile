FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk-0.16.8

# 1. Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    git cmake ninja-build gperf python3-pip python3-setuptools python3-tk \
    python3-wheel xz-utils file wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. West & outils Python
RUN pip3 install --no-cache-dir west pyelftools esptool

# 3. SDK Zephyr minimal (Toolchain ESP32)
WORKDIR /tmp
RUN wget -q https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.16.8/zephyr-sdk-0.16.8_linux-x86_64_minimal.tar.xz && \
    tar -xf zephyr-sdk-0.16.8_linux-x86_64_minimal.tar.xz -C /opt && \
    rm zephyr-sdk-0.16.8_linux-x86_64_minimal.tar.xz && \
    /opt/zephyr-sdk-0.16.8/setup.sh -t xtensa-espressif_esp32_zephyr-elf -h -c

WORKDIR /workspace

# 4. Initialisation Zephyr v4.0.0
RUN west init -m https://github.com/zephyrproject-rtos/zephyr --mr v4.0.0 -o=--depth=1 zephyrproject

WORKDIR /workspace/zephyrproject

# 5. Update ciblé pour éviter de surcharger WSL
RUN west config fetch.prune true && \
    west update --narrow -o=--depth=1 hal_espressif

WORKDIR /workspace
COPY app.overlay /workspace/app.overlay
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["build", "-b", "esp32_devkitc_wroom/esp32/procpu"]