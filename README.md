# Monitoring Réseau Client-Serveur — Mini-Projet RT2 2025/2026 

## Auteurs
**Hamdi Mohamed Aziz** & **Maddouri Ferdaous**   
## Encadrant  
**Dr. Kamel Karoui**

---

## Description
Application de monitoring réseau distribuée basée sur une architecture client-serveur TCP/UDP.  
Les agents collectent périodiquement les métriques CPU et RAM et les envoient à un serveur central qui agrège les données, détecte les agents inactifs et exporte les statistiques en CSV.

---

## Fichiers

| Fichier | Description |
|---|---|
| `serveurTCP.py` | Serveur TCP principal avec anti-flood |
| `clientTCO.py` | Agent de monitoring TCP |
| `serveurUDP.py` | Serveur UDP (extension) |
| `clientUDP.py` | Client UDP (extension) |
| `customClient.py` | Client personalisé  |
| `flood.py` | Simulation d'attaque DoS |
| `requirements.txt` | Dépendances Python |

## Fichiers générés automatiquement

| Fichier | Contenu |
|---|---|
| `stats_<horodatage>.csv` | Statistiques TCP exportées à chaque cycle |
| `statsUDP_<horodatage>.csv` | Statistiques UDP exportées à chaque cycle |


---

## Installation & Configuration

### Prérequis
- Windows avec WSL2
- Python 3.12+

### Étape 1 — Installer WSL (si pas encore fait)
```powershell
# Dans PowerShell (Windows)
wsl --install
```

### Étape 2 — Lancer Ubuntu et mettre à jour
```bash
wsl -d Ubuntu
sudo apt update
sudo apt install python3-pip
sudo apt install python3.12-venv
sudo apt install python3-tk
```

### Étape 3 — Créer le virtual environment
> ⚠️ Assurez-vous d'être dans le répertoire du mini-projet avant de continuer

```bash
cd /chemin/vers/mini-projet

# Créer un venv isolé sans pip
python3 -m venv --without-pip venv

# Activer le venv
source venv/bin/activate
```

### Étape 4 — Installer pip manuellement dans le venv
> ⚠️ À faire uniquement la première fois

```bash
curl -sS https://bootstrap.pypa.io/get-pip.py | python
```

### Étape 5 — Installer les dépendances
> ⚠️ À faire uniquement la première fois

```bash
pip install -r requirements.txt
```

---

## Exécution

Deux modes sont disponibles : **manuel** (avec venv) ou **automatique** (via script batch, sans prérequis).

### Mode automatique — Tests (Windows)
Aucune installation requise. Depuis l'explorateur Windows ou PowerShell, double-cliquez sur :

```
run_tests.bat
```

Ce script lance automatiquement la suite de tests sans nécessiter de virtual environment ni d'installation de dépendances.

---

### Mode manuel — Lancement individuel

> À chaque nouvelle session, activer le venv d'abord :
> ```bash
> source venv/bin/activate
> ```

#### 1. Lancer le serveur TCP
```bash
python3 serveurTCP.py
```

#### 2. Lancer un ou plusieurs clients (dans de nouveaux terminaux)
```bash
# UUID aléatoire généré automatiquement
python3 clientTCP.py

# Ou avec un nom fixe
python3 clientTCP.py agent1
```

#### 3. Lancer le serveur UDP (optionnel)
```bash
python3 serveurUDP.py
```

#### 4. Lancer le client UDP (optionnel)
```bash
python3 clientUDP.py
```

#### 5. Simulation d'attaque flood (optionnel)
```bash
python3 flood.py
```
