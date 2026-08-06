# Erreur : west build échoue

## 1. "west: command not found"

### Symptômes
La commande `west build` retourne :

```
west: command not found
```

### Causes
- Le virtual environment Python n'est pas activé
- `west` n'a jamais été installé dans le venv

### Solutions
1. Activer le venv :
   ```
   source ~/zephyrproject/.venv/bin/activate
   ```
2. Si west est toujours absent :
   ```
   pip install west
   ```
3. Vérifier :
   ```
   west --version
```
