import json, os, subprocess, tempfile, re
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime
from groq import Groq

client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.1-8b-instant"
ALLOWED_FRAMEWORKS = {"Zephyr RTOS", "Arduino/PlatformIO", "ESP-IDF", "Mbed OS", "inconnu"}

FINGERPRINTS = {
    "Zephyr RTOS": {"fichiers_requis": ["prj.conf"], "fichiers_bonus": ["CMakeLists.txt", "Kconfig", "west.yml"]},
    "Arduino/PlatformIO": {"fichiers_requis": ["platformio.ini"], "fichiers_bonus": [".ino"]},
    "ESP-IDF": {"fichiers_requis": ["sdkconfig"], "fichiers_bonus": ["CMakeLists.txt", "sdkconfig.defaults"]},
    "Mbed OS": {"fichiers_requis": ["mbed_app.json"], "fichiers_bonus": ["mbed-os.lib"]},
}


class Agent1:
    def __init__(self):
        self.memoire: List[Dict[str, Any]] = []
        self.etat: Dict[str, Any] = {}

    def _log(self, etape: str, detail: str, data: Any = None):
        entry = {"etape": etape, "detail": detail, "horodatage": datetime.now().isoformat()}
        if data is not None:
            entry["data"] = data
        self.memoire.append(entry)

    def outil_cloner(self, url_github: str) -> Path:
        self._log("PERCEVOIR", f"Clonage de {url_github}")
        tmpdir = tempfile.mkdtemp()
        repo_name = url_github.rstrip("/").split("/")[-1]
        clone_path = Path(tmpdir) / repo_name
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url_github, str(clone_path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Echec du clone : {result.stderr}")
        self._log("PERCEVOIR", "Clone reussi", str(clone_path))
        return clone_path

    def outil_scanner(self, chemin: Path) -> Dict[str, Any]:
        self._log("PERCEVOIR", "Scan de la structure")
        fichiers: Set[str] = set()
        extensions: Dict[str, int] = {}
        arborescence: List[str] = []
        for f in chemin.rglob("*"):
            rel = f.relative_to(chemin)
            rel_parts = rel.parts
            if ".git" in rel_parts or "node_modules" in rel_parts or "venv" in rel_parts or "__pycache__" in rel_parts:
                continue
            if f.is_file():
                fichiers.add(f.name)
                ext = f.suffix.lower()
                extensions[ext] = extensions.get(ext, 0) + 1
                arborescence.append(str(rel))
        langage_dominant = max(extensions, key=extensions.get) if extensions else "aucun"
        resultat = {
            "fichiers": list(fichiers),
            "extensions": extensions,
            "langage_dominant": langage_dominant,
            "arborescence": arborescence[:50],
            "nb_fichiers": len(fichiers)
        }
        self._log("PERCEVOIR", f"{len(fichiers)} fichiers trouves, langage: {langage_dominant}")
        return resultat

    def outil_detecter_framework(self, scan: Dict) -> Dict[str, Any]:
        self._log("PENSER", "Hypothese initiale par regles (fingerprints)")
        fichiers_set = {f.lower() for f in scan["fichiers"]}
        resultats = {}
        for framework, regles in FINGERPRINTS.items():
            requis = regles["fichiers_requis"]
            bonus = regles["fichiers_bonus"]
            requis_presents = [f for f in requis if f.lower() in fichiers_set]
            bonus_presents = []
            for b in bonus:
                if b.startswith("."):
                    if any(f.lower().endswith(b.lower()) for f in scan["fichiers"]):
                        bonus_presents.append(b)
                else:
                    if b.lower() in fichiers_set:
                        bonus_presents.append(b)
            if requis_presents:
                resultats[framework] = {
                    "score": len(requis_presents) * 2 + len(bonus_presents),
                    "fichiers_detectes": requis_presents + bonus_presents
                }
        if not resultats:
            if scan["langage_dominant"] in {".c", ".h", ".cpp"}:
                return {"framework": "inconnu", "confiance": "basse", "source": "regle", "fichiers_detectes": [], "note": "C/C++ detecte mais sans signature framework"}
            return {"framework": "inconnu", "confiance": "basse", "source": "regle", "fichiers_detectes": []}
        meilleur = max(resultats, key=lambda f: resultats[f]["score"])
        return {"framework": meilleur, "confiance": "haute", "source": "regle", "fichiers_detectes": resultats[meilleur]["fichiers_detectes"]}

    def outil_extraire_zephyr(self, chemin: Path) -> Dict[str, Any]:
        self._log("AGIR", "Extraction des protocoles Zephyr")
        resultat = {"prj_conf_trouve": False, "protocoles": [], "validations": [], "carte_cible": "unknown"}
        for prj in chemin.rglob("prj.conf"):
            resultat["prj_conf_trouve"] = True
            try:
                with open(prj, "r", errors="ignore") as f:
                    contenu = f.read()
                if len(contenu.strip()) == 0:
                    resultat["validations"].append({"fichier": str(prj), "statut": "vide"})
                    continue
                protocoles = []
                if "CONFIG_MQTT" in contenu:
                    protocoles.append("MQTT")
                if "CONFIG_WIFI" in contenu or "CONFIG_NET_L2_WIFI" in contenu:
                    protocoles.append("WiFi")
                if "CONFIG_BT" in contenu or "CONFIG_BLUETOOTH" in contenu:
                    protocoles.append("Bluetooth")
                if "CONFIG_CAN" in contenu:
                    protocoles.append("CAN")
                if "CONFIG_I2C" in contenu:
                    protocoles.append("I2C")
                if "CONFIG_SPI" in contenu:
                    protocoles.append("SPI")
                if "CONFIG_UART" in contenu:
                    protocoles.append("UART")
                carte = "unknown"
                for ligne in contenu.splitlines():
                    if ligne.startswith("CONFIG_BOARD="):
                        carte = ligne.split("=")[1].strip().strip('"')
                        break
                resultat["protocoles"].extend(protocoles)
                resultat["carte_cible"] = carte
                resultat["validations"].append({"fichier": str(prj), "statut": "valide", "protocoles_detectes": protocoles})
                self._log("AGIR", f"Protocoles Zephyr: {protocoles}, carte: {carte}", str(prj))
            except Exception as e:
                resultat["validations"].append({"fichier": str(prj), "statut": "erreur", "detail": str(e)})
        return resultat

    def outil_extraire_platformio(self, chemin: Path) -> Dict[str, Any]:
        self._log("AGIR", "Extraction librairies PlatformIO")
        resultat = {"ini_trouve": False, "libs": [], "board": "unknown", "protocoles": []}
        for ini in chemin.rglob("platformio.ini"):
            resultat["ini_trouve"] = True
            try:
                with open(ini, "r", errors="ignore") as f:
                    contenu = f.read()
                libs = re.findall(r'lib_deps\s*=\s*(.+)', contenu)
                resultat["libs"] = [l.strip() for l in libs]
                board_match = re.search(r'board\s*=\s*(\S+)', contenu)
                if board_match:
                    resultat["board"] = board_match.group(1)
                libs_str = " ".join(resultat["libs"]).lower()
                if "wifi" in libs_str or "esp8266" in libs_str:
                    resultat["protocoles"].append("WiFi")
                if "mqtt" in libs_str:
                    resultat["protocoles"].append("MQTT")
                if "bluetooth" in libs_str or "ble" in libs_str:
                    resultat["protocoles"].append("Bluetooth")
                self._log("AGIR", f"Board: {resultat['board']}, Libs: {resultat['libs']}")
            except Exception as e:
                resultat["erreur"] = str(e)
        return resultat

    def outil_extraire_espidf(self, chemin: Path) -> Dict[str, Any]:
        self._log("AGIR", "Extraction config ESP-IDF")
        resultat = {"sdkconfig_trouve": False, "options_cles": [], "protocoles": [], "carte_cible": "esp32"}
        for cfg in chemin.rglob("sdkconfig"):
            resultat["sdkconfig_trouve"] = True
            try:
                with open(cfg, "r", errors="ignore") as f:
                    contenu = f.read()
                lignes = [l.strip() for l in contenu.splitlines() if l.startswith("CONFIG_")]
                resultat["options_cles"] = lignes[:20]
                if "CONFIG_BT_ENABLED" in contenu:
                    resultat["protocoles"].append("Bluetooth")
                if "CONFIG_WIFI_ENABLED" in contenu or "CONFIG_ESP_WIFI" in contenu:
                    resultat["protocoles"].append("WiFi")
                if "CONFIG_MQTT" in contenu:
                    resultat["protocoles"].append("MQTT")
                self._log("AGIR", f"Options ESP-IDF extraites: {len(resultat['options_cles'])}")
            except Exception as e:
                resultat["erreur"] = str(e)
        return resultat

    def outil_verifier(self, hypothese: Dict, preuves: Dict) -> Dict[str, Any]:
        self._log("VERIFIER", "Validation de coherence")
        fw = hypothese["framework"]
        problemes = []
        if fw == "Zephyr RTOS" and not preuves.get("zephyr", {}).get("prj_conf_trouve"):
            problemes.append("Zephyr annonce mais prj.conf absent ou vide")
        if fw == "Arduino/PlatformIO" and not preuves.get("platformio", {}).get("ini_trouve"):
            if not any(f.endswith(".ino") for f in preuves["scan"]["fichiers"]):
                problemes.append("Arduino annonce mais ni .ini ni .ino trouve")
        if fw == "ESP-IDF" and not preuves.get("espidf", {}).get("sdkconfig_trouve"):
            problemes.append("ESP-IDF annonce mais sdkconfig absent")
        statut = "invalide" if problemes else "valide"
        self._log("VERIFIER", f"Statut: {statut}", problemes)
        return {"statut": statut, "problemes": problemes}

    def outil_raisonner(self, contexte: Dict) -> Dict[str, Any]:
        self._log("REFLECHIR", "Appel LLM Groq pour raisonnement agentic")
        prompt = f"""Tu es un agent expert en analyse de projets embarques (microcontroleurs).

CONTEXTE DE L'AGENT :
- Fichiers trouves : {contexte['scan']['fichiers'][:30]}
- Langage dominant : {contexte['scan']['langage_dominant']}
- Hypothese initiale : {contexte['hypothese']}
- Problemes de validation : {contexte['validation']['problemes']}

INSTRUCTIONS :
1. Analyse les fichiers les plus informatifs
2. Identifie le framework EXCLUSIVEMENT parmi : Zephyr RTOS, Arduino/PlatformIO, ESP-IDF, Mbed OS, inconnu
3. Si tu ne sais pas, dis "inconnu" - ne devine jamais
4. Explique ton raisonnement etape par etape

Reponds UNIQUEMENT en JSON :
{{"chain_of_thought": "etape 1: ... etape 2: ... etape 3: ...", "framework": "...", "confiance": "moyenne", "raisonnement": "resume final"}}"""
        try:
            reponse = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            resultat = json.loads(reponse.choices[0].message.content)
            if resultat.get("framework") not in ALLOWED_FRAMEWORKS:
                resultat = {"framework": "inconnu", "confiance": "basse", "raisonnement": "LLM propose un framework non autorise", "chain_of_thought": resultat.get("chain_of_thought", "")}
            self._log("REFLECHIR", f"Conclusion LLM: {resultat['framework']}")
            return resultat
        except Exception as e:
            self._log("REFLECHIR", f"Erreur LLM: {str(e)}")
            return {"framework": "inconnu", "confiance": "basse", "raisonnement": f"Erreur IA: {str(e)}"}

    def analyser(self, url_github: str) -> Dict[str, Any]:
        self._log("DEMARRER", f"Analyse agentic de {url_github}")
        try:
            clone_path = self.outil_cloner(url_github)
            scan = self.outil_scanner(clone_path)
            hypothese = self.outil_detecter_framework(scan)
            preuves = {"scan": scan}
            carte_cible = "unknown"
            protocoles = []
            if hypothese["framework"] == "Zephyr RTOS":
                z = self.outil_extraire_zephyr(clone_path)
                preuves["zephyr"] = z
                protocoles = z.get("protocoles", [])
                carte_cible = z.get("carte_cible", "unknown")
            elif hypothese["framework"] == "Arduino/PlatformIO":
                p = self.outil_extraire_platformio(clone_path)
                preuves["platformio"] = p
                protocoles = p.get("protocoles", [])
                carte_cible = p.get("board", "unknown")
            elif hypothese["framework"] == "ESP-IDF":
                e = self.outil_extraire_espidf(clone_path)
                preuves["espidf"] = e
                protocoles = e.get("protocoles", [])
                carte_cible = e.get("carte_cible", "esp32")
            validation = self.outil_verifier(hypothese, preuves)
            if validation["statut"] != "valide" or hypothese["confiance"] == "basse":
                hypothese_llm = self.outil_raisonner({"scan": scan, "hypothese": hypothese, "validation": validation, "preuves": preuves})
                hypothese["framework"] = hypothese_llm.get("framework", hypothese["framework"])
                hypothese["confiance"] = hypothese_llm.get("confiance", "moyenne")
                hypothese["raisonnement"] = hypothese_llm.get("raisonnement", "")
                hypothese["chain_of_thought"] = hypothese_llm.get("chain_of_thought", "")
                validation = self.outil_verifier(hypothese, preuves)
            rapport = {
                "framework": hypothese["framework"],
                "fichiers_detectes": hypothese.get("fichiers_detectes", []),
                "carte_cible": carte_cible,
                "protocoles": list(set(protocoles)),
                "confiance": hypothese["confiance"],
                "raisonnement": hypothese.get("raisonnement", self._construire_raisonnement()),
                "validation": validation,
                "memoire_agent": self.memoire,
                "metadonnees": preuves,
            }
            if "chain_of_thought" in hypothese:
                rapport["chain_of_thought"] = hypothese["chain_of_thought"]
            self._log("DECIDER", f"Rapport final: {hypothese['framework']}")
            return rapport
        except Exception as e:
            return {"framework": "inconnu", "fichiers_detectes": [], "carte_cible": "unknown", "protocoles": [], "confiance": "basse", "erreur": str(e), "memoire_agent": self.memoire}

    def _construire_raisonnement(self) -> str:
        return " -> ".join([m["etape"] for m in self.memoire])


def analyser_depot_complet(url_github: str) -> dict:
    agent = Agent1()
    return agent.analyser(url_github)