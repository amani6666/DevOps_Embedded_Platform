# Erreur : Docker et Docker Compose

## 1. "docker: command not found" ou "Cannot connect to Docker daemon"

### Symptômes
```
docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

### Causes
- Docker Desktop n'est pas lancé
- L'intégration WSL n'est pas activée

### Solutions
1. Ouvrir Docker Desktop sur Windows
2. Settings → Resources → WSL Integration → activer Ubuntu
3. Redémarrer Docker Desktop
4. Dans WSL : docker run hello-world

## 2. "port is already allocated" (port 8000 occupé)

### Symptômes
```
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
```

### Solutions
1. Voir quel processus utilise le port :
   ```bash
   sudo netstat -tlnp | grep 8000
   ```
2. Arrêter les conteneurs existants :
   ```bash
   docker compose down
   ```
3. Tuer le processus si nécessaire :
   ```bash
   kill -9 <PID>
   ```

## 3. Le conteneur backend s'arrête immédiatement

### Causes
- Le fichier .env est manquant
- Une erreur Python au démarrage

### Solutions
- Vérifier les logs :
  ```bash
  docker compose logs backend
  ```
- Vérifier que .env existe :
  ```bash
  ls -la ~/iot_project/.env
  ```
- Rebuild forcé :
  ```bash
  docker compose down
  docker rmi iot-project-backend:latest
  docker compose build --no-cache backend
  docker compose up -d
  ```

## 4. Commandes de diagnostic essentielles
```bash
docker compose ps              # Voir les conteneurs actifs
docker compose logs backend    # Logs du backend
docker compose logs -f backend # Logs en temps reel
docker compose down            # Arreter tout
docker compose up -d           # Demarrer en arrière-plan
docker compose up --build      # Rebuild et demarrer
docker system prune -f         # Nettoyer les images/volumes inutilises
```
