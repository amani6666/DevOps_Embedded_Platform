from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def racine():
    return {"message": "Backend is running"}