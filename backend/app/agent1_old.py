import json, os, subprocess, tempfile
from pathlib import Path
from groq import Groq

client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

ALLOWED_FRAMEWORKS = {"Zephyr RTOS", "Arduino/PlatformIO", "ESP-IDF", "Mbed OS", "inconnu"}


def analyser_avec_ia_si_besoin(fichiers_trouves: set, resultat_simple: dict) -> dict:
    if resultat_simple["confiance"] == "haute":
        return resultat_simple

    prompt = f"""Tu es un expert en projets embarques (microcontroleurs).

Fichiers trouves dans le depot : {list(fichiers_trouves)}

REGLES STRICTES :
- Si tu vois un fichier .ino ou platformio.ini → Arduino/PlatformIO
- Si tu vois sdkconfig ou sdkconfig.defaults → ESP-IDF
- Si tu vois prj.conf → Zephyr RTOS
- Si tu vois mbed_app.json ou mbed-os.lib → Mbed OS
- Si AUCUN de ces fichiers n'est present → reponds "inconnu"
- NE DEVINE JAMAIS. Ne mentionne pas de fichiers qui n'existent pas.
- Ce n'est PAS un projet web. Ne propose jamais React, Ember, Vue, etc.

Reponds UNIQUEMENT en JSON avec ce format exact :
{{"framework": "...", "confiance": "moyenne", "raisonnement": "..."}}

"framework" doit etre EXCLUSIVEMENT l'une de ces 5 valeurs :
"Zephyr RTOS", "Arduino/PlatformIO", "ESP-IDF", "Mbed OS", "inconnu"
"""

    try:
        reponse = client_groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        resultat = json.loads(reponse.choices[0].message.content)

        # Validation post-Groq : forcer "inconnu" si le framework n'est pas autorisé
        if resultat.get("framework") not in ALLOWED_FRAMEWORKS:
            resultat = {
                "framework": "inconnu",
                "confiance": "basse",
                "raisonnement": "Le modele a propose un framework non autorise",
                "erreur_ia": f"Valeur rejetee : {resultat.get('framework')}"
            }

        return resultat

    except Exception as e:
        return {"framework": "inconnu", "confiance": "basse", "erreur_ia": str(e)}


def detecter_framework_simple(fichiers: set) -> dict:
    fichiers_lower = {f.lower() for f in fichiers}

    if any(f.endswith(".ino") for f in fichiers):
        return {"framework": "Arduino/PlatformIO", "confiance": "haute", "raisonnement": "Fichier .ino trouve"}

    if "platformio.ini" in fichiers_lower:
        return {"framework": "Arduino/PlatformIO", "confiance": "haute", "raisonnement": "platformio.ini trouve"}

    if "sdkconfig" in fichiers_lower or "sdkconfig.defaults" in fichiers_lower:
        return {"framework": "ESP-IDF", "confiance": "haute", "raisonnement": "sdkconfig trouve"}

    if "prj.conf" in fichiers_lower:
        return {"framework": "Zephyr RTOS", "confiance": "haute", "raisonnement": "prj.conf trouve"}

    if "mbed_app.json" in fichiers_lower or "mbed-os.lib" in fichiers_lower:
        return {"framework": "Mbed OS", "confiance": "haute", "raisonnement": "mbed_app.json trouve"}

    return {"framework": "inconnu", "confiance": "basse", "raisonnement": "Aucun fichier caracteristique detecte"}


def analyser_depot_complet(url_github: str) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_name = url_github.rstrip("/").split("/")[-1]
        clone_path = Path(tmpdir) / repo_name

        result = subprocess.run(
            ["git", "clone", "--depth", "1", url_github, str(clone_path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"framework": "inconnu", "confiance": "basse", "erreur": f"Echec du clone : {result.stderr}"}

        # Lister les fichiers en IGNORANT le dossier .git
        fichiers = set()
        for f in clone_path.rglob("*"):
            if f.is_file():
                rel_parts = f.relative_to(clone_path).parts
                if ".git" in rel_parts:
                    continue
                fichiers.add(f.name)

        resultat_simple = detecter_framework_simple(fichiers)

        if resultat_simple["confiance"] != "haute":
            return analyser_avec_ia_si_besoin(fichiers, resultat_simple)

        return resultat_simple