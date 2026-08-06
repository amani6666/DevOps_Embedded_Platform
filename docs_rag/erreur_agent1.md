# Erreur : Agent 1 - Analyse de projet embarque

## 1. "framework": "inconnu" alors que le projet est bien embarque

### Symptomes
L'API POST /analyze retourne :
```json
{"framework": "inconnu", "confiance": "basse"}
```

### Causes
- Le repository GitHub est prive ou l'URL est incorrecte
- Le projet n'a pas de fichier signature reconnu
- Le clone a echoue (probleme reseau, repo trop gros)

### Solutions
- Verifier que l'URL est publique et correcte
- Verifier les fichiers a la racine apres clone manuel :
  ```bash
  git clone --depth 1 <URL> /tmp/test-repo
  ls /tmp/test-repo
  ```
- Tester avec un repo connu :
  ```bash
  curl -X POST http://localhost:8000/analyze \
    -d '{"url_github": "https://github.com/arduino-libraries/WiFi101"}'
  ```

## 2. Fichiers recherches par l'Agent 1

| Fichier | Framework detecte |
|---------|------------------|
| prj.conf | Zephyr RTOS |
| platformio.ini | Arduino / PlatformIO |
| sdkconfig | ESP-IDF |
| mbed_app.json | Mbed OS |
| *.ino | Arduino (indice bonus) |

## 3. L'Agent 1 retourne une erreur 500

### Causes
- La cle API Groq n'est pas definie dans .env
- Le repo GitHub est inaccessible (firewall, prive)

### Solutions
- Verifier .env :
  ```bash
  cat ~/iot_project/.env | grep GROQ
  ```
- Verifier que le backend peut cloner :
  ```bash
  docker exec -it <backend> git clone --depth 1 https://github.com/zephyrproject-rtos/zephyr /tmp/test
  ```

## 4. Endpoints disponibles

| Endpoint | Usage | Output |
|----------|-------|--------|
| POST /analyze | Stable - utilise par l'equipe | 6 champs (framework, fichiers_detectes, carte_cible, protocoles, confiance, raisonnement) |
| POST /analyze/details | Demo soutenance | Tout : memoire agent, chain-of-thought, validation, metadonnees |