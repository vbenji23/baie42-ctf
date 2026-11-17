https://vbenji23.github.io/baie42-ctf/ liens du site ctf si vous vouler le visiter 

AYER UN PEUX DE RESPECT POUR LE PROJET PAS DE NMAP PAS DE SCAN ET AUCUNE TENTATIVE D4ATAQUE NE SERA TOLERE 

# Baie 42 — backend CTF vulnérable (lab DevSecOps)

Backend d'entraînement **volontairement vulnérable** qui accompagne le CTF Baie 42.
Contrairement au front HTML (où les failles sont simulées en JavaScript), ici les
vulnérabilités sont **réelles** : injection SQL, SSTI, injection de commandes et
path traversal s'exploitent pour de vrai avec `curl`.

> ⚠️ **Avertissement.** Ce code contient des failles intentionnelles, comme DVWA
> ou OWASP Juice Shop. À lancer **uniquement en local ou dans un conteneur isolé**.
> Ne jamais l'exposer sur Internet ni sur un réseau de production.

## Lancer le lab

### Option A — Python

```bash
pip install -r requirements.txt
python app.py
# -> http://127.0.0.1:5000
```

### Option B — Docker

```bash
docker compose up --build
# -> http://127.0.0.1:5000
```

La page d'accueil (`/`) rappelle les endpoints et des exemples de payloads.

## Les 4 vulnérabilités

| # | Faille | Endpoint | Exploitation | Correctif |
|---|--------|----------|--------------|-----------|
| 1 | Injection SQL | `POST /login` | `login=admin' -- ` | Requête paramétrée (`?`) |
| 2 | SSTI (Jinja2) | `GET /salut?nom=` | `{{7*7}}`, `{{config}}` | Pas d'entrée dans le template |
| 3 | Injection de commandes | `GET /ping?hote=` | `127.0.0.1;id` | `subprocess` sans `shell=True` + validation |
| 4 | Path traversal | `GET /telecharger?f=` | `../secret.txt` | `basename()` + racine figée |

### Exemples

```bash
# 1. Injection SQL (contourne le mot de passe)
curl -s http://127.0.0.1:5000/login --data-urlencode "login=admin' -- " -d "mdp=x"

# 2. SSTI : exécution côté serveur
curl -s "http://127.0.0.1:5000/salut?nom=%7B%7B7*7%7D%7D"
curl -s "http://127.0.0.1:5000/salut?nom=%7B%7Bconfig%7D%7D"

# 3. Injection de commandes
curl -s "http://127.0.0.1:5000/ping?hote=127.0.0.1;id"

# 4. Path traversal
curl -s "http://127.0.0.1:5000/telecharger?f=../secret.txt"
```

Chaque exploitation réussie renvoie un flag au format `CTF{...}`.
Les correctifs sont commentés directement à côté de chaque faille dans `app.py`.

## Pipeline DevSecOps (`.gitlab-ci.yml`)

Le pipeline illustre une chaîne CI/CD sécurisée, avec les étapes de sécurité
**bloquantes** (contrairement au défi « pipeline sans contrôle » du front) :

```
build ─> test ─> security (Gitleaks + Trivy) ─> deploy (manuel)
```

- **Gitleaks** : détection de secrets dans le dépôt.
- **Trivy** : scan des dépendances et de la configuration (sévérités HIGH/CRITICAL).
- **deploy** : manuel, uniquement sur `main`, et seulement si la sécurité passe.

## Structure

```
baie42-backend/
├── app.py              # application Flask (failles + correctifs commentés)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitlab-ci.yml      # pipeline build/test/security/deploy
├── .gitignore
└── README.md
```

## Avertissement légal

Projet pédagogique. N'exploitez ces techniques que sur ce lab ou sur des systèmes
pour lesquels vous avez une autorisation écrite. Tester un système tiers sans
autorisation est illégal.

# Baie 42 — CTF cybersécurité

**[🔗 Jouer au CTF en ligne](https://vbenji23.github.io/baie42-ctf/)**

> AYEZ UN PEU DE RESPECT POUR LE PROJET : PAS DE NMAP, PAS DE SCAN, ET AUCUNE
> TENTATIVE D'ATTAQUE NE SERA TOLÉRÉE.

Plateforme d'entraînement CTF sur le thème d'une boutique fictive de matériel
réseau, **volontairement truffée de failles**. Projet réalisé dans le cadre de
ma formation en cybersécurité (Guardia Cyber School).

## Deux parties

### 1. Front interactif — `index.html`
Une page unique, sans dépendance, **78 épreuves** réparties en catégories :
Web · Injection SQL · SSTI · XSS · Session (JWT, cookies) · Encodage · Crypto ·
Logique métier · Achat · Back-office · **DevSecOps (CI/CD)** · **SOC** · **EDR** ·
Reverse engineering · Réseau (PCAP) · DFIR · Phishing · Force brute.

Fonctions : score, chrono, classement local, badges, indices à points, mode
formateur, export writeup, cartographie **MITRE ATT&CK** et certificat de réussite.
Les failles y sont **simulées en JavaScript** (aucun serveur requis).

### 2. Backend vulnérable — Flask
Contrairement au front, les vulnérabilités du backend sont **réelles** et
s'exploitent avec `curl` :

| # | Faille | Endpoint | Exploitation | Correctif |
|---|--------|----------|--------------|-----------|
| 1 | Injection SQL | `POST /login` | `login=admin' -- ` | Requête paramétrée |
| 2 | SSTI (Jinja2) | `GET /salut?nom=` | `{{7*7}}`, `{{config}}` | Pas d'entrée dans le template |
| 3 | Injection de commandes | `GET /ping?hote=` | `127.0.0.1;id` | `subprocess` sans `shell=True` |
| 4 | Path traversal | `GET /telecharger?f=` | `../secret.txt` | `basename()` + racine figée |

Chaque exploitation renvoie un flag `CTF{...}`. Les correctifs sont commentés
dans `app.py`.

> ⚠️ Le backend contient des failles intentionnelles (comme DVWA / OWASP Juice
> Shop). À lancer **en local ou en conteneur isolé uniquement**, jamais exposé.

```bash
pip install -r requirements.txt && python app.py   # ou : docker compose up --build
# -> http://127.0.0.1:5000
```

## Pipeline DevSecOps — `.gitlab-ci.yml`
`build → test → security (Gitleaks + Trivy, bloquants) → deploy (manuel)`.
Gitleaks détecte les secrets, Trivy scanne les dépendances (HIGH/CRITICAL), et
le déploiement est manuel et conditionné à la réussite de la sécurité.

## Compétences mises en œuvre
- Sécurité **offensive** : OWASP Top 10, exploitation web, reverse, crypto.
- Sécurité **défensive** : analyse SOC/EDR, forensic, timeline d'incident, MITRE ATT&CK.
- **DevSecOps** : Docker, CI/CD, scan de secrets et de vulnérabilités.
- Développement front (HTML/CSS/JS sans framework) et back (Python/Flask).

## Structure
```
baie42-ctf/
├── index.html          # le CTF (78 épreuves)
├── app.py              # backend Flask vulnérable (+ correctifs commentés)
├── Dockerfile
├── docker-compose.yml
├── .gitlab-ci.yml      # pipeline DevSecOps
├── requirements.txt
└── README.md
```

## Avertissement légal
Projet pédagogique. N'exploitez ces techniques que sur ce lab ou sur des systèmes
pour lesquels vous avez une autorisation écrite. Tester un système tiers sans
autorisation est illégal.
