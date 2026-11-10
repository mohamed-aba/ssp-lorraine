# Sites et sols pollués en Lorraine — hiérarchisation multicritère

Carte interactive : **[https://mohamed-aba.github.io/ssp-lorraine/](https://mohamed-aba.github.io/ssp-lorraine/)**

Hiérarchisation de **2 444 sites potentiellement pollués** sur deux métropoles lorraines
(Metz Métropole : 759 sites · Métropole du Grand Nancy : 1 685 sites), à partir de données publiques.

## Méthode
Chaque site reçoit une note de 1 à 3 pour trois facteurs, selon la logique source – transfert – cible :

| Facteur | Ce qu'il mesure | Données |
|---|---|---|
| **S**ource | potentiel polluant de l'activité, pollution instruite | CASIAS, InfoSols, SIS (Géorisques) |
| **T**ransfert | perméabilité du sous-sol, distance à l'eau de surface | BD Charm-50 (BRGM), BD TOPO (IGN) |
| **C**ibles | établissements sensibles < 100 m, logements dans 300 m | OpenStreetMap, BD TOPO, INSEE |

**Score = S × T × C** (1 à 27), puis 4 classes de priorité :
P1 = 27 et pollution active · P2 = 27 sans pollution active, ou 18 avec pollution active · P3 = 18 sans pollution active · P4 ≤ 12.

## Résultats
| | Metz Métropole | Grand Nancy |
|---|---|---|
| Sites analysés | 759 | 1 685 |
| P1 (priorité très élevée) | 14 (1,8 %) | 35 (2,1 %) |
| P1 + P2 | 28,7 % | 23,6 % |

## Outils
- **QGIS 3.44** : traitements et cartographie
- **Python** : téléchargement CASIAS par l'API Géorisques, géocodage BAN
- **Leaflet** : carte web (fonds IGN Géoplateforme)

## Contenu du dépôt
- `index.html` : page web (carte, résultats, méthode)
- `data/data.js` : données des sites (généré par `build_data.py`)
- `build_data.py` : conversion des exports QGIS (GeoJSON) vers la carte web

## Limites
Les résultats sont une aide à la priorisation, pas un diagnostic de sol :
localisation parfois approximative (adresse), activités déduites du nom de l'établissement,
ressource en eau (captages) non comptée comme cible.

---
Réalisation : Mohamed ABA — novembre 2026
