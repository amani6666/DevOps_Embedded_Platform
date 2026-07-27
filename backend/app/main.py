from fastapi import FastAPI
from pydantic import BaseModel
from agent1 import analyser_depot_complet

app = FastAPI(title="IoT Backend - Sahar")

class RequeteAnalyse(BaseModel):
    url_github: str

@app.get("/")
def racine():
    return {"message": "Backend is running"}

@app.post("/analyze")
def analyser(requete: RequeteAnalyse):
    rapport_complet = analyser_depot_complet(requete.url_github)
    return {
        "framework": rapport_complet.get("framework"),
        "fichiers_detectes": rapport_complet.get("fichiers_detectes", []),
        "carte_cible": rapport_complet.get("carte_cible", "unknown"),
        "protocoles": rapport_complet.get("protocoles", []),
        "confiance": rapport_complet.get("confiance"),
        "raisonnement": rapport_complet.get("raisonnement"),
    }

@app.post("/analyze/details")
def analyser_details(requete: RequeteAnalyse):
    return analyser_depot_complet(requete.url_github)
