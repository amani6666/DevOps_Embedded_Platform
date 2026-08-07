# Erreur : MQTT et Mosquitto

## 1. "Connection refused" au broker MQTT

### Symptomes
Le client MQTT ne parvient pas a se connecter, timeout ou message "connection refused".

### Causes
1. Le conteneur Mosquitto n'est pas demarre
2. Mauvais port (1883 vs 8883 pour TLS)
3. Authentification requise mais non configuree

### Solutions
1. Verifier que Mosquitto tourne :
   ```bash
   docker compose ps | grep mosquitto
   ```
2. Tester avec mosquitto_pub :
   ```bash
   mosquitto_pub -h localhost -p 1883 -t test -m "hello"
   ```
3. Verifier la configuration dans mosquitto/config/mosquitto.conf

## 2. Configuration minimale de Mosquitto
```
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
```

## 3. Verifier la connectivite reseau
```bash
# Depuis le conteneur backend
docker exec -it <nom_backend> sh
ping mosquitto
telnet mosquitto 1883
```

## 4. Topics MQTT courants pour IoT
- sensors/temperature : Donnees de temperature
- sensors/humidity : Donnees d'humidite
- actuators/led : Commande LED
- alerts/critical : Alertes systeme