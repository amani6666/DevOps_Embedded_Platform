import os
import glob
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb

# ── CONFIG ──────────────────────────────────────────────────────────
DOCS_DIR = "/app/docs_rag"   # Chemin DANS le conteneur Docker
DB_PATH = "/app/rag_db"       # Chemin DANS le conteneur Docker
MODEL_NAME = "all-MiniLM-L6-v2"

# ── INITIALISATION ─────────────────────────────────────────────────
print("🔧 Chargement du modele d'embeddings (1ere fois = telechargement ~80 Mo)...")
_embedder = SentenceTransformer(MODEL_NAME)
_chroma_client = chromadb.PersistentClient(path=DB_PATH)
_collection = _chroma_client.get_or_create_collection("docs_techniques")

_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n## ", "\n# ", "\n\n", "\n", " "]
)


# ═════════════════════════════════════════════════════════════════════
# FONCTION 1 : INDEXER TOUS LES DOCUMENTS
# ═════════════════════════════════════════════════════════════════════
def indexer_tous_les_documents():
    """
    Lit tous les fichiers .md dans docs_rag/, les decoupe en chunks,
    genere des embeddings, et les stocke dans ChromaDB.
    Appelee automatiquement au demarrage du backend.
    """
    fichiers_md = glob.glob(os.path.join(DOCS_DIR, "*.md"))
    if not fichiers_md:
        print(f"⚠️ Aucun fichier .md trouve dans {DOCS_DIR}")
        return

    print(f"📚 Indexation de {len(fichiers_md)} documents...")

    # Vider la collection existante pour eviter les doublons
    ids_existant = _collection.get()["ids"]
    if ids_existant:
        _collection.delete(ids=ids_existant)
        print(f"   🗑️ {len(ids_existant)} anciens chunks supprimes")

    for chemin in fichiers_md:
        nom = os.path.basename(chemin)
        with open(chemin, "r", encoding="utf-8") as f:
            texte = f.read()

        # Decouper en morceaux
        chunks = _text_splitter.split_text(texte)

        if not chunks:
            continue

        # Generer les embeddings (CPU, rapide)
        embeddings = _embedder.encode(chunks, show_progress_bar=False).tolist()

        # IDs uniques
        ids = [f"{nom}_{i}" for i in range(len(chunks))]

        # Metadonnees
        metadatas = [{"source": nom} for _ in chunks]

        # Ajouter a ChromaDB
        _collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )

        print(f"   ✅ {nom} -> {len(chunks)} chunks indexes")

    print(f"🎉 Indexation terminee. {_collection.count()} chunks dans la base.")


# ═════════════════════════════════════════════════════════════════════
# FONCTION 2 : RECHERCHER LES CHUNKS PERTINENTS
# ═════════════════════════════════════════════════════════════════════
def rechercher_documents(question: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """
    Transforme la question en embedding, cherche les n chunks les plus proches.
    Retourne une liste de dicts avec le texte, la source et la distance.
    """
    if _collection.count() == 0:
        return []

    embedding_question = _embedder.encode([question]).tolist()

    resultats = _collection.query(
        query_embeddings=embedding_question,
        n_results=n_results
    )

    chunks_trouves = []
    for i in range(len(resultats["documents"][0])):
        chunks_trouves.append({
            "texte": resultats["documents"][0][i],
            "source": resultats["metadatas"][0][i]["source"],
            "distance": resultats["distances"][0][i]
        })

    return chunks_trouves


# ═════════════════════════════════════════════════════════════════════
# FONCTION 3 : REPONDRE (MOCK - 0 token consomme)
# ═════════════════════════════════════════════════════════════════════
def repondre_question(question: str) -> Dict[str, Any]:
    """
    Version MOCK : recherche les chunks pertinents et retourne
    les extraits bruts. Aucun appel LLM = 0 token consomme.
    """
    chunks = rechercher_documents(question, n_results=3)

    if not chunks:
        return {
            "reponse": "Je n'ai trouve aucun document pertinent pour cette question.",
            "sources": [],
            "mode": "mock (pas de LLM - tokens epuises)"
        }

    extraits = "\n\n---\n\n".join([
        f"[Source: {c['source']}]\n{c['texte']}" for c in chunks
    ])

    return {
        "reponse": f"Question : '{question}'\n\nExtraits trouves :\n\n{extraits}",
        "sources": list(set(c["source"] for c in chunks)),
        "extraits": [{"source": c["source"], "distance": round(c["distance"], 4)} for c in chunks],
        "mode": "mock (pas de LLM - tokens epuises)"
    }


# ═════════════════════════════════════════════════════════════════════
# FONCTION 4 : REPONDRE AVEC LLM (Groq - activer quand tokens OK)
# ═════════════════════════════════════════════════════════════════════
def repondre_avec_llm(question: str) -> Dict[str, Any]:
    """
    Version COMPLETE : recherche + Groq LLM.
    A utiliser quand tes tokens Groq sont revenus.
    """
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    chunks = rechercher_documents(question, n_results=3)

    if not chunks:
        return {
            "reponse": "Aucun document trouve dans la base de connaissances.",
            "sources": [],
            "mode": "llm (Groq)"
        }

    extraits = "\n\n---\n\n".join([c["texte"] for c in chunks])
    sources = list(set(c["source"] for c in chunks))

    prompt = f"""Tu es un assistant technique expert en IoT et systemes embarques.
Tu reponds UNIQUEMENT a partir des extraits fournis ci-dessous.
Si la reponse n'est pas dans les extraits, dis-le clairement.

EXTRAITS :
{extraits}

QUESTION : {question}

Reponds de maniere concise, structuree et actionnable (avec les commandes exactes si pertinent)."""

    try:
        reponse = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024
        )
        contenu = reponse.choices[0].message.content

        return {
            "reponse": contenu,
            "sources": sources,
            "mode": "llm (Groq)"
        }
    except Exception as e:
        return {
            "reponse": f"Erreur LLM : {str(e)}",
            "sources": sources,
            "mode": "erreur"
        }