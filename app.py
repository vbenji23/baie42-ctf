#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baie 42 — backend CTF VOLONTAIREMENT VULNERABLE (lab d'entrainement).

/!\\ AVERTISSEMENT
Ce code contient des failles REELLES et intentionnelles (SQLi, SSTI, injection
de commandes, path traversal). Il sert uniquement a l'entrainement en
cybersecurite, comme DVWA ou OWASP Juice Shop.
- A lancer UNIQUEMENT en local ou dans un conteneur isole.
- NE JAMAIS exposer sur Internet ni sur un reseau de production.

Chaque faille, une fois exploitee, renvoie un flag CTF{...}.
Les correctifs sont indiques en commentaire a cote de chaque vulnerabilite.
"""
import os
import sqlite3
import subprocess
from flask import Flask, request, jsonify, render_template_string, send_file, g

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "baie42.db")

FLAGS = {
    "sqli": "CTF{sqli_r33ll3_byp4ss_4uth}",
    "ssti": "CTF{ssti_j1nj4_rc3_r33ll3}",
    "cmdi": "CTF{1nj3ct10n_c0mm4nd3_r33ll3}",
    "path": "CTF{p4th_tr4v3rs4l_r33ll3}",
}

# Fichier "secret" lu via le path traversal (simule /etc/passwd du lab)
SECRET_FILE = os.path.join(os.path.dirname(__file__), "secret.txt")
# Dossier public des telechargements (le secret est un cran au-dessus)
FILES_DIR = os.path.join(os.path.dirname(__file__), "files")


# --------------------------------------------------------------------------
# Base de donnees
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS utilisateurs")
    cur.execute(
        "CREATE TABLE utilisateurs (id INTEGER PRIMARY KEY, login TEXT, mdp TEXT, role TEXT)"
    )
    cur.executemany(
        "INSERT INTO utilisateurs (login, mdp, role) VALUES (?,?,?)",
        [
            ("guest", "guest", "client"),
            ("support", "support123", "support"),
            ("admin", "jardin", "admin"),
        ],
    )
    con.commit()
    con.close()
    # secret.txt est hors du dossier de telechargement -> cible du path traversal
    with open(SECRET_FILE, "w", encoding="utf-8") as f:
        f.write("fichier interne du serveur\n" + FLAGS["path"] + "\n")
    # dossier public des telechargements + un fichier legitime
    os.makedirs(FILES_DIR, exist_ok=True)
    with open(os.path.join(FILES_DIR, "catalogue.txt"), "w", encoding="utf-8") as f:
        f.write("Catalogue public Baie 42 : switch, serveur, proxy...\n")


# --------------------------------------------------------------------------
# Page d'accueil : mode d'emploi du lab
# --------------------------------------------------------------------------
INDEX = """<!doctype html><html lang=fr><meta charset=utf-8>
<title>Baie 42 — backend vulnerable</title>
<style>body{font-family:system-ui,sans-serif;max-width:820px;margin:2rem auto;padding:0 1rem;
line-height:1.5;color:#17283a;background:#e9eef2}code{background:#dce3e9;padding:.1rem .3rem;border-radius:3px}
h1{font-family:Arial Narrow,sans-serif}.w{border-left:4px solid #c2412d;background:#f7f9fb;padding:.8rem 1rem}
a{color:#2f6fb0}pre{background:#15222f;color:#cdd9e5;padding:1rem;border-radius:6px;overflow:auto}</style>
<h1>Baie 42 — backend CTF (vulnerable)</h1>
<p class=w><strong>Lab d'entrainement.</strong> Failles reelles et volontaires. A lancer en local
ou en conteneur isole uniquement, jamais en production.</p>
<p>4 endpoints vulnerables. Chaque exploitation renvoie un flag.</p>
<h2>1. Injection SQL — <code>POST /login</code></h2>
<pre>curl -s http://localhost:5000/login -d "login=admin' -- &mdp=x"</pre>
<h2>2. SSTI (Jinja2) — <code>GET /salut?nom=...</code></h2>
<pre>curl -s "http://localhost:5000/salut?nom={{7*7}}"
curl -s "http://localhost:5000/salut?nom={{config}}"</pre>
<h2>3. Injection de commandes — <code>GET /ping?hote=...</code></h2>
<pre>curl -s "http://localhost:5000/ping?hote=127.0.0.1;id"</pre>
<h2>4. Path traversal — <code>GET /telecharger?f=...</code></h2>
<pre>curl -s "http://localhost:5000/telecharger?f=../secret.txt"</pre>
<p>Correctifs commentes dans <code>app.py</code>. Frontend CTF complet : le fichier HTML Baie 42.</p>
</html>"""


@app.route("/")
def index():
    return INDEX


# --------------------------------------------------------------------------
# 1) INJECTION SQL (reelle) — authentification
# --------------------------------------------------------------------------
@app.route("/login", methods=["POST"])
def login():
    login_ = request.form.get("login", "")
    mdp = request.form.get("mdp", "")

    # VULNERABLE : la requete est construite par concatenation de chaines.
    #   Une entree comme   admin' --   contourne le mot de passe.
    # CORRECTIF : requete parametree ->
    #   cur.execute("SELECT * FROM utilisateurs WHERE login=? AND mdp=?", (login_, mdp))
    query = "SELECT * FROM utilisateurs WHERE login='%s' AND mdp='%s'" % (login_, mdp)
    try:
        rows = get_db().execute(query).fetchall()
    except sqlite3.Error as e:
        return jsonify({"erreur": str(e), "requete": query}), 400

    if rows:
        user = rows[0]
        resp = {"connecte": True, "login": user["login"], "role": user["role"], "requete": query}
        # Si l'injection a fait tomber le filtre de mot de passe, on recompense.
        if mdp == "" or "'" in login_ or "'" in mdp or "--" in login_ or "--" in mdp:
            resp["flag"] = FLAGS["sqli"]
        return jsonify(resp)
    return jsonify({"connecte": False, "requete": query})


# --------------------------------------------------------------------------
# 2) SSTI (reelle) — rendu d'un gabarit a partir d'une entree utilisateur
# --------------------------------------------------------------------------
@app.route("/salut")
def salut():
    nom = request.args.get("nom", "visiteur")

    # VULNERABLE : l'entree utilisateur est injectee dans le template puis evaluee.
    #   {{7*7}} => 49 ,  {{config}} => exposition de la config , etc.
    # CORRECTIF : ne jamais passer d'entree utilisateur au moteur. Utiliser
    #   render_template avec des variables : render_template("salut.html", nom=nom)
    gabarit = "<p>Bonjour %s !</p>" % nom
    rendu = render_template_string(gabarit)

    # Detection pedagogique : si l'utilisateur a prouve l'execution, on donne le flag.
    if nom.strip() not in ("", "visiteur") and ("{{" in nom):
        rendu += "<p>Flag : %s</p>" % FLAGS["ssti"]
    return rendu


# --------------------------------------------------------------------------
# 3) INJECTION DE COMMANDES (reelle) — outil ping
# --------------------------------------------------------------------------
@app.route("/ping")
def ping():
    hote = request.args.get("hote", "127.0.0.1")

    # VULNERABLE : l'entree est passee a un shell (shell=True) sans validation.
    #   127.0.0.1;id    enchaine une commande arbitraire.
    # CORRECTIF : pas de shell. subprocess.run(["ping","-c","1",hote], shell=False)
    #   + validation stricte de l'hote (regex IP/nom).
    try:
        sortie = subprocess.check_output(
            "ping -c 1 " + hote, shell=True, stderr=subprocess.STDOUT, timeout=5
        ).decode(errors="replace")
    except subprocess.CalledProcessError as e:
        sortie = e.output.decode(errors="replace")
    except Exception as e:  # noqa
        sortie = str(e)

    reponse = {"sortie": sortie}
    if any(c in hote for c in (";", "|", "&", "`", "$(")):
        reponse["flag"] = FLAGS["cmdi"]
    return jsonify(reponse)


# --------------------------------------------------------------------------
# 4) PATH TRAVERSAL (reel) — telechargement de fichier
# --------------------------------------------------------------------------
@app.route("/telecharger")
def telecharger():
    nom = request.args.get("f", "catalogue.txt")

    # VULNERABLE : le nom de fichier vient de l'utilisateur sans normalisation,
    # et il est joint directement au dossier public. '../secret.txt' remonte
    # d'un cran et lit un fichier hors du dossier de telechargement.
    # CORRECTIF : chemin = os.path.join(FILES_DIR, os.path.basename(nom)) PUIS
    #   verifier os.path.realpath(chemin).startswith(os.path.realpath(FILES_DIR)).
    chemin = os.path.join(FILES_DIR, nom)
    if os.path.exists(chemin) and os.path.isfile(chemin):
        return send_file(os.path.abspath(chemin), mimetype="text/plain")
    return jsonify({"erreur": "fichier introuvable", "demande": nom, "chemin": chemin}), 404


if __name__ == "__main__":
    init_db()
    # host=127.0.0.1 par defaut : ne pas binder 0.0.0.0 hors conteneur isole.
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")))
