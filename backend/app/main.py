from fastapi import FastAPI
from pydantic import BaseModel
from agent1 import analyser_depot_complet
from agent4 import indexer_tous_les_documents, repondre_question, repondre_avec_llm

app = FastAPI(title="IoT Backend - Sahar")

class RequeteAnalyse(BaseModel):
    url_github: str

class QuestionRAG(BaseModel):
    question: str

# ═════════════════════════════════════════════════════════════════════
# Racine
# ═════════════════════════════════════════════════════════════════════
@app.get("/")
def racine():
    return {"message": "Backend is running"}

# ═════════════════════════════════════════════════════════════════════
# Agent 1 — Analyseur de projets embarqués
# ═════════════════════════════════════════════════════════════════════
@app.post("/analyze")
def analyser(requete: RequeteAnalyse):
    rapport = analyser_depot_complet(requete.url_github)
    return {
        "framework": rapport.get("framework"),
        "fichiers_detectes": rapport.get("fichiers_detectes", []),
        "carte_cible": rapport.get("carte_cible", "unknown"),
        "protocoles": rapport.get("protocoles", []),
        "confiance": rapport.get("confiance"),
        "raisonnement": rapport.get("raisonnement"),
    }

@app.post("/analyze/details")
def analyser_details(requete: RequeteAnalyse):
    return analyser_depot_complet(requete.url_github)

# ═════════════════════════════════════════════════════════════════════
# Agent 4 — Assistant RAG
# ═════════════════════════════════════════════════════════════════════
@app.post("/assistant")
def assistant(requete: QuestionRAG):
    """
    Endpoint RAG mock — retourne les extraits trouvés sans LLM.
    Consomme 0 token Groq.
    """
    return repondre_question(requete.question)

@app.post("/assistant/llm")
def assistant_llm(requete: QuestionRAG):
    """
    Endpoint RAG complet avec LLM Groq.
    À utiliser quand les tokens sont revenus.
    """
    return repondre_avec_llm(requete.question)

# ═════════════════════════════════════════════════════════════════════
# Indexation au démarrage
# ═════════════════════════════════════════════════════════════════════
@app.on_event("startup")
def on_startup():
    print("🚀 Démarrage du backend...")
    indexer_tous_les_documents()
    print("✅ Backend prêt")