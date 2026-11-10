#!/usr/bin/env python3
"""
build_data.py — Prépare les données de la carte web (Metz + Nancy).

Arborescence attendue (à côté de index.html) :
    data/metz/sites.geojson    data/metz/zone.geojson    data/metz/eau.geojson (facultatif)
    data/nancy/sites.geojson   data/nancy/zone.geojson   data/nancy/eau.geojson (facultatif)
Écrit data/data.js, chargé par index.html.

- Les GeoJSON peuvent être en EPSG:4326 ou en Lambert 93 (converti automatiquement).
- Les noms de champs peuvent différer d'une couche à l'autre : voir ALIAS.
- priorite_v2 accepte « P1 », « 1 » ou « 1 - Très élevée ».
- Si le rang manque, il est recalculé (indice, sinon score, décroissant).

Usage (dans carte_web/) :  python build_data.py
"""
import json
import math
import re
from pathlib import Path

ICI = Path(__file__).resolve().parent
DATA = ICI / "data"
VILLES = ["metz", "nancy"]

# champ attendu -> noms acceptés dans la couche (le premier trouvé est utilisé)
ALIAS = {
    "rang": ["rang", "rang_aff", "rank"],
    "nom_etablissement": ["nom_etablissement", "nom_etab", "raison_sociale", "nom_usuel", "nom"],
    "nom_commune": ["nom_commune", "commune", "nom_com", "libelle_commune"],
    "priorite_v2": ["priorite_v2", "priorite", "prio_v2", "prio"],
    "score": ["score", "score_v2"],
    "S": ["S", "s", "note_source"],
    "T": ["T", "t", "note_transfert"],
    "C": ["C", "c", "note_cibles"],
    "statut_is": ["statut_is", "stat_instr", "statut_infosols"],
    "fiche_risque": ["fiche_risque", "url_fiche", "fiche"],
    "indice": ["indice", "indice_v2"],
}


# ---------------------------------------------------------------- géométrie
def l93_vers_wgs84(x, y):
    """Lambert 93 (EPSG:2154) -> lon/lat WGS84. Formule IGN (ALG0004), RGF93 ≈ WGS84."""
    n, C = 0.7256077650532670, 11754255.426096
    xs, ys, e = 700000.0, 12655612.049876, 0.08181919112823
    R = math.hypot(x - xs, y - ys)
    gamma = math.atan((x - xs) / (ys - y))
    lon = math.radians(3) + gamma / n
    L = -math.log(abs(R / C)) / n
    phi = 2 * math.atan(math.exp(L)) - math.pi / 2
    for _ in range(10):
        es = e * math.sin(phi)
        phi = 2 * math.atan(((1 + es) / (1 - es)) ** (e / 2) * math.exp(L)) - math.pi / 2
    return [math.degrees(lon), math.degrees(phi)]


def reprojeter(obj):
    if isinstance(obj, list) and len(obj) >= 2 and all(isinstance(v, (int, float)) for v in obj[:2]):
        return l93_vers_wgs84(obj[0], obj[1])
    if isinstance(obj, list):
        return [reprojeter(x) for x in obj]
    return obj


def premier_couple(obj):
    while isinstance(obj, list) and obj and isinstance(obj[0], list):
        obj = obj[0]
    return obj


def arrondir(obj, n=5):
    if isinstance(obj, float):
        return round(obj, n)
    if isinstance(obj, list):
        return [arrondir(x, n) for x in obj]
    return obj


# ---------------------------------------------------------------- attributs
def prio_normale(v):
    """'P1', 1, '1', '1 - Très élevée' -> 'P1'."""
    if v is None:
        return None
    m = re.search(r"([1-4])", str(v))
    return f"P{m.group(1)}" if m else None


def lire(ville, nom, sites=False, obligatoire=True):
    chemin = DATA / ville / nom
    if not chemin.exists():
        if obligatoire:
            raise SystemExit(f"Fichier manquant : {chemin}")
        print(f"  (absent, ignoré) {ville}/{nom}")
        return None
    gj = json.loads(chemin.read_text(encoding="utf-8"))
    feats = gj.get("features", [])

    l93 = False
    for f in feats:
        g = f.get("geometry")
        if g:
            c = premier_couple(g["coordinates"])
            l93 = bool(c) and abs(c[0]) > 180
            break
    if l93:
        print(f"  {ville}/{nom} : Lambert 93 détecté -> converti en WGS84")
    for f in feats:
        if f.get("geometry"):
            coords = f["geometry"]["coordinates"]
            f["geometry"]["coordinates"] = arrondir(reprojeter(coords) if l93 else coords)

    if sites:
        dispo = set()
        for f in feats:
            dispo.update((f.get("properties") or {}).keys())
        choix = {cle: next((a for a in noms if a in dispo), None) for cle, noms in ALIAS.items()}
        manquants = [c for c, v in choix.items() if v is None and c not in ("indice", "rang")]
        if manquants:
            print(f"  ATTENTION {ville} : champs introuvables -> {', '.join(manquants)}")
            print(f"    champs présents : {', '.join(sorted(dispo))}")
        for f in feats:
            p = f.get("properties") or {}
            f["properties"] = {cle: (p.get(src) if src else None) for cle, src in choix.items()}
            f["properties"]["priorite_v2"] = prio_normale(f["properties"]["priorite_v2"])
        if choix["rang"] is None:
            cle = "indice" if choix["indice"] else "score"
            ordre = sorted(feats, key=lambda f: -(float(f["properties"].get(cle) or 0)))
            for i, f in enumerate(ordre, 1):
                f["properties"]["rang"] = i
            print(f"  {ville} : rang absent -> recalculé par {cle} décroissant")
        for f in feats:
            f["properties"].pop("indice", None)
        compte = {}
        for f in feats:
            k = f["properties"]["priorite_v2"]
            compte[k] = compte.get(k, 0) + 1
        print(f"  {ville} : " + " · ".join(f"{k} {compte.get(k, 0)}" for k in ["P1", "P2", "P3", "P4"])
              + (f" · sans priorité {compte[None]}" if None in compte else ""))
    else:
        for f in feats:
            f["properties"] = {}

    gj.pop("crs", None)
    print(f"  {ville}/{nom} : {len(feats)} entités")
    return gj


def main():
    donnees = {}
    for v in VILLES:
        if not (DATA / v).exists():
            print(f"(dossier data/{v}/ absent, {v} ignorée)")
            continue
        print(f"--- {v}")
        donnees[v] = {
            "sites": lire(v, "sites.geojson", sites=True),
            "zone": lire(v, "zone.geojson"),
            "eau": lire(v, "eau.geojson", obligatoire=False),
        }
    if not donnees:
        raise SystemExit("Aucune donnée : créez data/metz/ et/ou data/nancy/.")
    js = "window.SSP_DATA = " + json.dumps(donnees, ensure_ascii=False, separators=(",", ":")) + ";\n"
    sortie = DATA / "data.js"
    sortie.write_text(js, encoding="utf-8")
    print(f"Écrit : {sortie} ({sortie.stat().st_size / 1024:.0f} Ko)")


if __name__ == "__main__":
    main()
