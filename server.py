import os
import re
import sqlite3
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

# Chargement des variables d'environnement (clé API)
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 💾 Chemins vers la base de données
SQLALCHEMY_URI = "sqlite:///csv.db"  
SQLITE_PATH = "csv.db"              

# Vérifier si le fichier existe
if not os.path.exists(SQLITE_PATH):
    raise FileNotFoundError(f"Base de données non trouvée : {SQLITE_PATH}")

# 🔗 Connexion à la base pour LangChain
db = SQLDatabase.from_uri(SQLALCHEMY_URI)

# 🔮 Modèle LLM Gemini
llm = ChatGoogleGenerativeAI(model='gemini-1.5-pro', temperature=0.5)

# 🧠 Création de la chaîne LangChain
sql_chain = create_sql_query_chain(llm, db)
# 🚀 Lancement du serveur MCP
mcp = FastMCP("rag_sqlite_mcp_server")

# 🔎 Utilitaire pour extraire proprement la requête SQL depuis un texte
def extract_sql(text: str) -> str:
    if "```sql" in text:
        return re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL).group(1).strip()
    if "SQLQuery:" in text:
        return text.split("SQLQuery:")[1].strip()
    for line in text.splitlines():
        if "SELECT" in line.upper() or "PRAGMA" in line.upper():
            return line.strip()
    return text.strip()
# 📦 MCP : Ressource exposant les tables disponibles
@mcp.resource("database://csv")
def list_tables() -> str:
    """Retourne la liste des tables dans la base de données."""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    if not tables:
        return "Aucune table disponible dans la base de données."
    return str(tables)

# 📦 MCP : Ressource pour lister les colonnes d'une table donnée
@mcp.resource("database://csv/{table_name}/columns")
def list_columns(table_name: str) -> str:
    """Retourne la liste des colonnes dans une table donnée."""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [row[1] for row in cursor.fetchall()]  # Le nom des colonnes se trouve en position 1
    conn.close()
    if not columns:
        return f"Aucune colonne trouvée pour la table {table_name}."
    return str(columns)

# 📦 MCP : Ressource pour lister les lignes d'une table donnée
@mcp.resource("database://csv/{table_name}/rows")
def list_rows(table_name: str) -> str:
    """Retourne les lignes d'une table donnée."""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return f"Aucune ligne trouvée dans la table {table_name}."
    # Retourne seulement un nombre limité de lignes (par exemple 10) pour éviter une surcharge d'affichage
    return str(rows[:10])  # Limiter les résultats à 10 lignes pour éviter un trop grand volume de données


@mcp.resource("database://csv/students/{column_name}/data")
def list_column_data(column_name: str) -> str:
    """Retourne toutes les données d'une colonne spécifique de la table students."""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT {column_name} FROM students")
        rows = cursor.fetchall()

        conn.close()

        if rows:
            # Format de la réponse pour lister chaque élément de la colonne
            return "\n".join([str(row[0]) for row in rows])  # Chaque ligne correspond à un élément de la colonne
        else:
            return f"Aucune donnée trouvée dans la colonne '{column_name}'."

    except sqlite3.Error as e:
        conn.close()
        return f"Erreur lors de la récupération des données de la colonne {column_name}: {str(e)}"



@mcp.resource("database://csv/students/all/data")
def list_all_student_data() -> str:
    """Retourne toutes les données (lignes et colonnes) de la table students."""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM students")
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        conn.close()

        if rows:
            # Format de la réponse : une ligne par étudiant, chaque valeur de la ligne séparée par colonne
            result = "\n".join([", ".join([f"{columns[i]}: {row[i]}" for i in range(len(columns))]) for row in rows])
            return result
        else:
            return "Aucune donnée trouvée dans la table students."

    except sqlite3.Error as e:
        conn.close()
        return f"Erreur lors de la récupération des données de la table students : {str(e)}"

# 🛠️ MCP : Outil pour exécuter une requête SQL
@mcp.tool()
def execute_query(sql_query: str) -> str:
    """Exécute une requête SQL sur la base de données et retourne les résultats."""
    conn = sqlite3.connect(SQLITE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        if results:
            # Formater les résultats correctement pour chaque ligne
            formatted_results = "\n".join([str(row[0]) for row in results])  # Chaque ligne est un élément
            return formatted_results
        else:
            return "Requête exécutée avec succès, mais aucun résultat retourné."
    except sqlite3.Error as e:
        conn.close()
        return f"Erreur d'exécution de la requête SQL : {str(e)}"

# Fonction de prompt pour poser des questions en langage naturel
# @mcp.prompt()
# def ask_database_prompt(question: str) -> str:
#     """Utilise LangChain pour transformer une question en requête SQL."""
#     result = sql_chain.invoke({"question": question})
#     return extract_sql(result)

@mcp.prompt()
def ask_database_prompt(question: str) -> str:
    """Utilise LangChain pour transformer une question en requête SQL complète."""
    result = sql_chain.invoke({"question": f"{question}. Donne une requête SQL complète avec toutes les colonnes si possible."})
    return extract_sql(result)

#######################################




# 2. Fonction de prompt pour poser des questions en langage naturel

# 3. Fonction de ressource pour interroger la base de données avec une question en langage naturel
@mcp.resource("database://csv/query/{question}")
def ask_and_execute_query(question: str) -> str:
    """Demande à exécuter une requête SQL générée par le LLM."""
    
    # Utiliser le prompt pour transformer la question en une instruction SQL
    prompt_response = ask_database_prompt(question)
    
    # On extrait la requête SQL à partir du prompt
    sql_query = extract_sql_from_prompt(prompt_response)
    
    # Exécuter la requête via l'outil 'execute_query'
    return execute_query(sql_query)

# Fonction pour extraire la requête SQL à partir du prompt généré
def extract_sql_from_prompt(prompt_response: str) -> str:
    """Extrait la requête SQL d'un prompt donné par le LLM."""
    # Rechercher la requête SQL dans le texte du prompt
    match = re.search(r"SQLQuery:(.*)", prompt_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return prompt_response.strip()

# ▶️ Lancer le serveur (mode console stdio)
if __name__ == "__main__":
    mcp.run(transport="stdio")
