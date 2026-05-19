#!/usr/bin/env python3
"""Agent de veille quotidienne — Pape Malle BA."""

import os
import datetime
import smtplib
import subprocess
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import anthropic

# ── Configuration ────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_USER        = "papemalleba@gmail.com"
GMAIL_TO          = "papemalleba@gmail.com"
GMAIL_PASSWORD    = os.environ["GMAIL_APP_PASSWORD"]
GITHUB_TOKEN      = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USER       = "toxba851-creator"

TODAY = datetime.date.today().isoformat()


# ── 1. Vérification des sites ────────────────────────────────────────────────
def check_sites():
    if not os.path.exists("sites.txt"):
        return ["⚠️ `sites.txt` absent — aucune URL à surveiller"]

    with open("sites.txt") as f:
        urls = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    if not urls:
        return ["ℹ️ `sites.txt` vide — ajoutez des URLs pour activer la surveillance"]

    results = []
    for url in urls:
        try:
            r = requests.get(url, timeout=10, allow_redirects=True)
            icon = "✅" if r.status_code == 200 else "⚠️"
            results.append(f"{icon} `{url}` → HTTP {r.status_code}")
        except Exception as e:
            results.append(f"❌ `{url}` → Inaccessible ({str(e)[:60]})")
    return results


# ── 2. Repos GitHub ──────────────────────────────────────────────────────────
def get_github_repos():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    try:
        r = requests.get(
            f"https://api.github.com/users/{GITHUB_USER}/repos?sort=updated&per_page=5",
            headers=headers, timeout=10
        )
        if r.status_code == 200:
            return [
                f"- **{repo['name']}** — {repo.get('updated_at','?')[:10]} — {repo.get('description') or 'pas de description'}"
                for repo in r.json()
            ]
        return [f"⚠️ API GitHub: HTTP {r.status_code}"]
    except Exception as e:
        return [f"❌ Erreur GitHub: {e}"]


# ── 3. Contenu veille via Claude + web search ─────────────────────────────────
def generate_veille_content():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Tu es un agent de veille pour Pape Malle BA, graphiste et expert IA basé à Dakar, Sénégal.
Date du jour : {TODAY}.

Effectue des recherches web et génère un rapport de veille structuré (max 500 mots total).
Utilise EXACTEMENT ces sections markdown :

## Design & Graphisme
3-4 tendances UI/UX et typographie du moment. Sources : Dribbble, Behance, Awwwards.

## Couleurs Tendances
3-4 palettes/couleurs populaires cette semaine avec codes hex.

## Actualités IA & Tech
4-5 news clés de la semaine. Focus : outils IA pratiques, Afrique de l'Ouest numérique.

## Focus du Jour
1 recommandation actionnable pour Pape (marketplace IA, graphisme, développement web à Dakar).

Sois concis, direct et professionnel. Pas d'introduction générique."""

    messages = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]

    # Boucle agentique pour gérer les appels web search
    for _ in range(8):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            texts = [b.text for b in response.content if hasattr(b, "text") and b.text]
            return "\n".join(texts)

        # Continuer si tool_use
        messages.append({"role": "assistant", "content": response.content})
        tool_results = [
            {"type": "tool_result", "tool_use_id": b.id, "content": ""}
            for b in response.content if b.type == "tool_use"
        ]
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            texts = [b.text for b in response.content if hasattr(b, "text") and b.text]
            return "\n".join(texts)

    return "⚠️ Génération de contenu incomplète."


# ── 4. Assemblage du rapport ──────────────────────────────────────────────────
def build_report(veille_content, sites_results, github_repos):
    return f"""# Veille du {TODAY}

{veille_content}

---

## GitHub — Activité Récente

{'  '.join(chr(10) + r for r in github_repos)}

---

## Disponibilité Sites

{'  '.join(chr(10) + s for s in sites_results)}
"""


# ── 5. Sauvegarde ────────────────────────────────────────────────────────────
def save_report(report):
    os.makedirs("reports", exist_ok=True)
    path = f"reports/{TODAY}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return path


# ── 6. Commit & push ─────────────────────────────────────────────────────────
def commit_and_push(report_path):
    subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
    subprocess.run(["git", "config", "user.name", "Veille Bot"], check=True)
    subprocess.run(["git", "add", report_path], check=True)
    result = subprocess.run(
        ["git", "commit", "-m", f"veille: rapport du {TODAY}"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        subprocess.run(["git", "push"], check=True)
        print("Rapport commité et poussé.")
    else:
        print("Rien à commiter.")


# ── 7. Envoi email ───────────────────────────────────────────────────────────
def send_email(report_md):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"\U0001f50d Veille du {TODAY} — Design, IA & Projets"
    msg["From"]    = GMAIL_USER
    msg["To"]      = GMAIL_TO

    # Conversion markdown basique → HTML
    html_body = report_md \
        .replace("&", "&amp;") \
        .replace("<", "&lt;") \
        .replace("\n## ", "\n<h2>") \
        .replace("\n# ",  "\n<h1>")

    # Nettoyage des balises h non fermées
    import re
    html_body = re.sub(r'<(h[12])>(.*?)\n', r'<\1>\2</\1>\n', html_body)
    html_body = html_body.replace("\n", "<br>")

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:680px;margin:auto;padding:20px">
    {html_body}
    <hr><p style="color:#999;font-size:12px">Rapport complet : github.com/toxba851-creator/routine/blob/main/reports/{TODAY}.md</p>
    </body></html>"""

    msg.attach(MIMEText(report_md, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, GMAIL_TO, msg.as_string())
    print(f"Email envoyé à {GMAIL_TO}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"=== Veille du {TODAY} ===")

    print("[1/5] Vérification des sites...")
    sites = check_sites()

    print("[2/5] Récupération repos GitHub...")
    repos = get_github_repos()

    print("[3/5] Génération du contenu via Claude...")
    content = generate_veille_content()

    print("[4/5] Assemblage et sauvegarde du rapport...")
    report = build_report(content, sites, repos)
    path = save_report(report)

    print("[5/5] Commit, push et envoi email...")
    commit_and_push(path)
    send_email(report)

    print(f"Terminé. Rapport : {path}")


if __name__ == "__main__":
    main()
