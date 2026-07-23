from git import Repo, GitCommandError
import tempfile, shutil, os

def cloner_depot(url_github: str) -> dict:
    dossier_temp = tempfile.mkdtemp()
    try:
        Repo.clone_from(url_github, dossier_temp, depth=1)
        return {"succes": True, "dossier": dossier_temp}
    except GitCommandError as e:
        shutil.rmtree(dossier_temp, ignore_errors=True)
        return {"succes": False, "erreur": str(e)}

def lister_tous_les_fichiers(dossier: str) -> set:
    fichiers_trouves = set()
    for racine, dossiers, fichiers in os.walk(dossier):
        if "deps" in racine or "modules" in racine or ".git" in racine:
            continue
        fichiers_trouves.update(fichiers)
    return fichiers_trouves

FINGERPRINTS = {
    "Zephyr RTOS": {"fichiers_requis": ["prj.conf"], "fichiers_bonus": ["CMakeLists.txt"]},
    "Arduino/PlatformIO": {"fichiers_requis": ["platformio.ini"], "fichiers_bonus": []},
    "ESP-IDF": {"fichiers_requis": ["sdkconfig"], "fichiers_bonus": ["CMakeLists.txt"]},
    "Mbed OS": {"fichiers_requis": ["mbed_app.json"], "fichiers_bonus": []},
}

def detecter_framework(fichiers_trouves: set) -> dict:
    resultats = {}
    for framework, regles in FINGERPRINTS.items():
        requis = [f for f in regles["fichiers_requis"] if f in fichiers_trouves]
        bonus = [f for f in regles["fichiers_bonus"] if f in fichiers_trouves]
        if requis:
            resultats[framework] = {"score": len(requis) * 2 + len(bonus), "fichiers_detectes": requis + bonus}
    if not resultats:
        return {"framework": "inconnu", "confiance": "basse"}
    meilleur = max(resultats, key=lambda f: resultats[f]["score"])
    return {"framework": meilleur, "confiance": "haute", "fichiers_detectes": resultats[meilleur]["fichiers_detectes"]}

def analyser_depot_complet(url_github: str) -> dict:
    clonage = cloner_depot(url_github)
    if not clonage["succes"]:
        return {"erreur": clonage["erreur"]}
    fichiers = lister_tous_les_fichiers(clonage["dossier"])
    return detecter_framework(fichiers)