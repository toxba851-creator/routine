# Configuration — Veille Automatique

## 1. Secrets GitHub à créer

Va dans **Settings → Secrets and variables → Actions → New repository secret** :

| Secret | Valeur | Comment l'obtenir |
|--------|--------|-------------------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | [console.anthropic.com](https://console.anthropic.com) |
| `GMAIL_APP_PASSWORD` | `xxxx xxxx xxxx xxxx` | Voir étape 2 ci-dessous |

## 2. Créer un App Password Gmail

1. Va sur [myaccount.google.com/security](https://myaccount.google.com/security)
2. Active la **vérification en 2 étapes** (si pas déjà fait)
3. Retourne dans Sécurité → **Mots de passe des applications**
4. Sélectionne *Autre (nom personnalisé)* → tape `Veille Bot` → Générer
5. Copie le mot de passe à 16 caractères → colle-le dans le secret `GMAIL_APP_PASSWORD`

## 3. Ajouter des sites à surveiller

Édite `sites.txt` et ajoute une URL par ligne :
```
https://monportfolio.com
https://marketplace-ia.com
https://monsite-client.sn
```

## 4. Déclenchement

- **Automatique** : chaque matin à **7h00 (heure Dakar)**
- **Manuel** : onglet *Actions* → *Veille Quotidienne* → *Run workflow*

## 5. Voir les rapports

Chaque rapport est sauvegardé dans `reports/YYYY-MM-DD.md` et envoyé par email à `papemalleba@gmail.com`.
