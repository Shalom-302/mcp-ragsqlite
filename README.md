
# 📦 MCP Server Demo – RagSQLite x LangChain x Gemini

Ce projet est une démo d'un **serveur MCP (Model Context Protocol)** qui prend des **questions en langage naturel**, les convertit en **requêtes SQL via LangChain et Gemini**, exécute les requêtes sur une base de données SQLite issue d’un fichier CSV, puis renvoie les résultats de manière structurée via le protocole MCP.

---

## ✨ Objectif

Créer un assistant intelligent capable de comprendre une requête comme :

> "Donne-moi la liste des étudiants en mathématiques"

Et de la convertir dynamiquement en SQL, l’exécuter, et répondre avec les données correspondantes.

---

## 🛠️ Installation

### 1. Cloner le projet

```bash
git clone https://github.com/Shalom-302/mcp-ragsqlite.git
cd mcp-ragsqlite
```

### 2. Initialiser l’environnement Python avec `uv`

```bash
uv init mcp-server-demo
cd mcp-server-demo
source .venv/bin/activate
```

> Tu peux aussi utiliser `python -m venv .venv && source .venv/bin/activate` si `uv` n’est pas dispo.

### 3. Installer les dépendances

```bash
uv sync
# ou
pip install -r requirements.txt
```

---

## 🧱 Configuration

### 1. Fichier `.env`

Crée un fichier `.env` à la racine avec ta clé API Gemini :

```env
GOOGLE_API_KEY=ta_clé_api_gemini
```

### 2. Préparer la base de données

Le fichier `data.csv` contient les données des étudiants.

> Exemple : `1001,John,Doe,Mathematics,95`

Exécute le script de migration :

```bash
python migration.py
```

Cela crée le fichier `csv.db` avec une table `students`.

---

## 🚀 Lancer le serveur MCP

```bash
python server.py
```

Le serveur expose alors plusieurs **ressources MCP**, dont :

- `database://csv/query/{question}`
- `database://csv/students/{column_name}/data`
- `database://csv/students/{row_id}/data`

Et des **tools** comme :

- `execute_query(sql_query: str)`

Le prompt LangChain est utilisé pour convertir une question NLP en requête SQL à l’aide de Gemini via l’outil `ask_database_prompt`.

---

## 🔄 Fonctionnalité principale (Use case RagSQLite)

**Requête NLP ➡️ Prompt LangChain ➡️ SQL ➡️ Résultat MCP**

Tu peux tester par exemple :

```http
GET database://csv/query/donne moi toutes les lignes de la table students
```

Et recevoir une réponse structurée contenant toutes les données.

---

## 🧪 À faire / Bugs connus

- [ ] Améliorer la gestion des erreurs quand Gemini génère une requête invalide.
- [ ] Ajouter des tests unitaires sur les outils MCP.
- [ ] Étendre la base pour d’autres types de requêtes (insert/update).

---
