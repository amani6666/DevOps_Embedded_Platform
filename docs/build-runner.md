# Build Runner — Commande exacte pour Sahar / Agent 4

## Lancer un build
```bash
docker build -t build-runner ./build-runner
docker run --rm -v "$(pwd)/firmware:/app" build-runner build -p auto -b esp32_devkitc_wroom/esp32/procpu /app