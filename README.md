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
