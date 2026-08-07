# Erreur : prj.conf et Kconfig

## 1. Syntaxe de base de prj.conf

### Règles officielles
- Chaque option commence par `CONFIG_`
- Pas d'espace autour du signe `=`
- Les booléens utilisent `y` (activé) ou `n` (désactivé)
- Les chaînes utilisent des guillemets doubles

### Exemples corrects
```kconfig
CONFIG_GPIO=y
CONFIG_FPU=y
CONFIG_SOME_STRING="cool value"
CONFIG_SOME_INT=123
```

### Format historique pour "désactivé"
```kconfig
# CONFIG_SOME_OTHER_BOOL is not set
```
Ce format est accepté pour compatibilité avec Make.

## 2. "warning: attempt to assign the value 'y' to the undefined symbol X"

### Symptômes
```
warning: attempt to assign the value 'y' to the undefined symbol BLUETOOTH_CTRL
```

### Causes
- Faute de frappe dans le nom du symbole Kconfig
- Le symbole a été renommé ou supprimé dans cette version de Zephyr

### Solutions
- Rechercher le bon symbole via menuconfig :
  ```bash
  west build -t menuconfig
  ```
  Puis appuyer sur / pour chercher.
- Consulter le guide de migration de la release notes.

## 3. Où placer prj.conf

### Emplacement correct
prj.conf doit être à la racine du projet applicatif, au même niveau que CMakeLists.txt.

### Structure minimale
```
mon_projet/
├── CMakeLists.txt
├── prj.conf
└── src/
    └── main.c
```

### Fichiers additionnels
- prj_release.conf : build type release
- boards/<carte>.conf : configuration spécifique à une carte

Pour utiliser un fichier alternatif :
```bash
west build -- -DCONF_FILE=prj_release.conf
```

## 4. Comment les configurations sont fusionnées

Ordre de fusion :
1. *_defconfig de la carte (board)
2. prj.conf de l'application
3. EXTRA_CONF_FILE

Le résultat est dans build/zephyr/.config.

### Important
- prj.conf a le dernier mot
- menuconfig modifie .config directement - ces changements sont perdus si on fait west build -p always

## 5. Options fréquentes dans prj.conf
```kconfig
CONFIG_BT=y                    # Activer Bluetooth
CONFIG_WIFI=y                  # Activer WiFi
CONFIG_MQTT=y                  # Activer MQTT
CONFIG_SENSOR=y                # Activer les capteurs
CONFIG_GPIO=y                  # Activer GPIO
CONFIG_SERIAL=y                # Activer UART
CONFIG_CONSOLE=y               # Activer la console
CONFIG_UART_CONSOLE=y          # Console sur UART
CONFIG_LOG=y                   # Activer le logging
CONFIG_PRINTK=y                # Activer printk
CONFIG_SIZE_OPTIMIZATIONS=y    # Optimiser pour la taille
```

Source : docs.zephyrproject.org/latest/build/kconfig/setting.html