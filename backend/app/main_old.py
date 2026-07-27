from fastapi import FastAPI
from pydantic import BaseModel
from agent1 import analyser_depot_complet

app = FastAPI()

class RequeteAnalyse(BaseModel):
    url_github: str

@app.get("/")
def racine():
    return {"message": "Backend is running"}

@app.post("/analyze")
def analyser(requete: RequeteAnalyse):
    return analyser_depot_complet(requete.url_github)