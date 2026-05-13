"""
BTP AI — Base de Connaissances DTU / Normes BTP
================================================
Contenu structuré couvrant les principaux DTU, normes NF/EN/ISO,
réglementation et guides CSTB utilisés dans la construction française.

Ce module génère des chunks de connaissance métier prêts à être
vectorisés et indexés dans FAISS au démarrage du système.
"""

from typing import List, Dict, Any
from datetime import datetime

# ── Constantes ───────────────────────────────────────────
SOURCE_SYSTEM = "[BASE DTU]"
PROJECT_SYSTEM = "Base Connaissances BTP"
AUTEUR_SYSTEM  = "Système BTP AI"
CRITICITE_DEFAULT = "Élevée"

# ── Helpers ──────────────────────────────────────────────

def _entry(ref: str, titre: str, lot: str, criticite: str, contenu: str) -> Dict[str, Any]:
    """Créer un chunk de connaissance normalisé."""
    return {
        "text": f"[{ref}] {titre}\n\n{contenu.strip()}",
        "metadata": {
            "source":      f"{SOURCE_SYSTEM} {ref}",
            "project":     PROJECT_SYSTEM,
            "lot":         lot,
            "auteur":      AUTEUR_SYSTEM,
            "criticite":   criticite,
            "file_type":   "knowledge",
            "reference":   ref,
            "titre":       titre,
            "ingested_at": datetime.utcnow().isoformat(),
            "total_chunks": 1,
            "chunk_index": 0,
            "is_builtin":  True,
        }
    }


# ════════════════════════════════════════════════════════════
# DTU — GROS ŒUVRE
# ════════════════════════════════════════════════════════════

DTU_GROS_OEUVRE = [

    _entry("DTU 13.1", "Travaux de fondations superficielles",
           "GO - Fondations", "Critique",
           """
Champ d'application : fondations superficielles (semelles, radiers) pour bâtiments courants.

Études de sol préalables :
- Étude géotechnique obligatoire (mission G2 minimum selon NF P 94-500)
- Reconnaissance des sols par sondages ou essais pénétrométriques
- Détermination de la contrainte admissible du sol (qadm)
- Vérification de l'absence de remblais, cavités, nappes phréatiques agressives

Semelles isolées et filantes :
- Profondeur minimale hors gel : 0,80 m en zone H1 (montagne), 0,60 m en zone H2, 0,50 m en zone H3
- Débord minimal des semelles par rapport au poteau/mur : D ≥ h (hauteur de la semelle)
- Rapport longueur/largeur semelle filante ≥ 2
- Armatures longitudinales et transversales selon calcul béton armé (EC2)
- Enrobage minimal des armatures : 3 cm (en contact sol non agressif), 4 cm (sol agressif)

Radiers :
- Épaisseur minimale : 20 cm (radier simple), 25 cm (radier nervuré)
- Joints de dilatation obligatoires tous les 20 à 30 m
- Film polyane 200 µm entre le béton propre et le radier
- Béton de propreté : 5 cm d'épaisseur minimum, dosage 150 kg/m³

Béton de fondation :
- Classe minimale : C25/30 (XC2 selon EN 206)
- Classe d'exposition selon agressivité du sol et de l'eau
- Affaissement au cône : S3 recommandé pour bonne mise en œuvre
- Délai de décoffrage : 16h minimum à 20°C, augmenté si températures basses

Contrôles et réceptions :
- Vérification du fond de fouille avant coulage (portance, propreté)
- Contrôle des cotes de nivellement
- Essais de compression béton : 1 éprouvette par 25 m³ minimum
"""),

    _entry("DTU 13.2", "Travaux de fondations profondes",
           "GO - Fondations", "Critique",
           """
Champ d'application : pieux, micropieux, barrettes pour ouvrages nécessitant un ancrage profond.

Types de fondations profondes :
- Pieux forés simples : diamètre 300 à 1500 mm
- Pieux forés tubés (terrain instable ou présence d'eau)
- Pieux battus béton préfabriqué ou acier
- Micropieux (diamètre < 300 mm) : charges axiales jusqu'à 1 500 kN
- Pieux vissés moulés (CMC, VMV)

Règles de dimensionnement :
- Portance par frottement latéral et résistance en pointe selon NF P 94-262
- Coefficient de sécurité global : Fs ≥ 2 sur la charge ultime
- Charges horizontales : vérification par méthode p-y
- Tassement admissible : ≤ 25 mm pour ouvrages courants

Matériaux :
- Béton : C25/30 minimum, C30/37 pour pieux en milieu agressif
- Armatures : acier HA FeE500, cage sur toute la hauteur du pieu si sollicitation de traction
- Enrobage : 5 cm minimum, 7 cm en milieu agressif ou en présence d'eau

Essais de contrôle :
- Essai de chargement statique (1% des pieux, minimum 2) selon NF P 94-150
- Essai dynamique STATNAMIC ou PDA autorisé en complément
- Contrôle d'intégrité (sondage sonique) : 100% des pieux forés de grand diamètre

Espacement minimal entre pieux : 3 fois le diamètre (centre à centre).
"""),

    _entry("DTU 20.1", "Maçonnerie de petits éléments — Murs en blocs",
           "GO - Maçonnerie", "Élevée",
           """
Champ d'application : murs en briques, blocs béton, blocs de béton cellulaire (AAC).

Matériaux et caractéristiques :
- Briques terre cuite : résistance minimale fb ≥ 5 MPa (parois portantes), 2 MPa (cloisons)
- Blocs béton plein : fb ≥ 8 MPa; blocs creux : fb ≥ 4 MPa
- Béton cellulaire (AAC) : densité 400 à 700 kg/m³, fb ≥ 2,5 MPa
- Mortier de pose : classe M5 minimum pour murs porteurs (dosage ≥ 250 kg/m³ ciment)
- Mortier-colle pour blocs AAC : joint mince 1 à 3 mm

Dimensionnement des murs porteurs :
- Élancement maximal : h/e ≤ 27 (mur chaîné), h/e ≤ 20 (mur non chaîné)
- Portée libre maximale entre chaînages : 6 m en longueur, 3 m en hauteur
- Charge verticale admissible : selon NF EN 1996-1-1 (Eurocode 6)
- Chaînages horizontaux : tous les niveaux, armatures 4HA8 minimum
- Chaînages verticaux : encadrements d'ouvertures, angles, refends tous les 6 m

Murs de façade (non porteurs) :
- Épaisseur minimale avec isolation intégrée : 30 cm (selon zone climatique)
- Pont thermique à traiter en linteau, tableau, appui de baie
- Drainage indispensable en présence de mur double avec lame d'air

Tolérances d'exécution :
- Planéité : ±5 mm sous règle de 2 m
- Verticalité : ±10 mm sur hauteur d'étage
- Niveau des assises : ±5 mm
"""),

    _entry("DTU 21", "Béton armé — Exécution des travaux",
           "GO - Structure béton", "Critique",
           """
Champ d'application : exécution des ouvrages en béton armé coulé en place.

Béton — Formulation et classes :
- Classe minimale selon usage : C20/25 (dalle sur sol), C25/30 (poteaux, poutres), C30/37 (environnement agressif)
- Classes d'exposition XC0 à XS3 selon NF EN 206
- Rapport eau/ciment maximal : 0,55 (XC1), 0,50 (XC3/XC4), 0,45 (XS/XD)
- Dosage minimal en ciment : 260 kg/m³ (XC1), 300 kg/m³ (XC3), 340 kg/m³ (XS)
- Granulats : Dmax ≤ espacement libre armatures / 1,3 et ≤ 31,5 mm

Armatures (NF EN 10080) :
- Acier B500B ou B500C (ductilité améliorée pour zones sismiques)
- Enrobage nominal : 25 mm (XC1), 30 mm (XC2/XC3), 35 mm (XC4), 40 mm (XD/XS)
- Recouvrement minimal : 40 × diamètre barre (zone courante)
- Espacement minimal barres : max(Dmax + 5 mm ; 20 mm ; 1,2 × diamètre)
- Ligatures : toutes les intersections pour les zones de nœuds de cadres

Coffrage :
- Résistance aux pressions de coulage (hauteur libre, vitesse de bétonnage)
- Étanchéité pour éviter pertes de laitance
- Huile de décoffrage : appliquer avant ferraillage
- Délai décoffrage : 16h à 20°C (voiles), 14 jours (poutres sans étais), 21 jours (dalles)

Mise en œuvre du béton :
- Hauteur de chute libre maximale : 1,50 m (éviter ségrégation)
- Compactage par vibration interne : aiguille vibrante tous les 50 cm
- Durée vibration : 5 à 15 secondes par point jusqu'à disparition bulles
- Reprise de bétonnage : traitement joint (grenaillage, humidification, couche de pontage)

Cure et protection :
- Commencer la cure immédiatement après décoffrage ou finition
- Durée minimale : 3 jours (CEM I, T>15°C), 7 jours (CEM III/IV ou T<10°C)
- Méthodes : bâches humides, produits de cure, aspersion d'eau

Contrôles obligatoires :
- Contrôle intérieur production béton (prélèvements éprouvettes)
- Contrôle extérieur : 1 prélèvement / 100 m³ minimum
- Résistance à 28 jours : 85% des éprouvettes ≥ fck spécifiée
"""),

    _entry("DTU 22.1", "Murs extérieurs en panneaux préfabriqués",
           "GO - Structure béton", "Normale",
           """
Champ d'application : façades en panneaux béton préfabriqués porteurs ou non porteurs.

Conception des panneaux :
- Épaisseur minimale : 14 cm (panneau sandwich), 18 cm (panneau plein porteur)
- Armatures de peau : treillis soudé HA8 maille 15×15 cm minimum
- Armatures de levage : calcul selon poids panneau × coefficient dynamique 2,0
- Ancrages : 4 points minimum, vérification à l'arrachement et au cisaillement

Isolation thermique intégrée (sandwich) :
- PSE, XPS ou PIR entre les deux peaux de béton
- Connecteurs inox ou composite (pas d'acier traversant = pont thermique)
- Up ≤ 0,30 W/(m².K) selon RE 2020

Joints entre panneaux :
- Joint ouvert drainé (type feuillure) ou joint collé (mastic élastomère)
- Largeur minimale joint : 15 mm pour absorption des dilatations thermiques
- Mastic : classe F25 minimum (ISO 11600), durée de vie ≥ 25 ans
- Joint PE fond de joint obligatoire avant application mastic

Tolérances de fabrication : ±3 mm sur dimensions, ±2 mm planéité.
Tolérances de pose : ±10 mm position, ±5 mm verticalité, ±3 mm joint.
"""),

    _entry("DTU 23.1", "Murs en béton banché",
           "GO - Structure béton", "Élevée",
           """
Champ d'application : murs coulés entre coffrages (banches métalliques ou bois).

Épaisseur des murs :
- Mur de soubassement : 20 cm minimum
- Mur porteur courant : 18 à 25 cm selon hauteur et charges
- Voile de refend : 16 cm minimum

Formulation béton pour banchage :
- Affaissement S4 (18-22 cm) recommandé pour bonne coulabilité
- Granulats : Dmax ≤ 20 mm pour passage entre armatures
- Adjuvant plastifiant si nécessaire (pas de sur-dosage en eau)

Pression sur les banches :
- Pression latérale = ρ × g × H (colonne liquide)
- Vitesse de bétonnage maximale : calculée selon résistance banches
- Hauteur de couche : ≤ 50 cm pour vibration efficace

Ouvertures et réservations :
- Boîtes de réservation : fixées solidement, vérifiées avant coulage
- Ferraillage de renfort encadrant chaque ouverture

Décoffrage et finition :
- Décoffrage 16 à 24h après coulage (températures normales)
- Ragréage des épaufrures et nids de graviers
- Bouchonnage des trous de tirant avec mortier dosé à 450 kg/m³
"""),

]

# ════════════════════════════════════════════════════════════
# DTU — ÉTANCHÉITÉ / COUVERTURE
# ════════════════════════════════════════════════════════════

DTU_ETANCHEITE = [

    _entry("DTU 43.1", "Étanchéité des toitures-terrasses — Toits plats",
           "SO - Étanchéité", "Critique",
           """
Champ d'application : étanchéité de toitures-terrasses inaccessibles, techniques, accessibles piétons ou véhicules.

Classification des toitures-terrasses :
- Inaccessible (sauf entretien) : pente 1 à 5%
- Technique (accès équipements) : pente 1 à 3%
- Accessible piétons : protection lourde obligatoire
- Accessible véhicules : dalle béton sur plots + étanchéité renforcée
- Toiture végétalisée : système complet drainage + substrat + végétaux

Pentes minimales :
- Asphalte coulé : 0% accepté
- Multicouches bitumineux : 1% minimum
- Monocouche synthétique (TPO, EPDM, PVC) : 1% minimum
- Zinc/plomb (DTU 40.41) : 5% minimum

Support d'étanchéité :
- Maçonnerie : planéité 5 mm sous règle de 2 m, siccité > 90%
- Bac acier : fixations tous les nervures, joints agrafés
- Isolation thermique en toiture inversée : XPS λ ≤ 0,035 W/(m.K)

Relevés d'étanchéité :
- Hauteur minimale : 15 cm au-dessus de la protection finie
- 20 cm en zone très exposée au vent (bord de mer, altitude)
- Fixation mécanique du relevé en tête + solin ou profilé métallique
- Protection du relevé obligatoire (enduit, aluminium, etc.)

Évacuations pluviales :
- 2 dispositifs minimum par toiture (sécurité + principal)
- Calcul débit selon surface et pluviométrie locale (Météo France)
- Entonnoirs de drainage avec garde étanche (relevé ≥ 0 cm toléré)

Isolation thermique (RE 2020) :
- R ≥ 6,0 m².K/W pour toiture (zones H1a, H1b, H1c)
- R ≥ 5,5 m².K/W pour zones H2 et H3
- Pare-vapeur obligatoire côté chaud (sd ≥ 1500 m)

Contrôle d'étanchéité :
- Essai à l'eau 24h minimum avant pose protection
- Seuil d'humidité du support vérifié (humidimètre)
- Contrôle des soudures (sonde de détection sur géomembrane)
"""),

    _entry("DTU 40.35", "Couverture en tuiles en terre cuite",
           "SO - Étanchéité", "Élevée",
           """
Champ d'application : couvertures en tuiles canal, romanes, mécaniques, grand moule.

Pentes minimales selon type de tuile et zone de vent :
- Tuile mécanique petite surface (16 tuiles/m²) : 25% minimum (zone courante)
- Tuile grand moule (10 tuiles/m²) : 20% minimum
- Tuile canal : 30% minimum (35% en zones exposées)
- Tuile romane : 35% minimum

Règles de pose :
- Pureau (partie visible) : selon fabricant, en respectant recouvrement minimal
- Recouvrement minimal : 8 cm (pente 45°), 12 cm (pente 30%), 16 cm (pente 25%)
- Pose à sec : fixation obligatoire en zones de vent (1/4 des tuiles en zone 1, 1/3 zone 2, toutes zone 3-4)
- Pose en mortier de scellement : interdite sauf accessoires (faîtage, noues)

Éléments de jonction :
- Faîtage ventilé : espace 2 cm minimum, grille anti-rongeurs
- Noue : zinc, plomb ou EPDM, largeur ≥ 33 cm chaque côté de l'axe
- Égout : tuile d'about, chéneau ou larmier débord ≥ 5 cm du nu mur
- Rives : tuile de rive ou rabat plomb/zinc ≥ 15 cm

Isolation et ventilation :
- Ventilation sous tuile : lame d'air 2 cm minimum entre isolant et tuile
- Écrans de sous-toiture HPV (haute perméabilité vapeur) : sd ≤ 0,3 m

Zones de neige : pureau réduit + fixation systématique de toutes les tuiles.
"""),

    _entry("DTU 40.41", "Couverture en zinc",
           "SO - Étanchéité", "Élevée",
           """
Champ d'application : couvertures et façades en zinc titane selon NF EN 988.

Caractéristiques du zinc :
- Épaisseur minimale en toiture : 0,65 mm (faible pente), 0,80 mm (usuel)
- Coefficient de dilatation thermique : 2,2 × 10⁻⁵ /°C
- Dilatation pour 1 m de zinc : 2,2 mm pour ΔT = 100°C → joints de dilatation obligatoires

Pentes minimales :
- Joint debout : 5% (long pan), 3% (noue)
- Feuille à tasseaux : 25%
- Bac à joint debout préformé : 2% minimum

Joints debout :
- Espacement : 40 à 65 cm selon vent et pente
- Agrafage : toutes les 33 cm (zone courante), 20 cm (zones exposées)
- Pinces de fixation : acier inox 304 minimum, jamais d'acier ordinaire au contact zinc

Sous-face et ventilation :
- Volige bois traité ou support continu nécessaire
- Lame d'air ≥ 20 mm sous le zinc
- Pas de contact direct zinc/béton/mortier (réaction basique)
- Papier kraft bitumé ou écran HPV interposé

Raccordements et relevés :
- Relevé sous zinc : ≥ 15 cm
- Bavette zinc sur maçonnerie : engravure 2 cm minimum
- Solin zinc : agrafé et masticé

Entretien : inspection tous les 10 ans, nettoyage des mousses (traitement biocide).
"""),

]

# ════════════════════════════════════════════════════════════
# DTU — ISOLATION / SECOND ŒUVRE
# ════════════════════════════════════════════════════════════

DTU_ISOLATION = [

    _entry("DTU 45.10", "Isolation des combles par soufflage",
           "SO - Isolation", "Normale",
           """
Champ d'application : isolation thermique des combles perdus par soufflage de laine minérale ou ouate de cellulose.

Matériaux isolants soufflés :
- Laine de verre : λ ≤ 0,040 W/(m.K), densité soufflée 8 à 20 kg/m³
- Laine de roche : λ ≤ 0,040 W/(m.K), densité soufflée 25 à 45 kg/m³
- Ouate de cellulose : λ ≤ 0,042 W/(m.K), densité soufflée 25 à 60 kg/m³

Épaisseurs pour atteindre les objectifs RE 2020 :
- R = 7,0 m².K/W : 28 cm laine verre λ=0,040
- R = 8,0 m².K/W : 32 cm laine verre λ=0,040
- R = 10,0 m².K/W : 40 cm laine verre λ=0,040

Mise en œuvre :
- Obturation de toutes les entrées d'air (boîtes électriques, chemins de câbles, pénétrations)
- Mise en place du pare-vapeur (sd ≥ 18 m) avant soufflage si non existant
- Jauges de repères de hauteur posées tous les 5 m²
- Trappe d'accès isolée (panneau amovible R ≥ valeur comble)
- Garde-corps soufflage : maintien de la lame de ventilation sous rampant (≥ 2 cm)
- Tassement à considérer : +10% d'épaisseur initiale pour laine de verre

Ventilation combles :
- Entrées d'air en égout + sorties en faîtage
- Ratio surface libre ventilation ≥ 1/500 de la surface de comble

Points singuliers :
- Encoffrement des luminaires encastrés chauds (distance sécurité incendie)
- Maintien de l'accès aux équipements (VMC, etc.) par plancher de circulation
"""),

    _entry("DTU 45.11", "Isolation thermique de combles et toitures — Laines minérales en rouleaux",
           "SO - Isolation", "Normale",
           """
Champ d'application : isolation en rampants, combles aménagés et plafonds sous rampants.

Mise en œuvre entre chevrons (1ère couche) :
- Largeur rouleau = entraxe chevrons + 2 cm (compression latérale assure jointoiement)
- Pose perpendiculaire aux chevrons si 2 couches
- Pas de pont thermique au droit des chevrons sans croisement

Croisement obligatoire (2ème couche) :
- Couche croisée perpendiculaire à la première
- Décalage des joints d'au moins 20 cm
- Résistance totale = somme des résistances des 2 couches

Pare-vapeur :
- Côté chaud (intérieur) : sd ≥ 18 m (film polyéthylène 200 µm ou kraft armé)
- Recouvrement des lés : ≥ 10 cm, agrafé + ruban adhésif spécial
- Relevés sur murs et gaines techniques : ≥ 10 cm

Lame de ventilation sous couverture :
- Maintien obligatoire : ≥ 20 mm (comble), ≥ 30 mm (toiture rampant)
- Grilles anti-rongeurs en entrée d'air

Conditions climatiques de pose :
- Température ≥ +5°C
- Pas de pose sous pluie directe avant fermeture
"""),

]

# ════════════════════════════════════════════════════════════
# DTU — PLOMBERIE / SANITAIRES
# ════════════════════════════════════════════════════════════

DTU_PLOMBERIE = [

    _entry("DTU 60.1", "Plomberie sanitaire — Installations eau potable",
           "Plomb - Plomberie", "Élevée",
           """
Champ d'application : réseaux d'eau froide et chaude sanitaire dans les bâtiments.

Matériaux de canalisations :
- Cuivre (NF EN 1057) : assemblage brasé, à sertir ou à compression
- Multicouche PER-AL-PER : ≤ 90°C, pression ≤ 10 bar
- PER (polyéthylène réticulé) : enrobé obligatoire, gaine corrugée
- Acier galvanisé : interdit en contact cuivre (corrosion galvanique)
- Raccords laiton ou bronze uniquement avec cuivre

Dimensionnement des réseaux (NF EN 806-3) :
- Débit de base par appareil : WC 0,1 l/s, lavabo 0,1 l/s, douche 0,2 l/s, baignoire 0,3 l/s, LV 0,2 l/s
- Vitesse d'écoulement : 0,5 à 1,5 m/s (eau froide), 0,3 à 1,0 m/s (eau chaude)
- Pression minimale aux appareils : 1 bar (WC), 1,5 bar (mitigeur thermostatique)
- Pression maximale en tout point : 5 bar (réducteur obligatoire si réseau > 5 bar)

Protection anti-retour et disconnexion :
- Clapet anti-retour sur tout branchement à un appareil
- Disconnecteur BA (type BA selon NF EN 1717) pour raccordements à risques
- Disconnecteur CA ou CB pour arrosage, lave-vaisselle, etc.

Eau chaude sanitaire (ECS) :
- Température de production : 60°C minimum (anti-légionellose)
- Température de distribution : maintien ≥ 55°C sur toute la boucle
- Eau mitigée en sortie (robinetterie thermostatique) : ≤ 50°C pour risque brûlure

Essais de réception :
- Épreuve hydraulique : 1,5 × pression de service, ≥ 15 bar, maintenu 30 min
- Désinfection réseau eau potable avant mise en service (chloration)
- Rinçage jusqu'à teneur en chlore résiduel < 0,2 mg/l

Traçabilité : étiquetage couleur normalisé (EF bleu, ECS rouge, EFS vert).
"""),

    _entry("DTU 60.11", "Règles de calcul des installations de plomberie sanitaire",
           "Plomb - Plomberie", "Normale",
           """
Règles de dimensionnement des réseaux de plomberie (méthode probabiliste).

Débits de base (Qa) par appareil sanitaire :
- Robinet d'eau froide isolé : 0,2 l/s
- Lavabo / Bidet : Qa = 0,1 l/s (froid + chaud)
- Baignoire : Qa = 0,3 l/s
- Douche : Qa = 0,2 l/s
- WC chasse 9 litres : Qa = 0,1 l/s
- WC chasse 6 litres : Qa = 0,1 l/s
- Lave-linge : Qa = 0,2 l/s
- Lave-vaisselle : Qa = 0,2 l/s
- Évier cuisine : Qa = 0,2 l/s

Coefficient de simultanéité :
- Usage privatif (logement) : Ks = 1/√N (N = nombre de robinets)
- Usage collectif (hôtel, internat) : Ks = 0,7/√N
- Usage public (gare, aéroport) : Ks = 1 (simultanéité totale à considérer)

Débit de calcul : Qc = Ks × ΣQa

Diamètres nominaux courants :
- DN15 (1/2") : jusqu'à 0,3 l/s
- DN18 (3/4") : jusqu'à 0,6 l/s  
- DN22 (7/8") : jusqu'à 1,0 l/s
- DN28 (1"1/8") : jusqu'à 1,8 l/s
- DN35 (1"3/8") : jusqu'à 3,0 l/s

Pertes de charge : calcul par mètre équivalent ou Darcy-Weisbach.
"""),

]

# ════════════════════════════════════════════════════════════
# DTU — ÉLECTRICITÉ
# ════════════════════════════════════════════════════════════

DTU_ELECTRICITE = [

    _entry("NF C 15-100", "Installations électriques basse tension — Règles générales",
           "Élec - Électricité", "Critique",
           """
Norme fondamentale régissant toutes les installations électriques basse tension en France.

Tableaux électriques :
- Tableau principal (TGBT) : protection générale différentielle 500 mA ou 300 mA
- Tableau divisionnaire (TDD) : protection de chaque départ
- Disjoncteur de branchement EDF : calibre selon puissance souscrite
- Interrupteur différentiel de tête : 30 mA obligatoire pour locaux mouillés

Circuits et sections de câble :
- Éclairage : 1,5 mm² (max 8 points), disjoncteur 10A
- Prises 16A : 2,5 mm² (max 8 prises par circuit), disjoncteur 16A
- Cuisinière / plaque : 6 mm², disjoncteur 32A, circuit dédié
- Lave-linge, sèche-linge, lave-vaisselle : 2,5 mm², disjoncteur 20A, circuit dédié
- Chauffe-eau électrique : 2,5 mm², disjoncteur 20A, circuit dédié
- Climatisation ≤ 5,5 kW : 4 mm², disjoncteur 25A

Salle de bain — Volumes réglementaires :
- Volume 0 (dans la baignoire/douche) : IPX7, appareils très basse tension 12V
- Volume 1 (au-dessus baignoire, h≤2,25m) : IPX4 minimum, pas de prise
- Volume 2 (0,6m autour vol.1) : IPX4, appareils fixés autorisés (rasoir, sèche-cheveux)
- Hors volume : prises et interrupteurs autorisés à ≥60 cm de la paroi baignoire

Prises de courant — Règles NF C 15-100 :
- Séjour : minimum 5 prises + 1 prise TV + 1 prise RJ45
- Chambre : minimum 3 prises + 1 prise RJ45
- Cuisine : minimum 6 prises (dont 4 au-dessus plan de travail) + prises dédiées
- Couloir/entrée : 1 prise minimum

Liaison équipotentielle :
- Salle de bain : raccordement de toutes masses métalliques (baignoire, colonne, gaine)
- Conducteur PE : section ≥ 2,5 mm² sous conduit, 4 mm² nu

Mise à la terre :
- Prise de terre : piquet acier galvanisé ∅26mm L≥2m, ou conducteur en fond de fouille
- Résistance ≤ 100 Ω (déclenchement différentiel 500 mA)
- Résistance ≤ 50 Ω si usage différentiel 300 mA

Vérification CONSUEL obligatoire avant mise en service.
"""),

    _entry("NF C 14-100", "Installations de branchement basse tension",
           "Élec - Électricité", "Élevée",
           """
Règles de raccordement au réseau ENEDIS (anciennement ERDF).

Types de branchement :
- Monophasé 230V : jusqu'à 12 kVA (logement individuel standard)
- Triphasé 400V : au-delà de 12 kVA ou sur demande

Puissances souscrites et calibres disjoncteurs :
- 3 kVA → disjoncteur 15A mono
- 6 kVA → disjoncteur 30A mono
- 9 kVA → disjoncteur 45A mono
- 12 kVA → disjoncteur 60A mono
- 18 kVA → 3×30A triphasé
- 24 kVA → 3×40A triphasé
- 36 kVA → 3×60A triphasé

Câbles de branchement :
- Aérien isolé torsadé : câble aluminium PR section selon puissance
- Souterrain : câble cuivre ou aluminium sous gaine
- Section minimale : 16 mm² alu (monophasé), 25 mm² alu (triphasé)

Compteur Linky :
- Pose en limite de propriété ou en gaine technique logement
- Hauteur de pose : entre 1,20 m et 1,80 m du sol fini
- Espace libre : 30 cm de chaque côté

Coffret de coupure (si compteur extérieur) :
- Disjoncteur de branchement + accessoires normalisés ENEDIS
- Serrure barillet ENEDIS
"""),

]

# ════════════════════════════════════════════════════════════
# DTU — CVC / CHAUFFAGE
# ════════════════════════════════════════════════════════════

DTU_CVC = [

    _entry("DTU 65.11", "Dispositifs de sécurité pour chauffage central",
           "CVC - Chauffage", "Critique",
           """
Champ d'application : sécurités obligatoires pour installations de chauffage central eau chaude.

Chaudières gaz (< 400 kW) :
- Soupape de sécurité tarée à 3 bar (logement) ou 4 bar (collectif)
- Vase d'expansion : volume calculé selon contenance installation et pression
- Thermostats de sécurité : STB (sécurité température haute) ≥ 110°C
- Pressostat bas : arrêt brûleur si pression < 0,5 bar
- Détecteur CO : obligatoire en local chaudière fermé

Puissances et locaux :
- < 70 kW : local non spécifique requis, ventilation haute + basse obligatoire
- 70 à 400 kW : local chaufferie dédié, RF 1h, porte CF
- > 400 kW : chaufferie indépendante, règles ERP/ICPE selon cas

Ventilation des locaux chaudières (gaz) :
- Amenée d'air comburant : 5 cm² par kW pour chaudières atmosphériques
- Sortie des gaz : conduit en dépression naturelle ou ventouse pour chaudières à condensation
- Désenfumage : requis pour chaufferies > 70 kW

Pompe à chaleur (PAC) :
- Soupape et vase d'expansion côté eau : mêmes règles que chaudière
- Fluide frigorigène R32, R410A : détecteur de fuite pour locaux fermés
- Niveau sonore : respecter les seuils locaux (arrêté du 30/05/1996, limites selon zone)

Plancher chauffant hydraulique :
- Pression d'essai : 6 bar pendant 24h avant chape
- Température départ maximale : 50°C (norme EN 1264)
- Distributeurs avec débitmètres et vannes de réglage
"""),

    _entry("DTU 65.12", "Réalisation des installations de génie climatique",
           "CVC - Chauffage", "Élevée",
           """
Champ d'application : réalisation et réception des installations CVC dans les bâtiments.

Canalisations de chauffage :
- Acier noir soudé (NF EN 10216-2) : > DN50 en général
- Cuivre (NF EN 1057) : ≤ DN54 en logement
- Multicouche ou PER : circuits basse température ≤ 70°C
- Isolation thermique obligatoire : λ × e ≤ coefficient selon DTU
- Purge d'air : purgeurs automatiques aux points hauts, manuels en plancher

Essai d'étanchéité :
- Pression d'épreuve : 1,5 × Pmax de service (mini 6 bar)
- Durée : 30 minutes minimum, 2h pour contrôle complet
- Avant fermeture des saignées et cloisons

Équilibrage hydraulique :
- Vannes d'équilibrage sur chaque colonne
- Mesure des débits par débitmètre
- Réglage des robinets de radiateurs (préréglage fabricant)

Réception et essais de performance :
- Mesure températures départ/retour
- Vérification rendement chaudière (CO2 fumées, rendement saisonnier)
- Mesure puissances absorbées pompes
- Essai de régulation : simulation consignes, vérification réponse

Contrat d'entretien obligatoire pour chaudières > 4 kW (décret 2009-649).
Attestation d'entretien annuelle à fournir au propriétaire.
"""),

]

# ════════════════════════════════════════════════════════════
# NORMES ET RÉGLEMENTATION
# ════════════════════════════════════════════════════════════

NORMES_REGLEMENTATION = [

    _entry("RE 2020", "Réglementation Environnementale 2020 — Exigences thermiques et carbone",
           "Admin - Administratif", "Critique",
           """
La RE 2020 est entrée en vigueur le 1er janvier 2022 pour les maisons individuelles et logements collectifs.
Elle remplace la RT 2012 et ajoute des exigences carbone (ACV — analyse du cycle de vie).

Indicateurs de performance obligatoires :

1. Bbio (Besoin bioclimatique) :
   - Qualité de l'enveloppe thermique indépendamment des systèmes
   - Bbio ≤ Bbio_maxmodulé (valeur selon zone climatique, altitude, surface)
   - Valeur de référence : Bbiomax ≈ 63 points (zone H1a, maison individuelle)

2. Cep (Consommation d'énergie primaire) :
   - Énergie primaire pour chauffage + ECS + refroidissement + éclairage + auxiliaires
   - Cep ≤ Cep_max (≈ 65 kWhep/m².an zone H1 logement collectif)
   - Cep,nr (énergie non renouvelable) limité séparément

3. DH (Degrés Heures d'inconfort) :
   - Nouveau indicateur absent de la RT 2012
   - Limite inconfort estival : DH ≤ 350 h (MI), ≤ 1250 h (LC) en zone H1
   - Favorise protections solaires, inertie, ventilation nocturne

4. Ic énergie (Impact carbone énergie) :
   - Émissions CO2 sur 50 ans liées à l'énergie : ≤ 560 kgeqCO2/m² (MI)

5. Ic construction (Impact carbone composants) :
   - ACV dynamique des matériaux et équipements
   - Seuil 2022 : ≤ 640 kgeqCO2/m² (MI) ; renforcé en 2025 et 2028

Interdit :
- Chauffage au gaz comme système principal dans les maisons neuves
- Climatisation à détente directe à haut GWP comme système principal

Logiciel de calcul : Th-BCE 2020 (moteur officiel), avec résultats en RSET.
"""),

    _entry("NF EN 1990", "Eurocode 0 — Bases de calcul des structures",
           "GO - Structure béton", "Élevée",
           """
Eurocode 0 : bases générales pour le calcul aux états limites de toutes les structures.

États limites :
- ELU (État Limite Ultime) : rupture, instabilité, perte d'équilibre
- ELS (État Limite de Service) : déformations excessives, vibrations, fissuration

Combinaisons d'actions à l'ELU (situation persistante/transitoire) :
- ΣγG × Gk + γQ × Qk1 + ΣγQ × ψ0 × Qki
- γG = 1,35 (défavorable), 1,00 (favorable)
- γQ = 1,50 (variable)

Combinaisons à l'ELS :
- Combinaison caractéristique : Gk + Qk1 + ΣψO × Qki
- Combinaison fréquente : Gk + ψ1 × Qk1 + Σψ2 × Qki
- Combinaison quasi-permanente : Gk + Σψ2 × Qki

Valeurs des coefficients ψ (NF EN 1990 Annexe A1) :
- Charges d'exploitation catégorie A (habitation) : ψ0=0,7 ; ψ1=0,5 ; ψ2=0,3
- Charges d'exploitation catégorie B (bureaux) : ψ0=0,7 ; ψ1=0,5 ; ψ2=0,3
- Neige altitude < 1000 m : ψ0=0,5 ; ψ1=0,2 ; ψ2=0
- Vent : ψ0=0,6 ; ψ1=0,2 ; ψ2=0

Charges permanentes (valeurs indicatives NF EN 1991-1-1) :
- Béton armé : 25 kN/m³
- Maçonnerie brique pleine : 18 kN/m³
- Maçonnerie bloc béton creux : 12 kN/m³
- Chape + carrelage : 1,2 à 1,8 kN/m²

Charges d'exploitation (valeurs indicatives) :
- Logement (cat. A) : 1,5 kN/m²
- Bureaux (cat. B) : 2,5 kN/m²
- Parkings (cat. F) : 2,5 kN/m² (véhicules ≤ 30 kN)
"""),

    _entry("NF EN 1992-1-1", "Eurocode 2 — Calcul des structures en béton",
           "GO - Structure béton", "Élevée",
           """
Eurocode 2 : conception et dimensionnement des structures en béton armé et précontraint.

Résistances caractéristiques du béton :
- fck (cylindrique) : C20/25 → 20 MPa ; C25/30 → 25 MPa ; C30/37 → 30 MPa
- fcd (de calcul) : fcd = αcc × fck / γC ; γC = 1,5 ; αcc = 1,0 (France)
- Résistance à la traction : fctm = 0,3 × fck^(2/3) pour fck ≤ C50

Résistances des aciers :
- fyk = 500 MPa (B500B/C standard)
- fyd = fyk / γS = 500 / 1,15 = 435 MPa

Vérification flexion simple (rectangulaire) :
- μ = Msd / (b × d² × fcd)
- Si μ ≤ μlim (0,372 pour ε_s=10‰) : section non comprimée, pas d'armature comprimée
- As = Msd / (z × fyd) avec z = bras de levier ≈ 0,9d (approximation courante)

Vérification effort tranchant :
- VEd ≤ VRd,c (sans armatures d'âme) : VRd,c = [0,18/γc × k × (100ρl × fck)^(1/3)] × bw × d
- Si VEd > VRd,c : armatures transversales (étriers) obligatoires
- Angle des bielles béton θ : 21,8° ≤ θ ≤ 45° (cotg θ entre 1 et 2,5)

États limites de service :
- Déformation maximale : L/250 (total), L/500 (après cloisons)
- Largeur de fissure : wk ≤ 0,3 mm (XC2/XC3), 0,2 mm (XD/XS)
- Contraintes de compression au service : σc ≤ 0,6 × fck (quasi-permanent)
"""),

    _entry("Code du Travail — Sécurité Chantier", "Obligations légales de sécurité sur chantier BTP",
           "Sécu - Sécurité chantier", "Critique",
           """
Principales obligations légales du Code du Travail et des décrets relatifs à la sécurité sur les chantiers BTP.

Plan de Prévention (PP) :
- Obligatoire dès que 400 heures de travail ou travaux dangereux
- Co-signé par maître d'ouvrage et entreprise extérieure
- Recense les risques, mesures de prévention, matériels utilisés

Plan Particulier de Sécurité et Protection de la Santé (PPSPS) :
- Obligatoire pour chantiers avec SPS de niveau 1 ou 2
- Rédigé par chaque entreprise exécutante
- Contenu : analyse des risques propres, mesures préventives, procédures d'urgence

Coordination SPS (Sécurité et Protection de la Santé) :
- CSPS niveau 1 : chantiers > 10 000 hj ou > 5 entreprises simultanées + ERP/IGH/ICPE
- CSPS niveau 2 : chantiers entre 500 hj et 10 000 hj
- CSPS niveau 3 : chantiers < 500 hj et moins de 20 travailleurs simultanément

EPI obligatoires sur chantier (R4323-91 et suivants) :
- Casque de protection : obligatoire en permanence (NF EN 397)
- Chaussures de sécurité : S3 minimum (embout + semelle anti-perforation)
- Gilet haute visibilité : classe 2 minimum (NF EN 20471)
- Harnais antichute : obligatoire au-dessus de 3 m, sauf protections collectives suffisantes
- Lunettes de protection : lors de tout travail générant projections
- Protection auditive : si exposition > 80 dB(A)

Travaux en hauteur :
- Protection collective prioritaire sur protection individuelle
- Garde-corps : hauteur ≥ 1,00 m, plinthe ≥ 15 cm, lisse intermédiaire
- Échafaudages : réception par personne compétente, ancrage calculé, filets de sécurité
- Passerelles : largeur ≥ 60 cm, lisse ≥ 90 cm

Installations de chantier :
- Vestiaires, sanitaires, réfectoire : obligations selon effectif (R4228-1)
- Eau potable : 3 litres/personne/jour minimum
- Toilettes : 1 WC pour 20 personnes maximum

VLEP (Valeurs Limites d'Exposition Professionnelle) — Poussières :
- Poussières inhalables : 10 mg/m³ (8h)
- Poussières alvéolaires : 5 mg/m³ (8h)
- Silice cristalline : 0,1 mg/m³ (8h) — VLEP contraignante
- Amiante : 10 fibres/litre (VLEP réglementaire stricte, repérage obligatoire)
"""),

    _entry("Réglementation Amiante", "Obligations de repérage et gestion de l'amiante",
           "Sécu - Sécurité chantier", "Critique",
           """
Réglementation française sur l'amiante dans les bâtiments (décret 2011-629, arrêtés 2012-2013).

Dossier Technique Amiante (DTA) :
- Obligatoire pour tout immeuble bâti dont le PC est antérieur au 1er juillet 1997
- Tenu par le propriétaire, remis au locataire et à toute entreprise intervenant
- Contient : repérage amiante, préconisations, plan de localisation

Repérage avant travaux (RAT) :
- Obligatoire avant TOUT travail pouvant exposer à l'amiante (démolition, rénovation)
- Réalisé par opérateur certifié (certification COFRAC)
- Périmètre : tous les matériaux susceptibles de contenir de l'amiante dans la zone de travaux

Niveaux de risque :
- Liste A (matériaux friables) : flocages, calorifugeages, faux-plafonds → retrait obligatoire avant travaux
- Liste B (matériaux non friables) : dalles vinyle-amiante, plaques fibrociment, etc. → évaluation de l'état
- Liste C : matériaux extérieurs (toitures, façades) → repérage si travaux

VLEP amiante : 10 fibres/litre (valeur limite réglementaire) ; objectif de moyens : 5 f/l.

Entreprises de retrait :
- Certification obligatoire (sous-section 3 ou 4 selon type de travaux)
- Plan de retrait soumis à l'Inspection du Travail 30 jours avant travaux
- Déchets amiante : élimination en centre agréé (ISDD), traçabilité BSD

Sanctions : travaux sans repérage = infraction pénale, arrêt de chantier immédiat.
"""),

    _entry("DTU 26.1", "Enduits aux mortiers de ciment, chaux et mélange",
           "SO - Plâtrerie", "Normale",
           """
Champ d'application : enduits extérieurs et intérieurs sur supports maçonnerie.

Supports acceptables :
- Briques, blocs béton, béton banché, pierres naturelles
- Condition : cohésion suffisante, propreté, humidification avant enduit

Composition des mortiers (proportions volumiques) :
- Enduit bâtard courant : 1 ciment + 1 chaux + 6 sable
- Enduit ciment seul : 1 ciment + 3 sable (rigide, risques de fissuration)
- Enduit chaux seul : 1 chaux aérienne + 3 sable (souple, respirant)
- Finition : 1 ciment blanc + 2 sable fin ou enduit de finition prêt-à-l'emploi

Nombre de couches :
- Gobetis (accrochage) : 3 à 5 mm, projeté, non dressé
- Corps d'enduit : 10 à 15 mm, dressé à la règle
- Finition : 2 à 5 mm selon effet recherché

Épaisseur totale maximale :
- Extérieur : 25 mm (au-delà, risque de chute)
- Intérieur : 15 mm (3 couches), 20 mm sur support irrégulier

Conditions météorologiques :
- Température : +5°C minimum, éviter soleil direct et vent fort
- Gel : interdit si T < +5°C (dans les 24h)
- Pluie : protéger l'enduit frais

Délais entre couches :
- Gobetis → corps d'enduit : 24h minimum (humide), 72h (temps sec chaud)
- Corps d'enduit → finition : 72h minimum

Pathologies courantes :
- Fissures de retrait : couche trop épaisse, séchage trop rapide
- Décollement : support trop lisse, trop sec ou pollué
- Efflorescences : remontées de sel, trop d'eau de gâchage
"""),

]

# ════════════════════════════════════════════════════════════
# VRD / VOIRIE
# ════════════════════════════════════════════════════════════

DTU_VRD = [

    _entry("DTU 70.1", "Installations électriques — Voirie et réseaux divers",
           "VRD - Voirie", "Élevée",
           """
Règles de pose des réseaux enterrés (eau, électricité, télécoms, gaz) en domaine public et privé.

Profondeurs minimales de pose (TPC et câbles) :
- Électricité HTA : 0,85 m sous trottoir, 1,00 m sous chaussée
- Électricité BT : 0,60 m sous trottoir, 0,85 m sous chaussée
- Éclairage public : 0,60 m minimum
- Gaz (MP/BP) : 0,60 m minimum, grillage avertisseur jaune à 0,20 m au-dessus
- Eau potable : 0,80 m minimum (hors gel), grillage avertisseur bleu
- Télécom : 0,60 m minimum, grillage avertisseur vert ou rouge

Tranchées et remblaiement :
- Fond de tranchée : lit de sable fin 10 cm avant pose du câble/canalisation
- Enrobage câble : sable fin 20 cm au-dessus du câble
- Grillage avertisseur : posé 20 cm au-dessus du réseau
- Remblai : matériaux sélectionnés (GNT 0/31,5), compactage par couches de 30 cm
- Essai de compactage : densité ≥ 95% de l'OPM

Distances entre réseaux (parallèles) :
- Eau potable / assainissement : ≥ 0,50 m (horizontal)
- Électricité / gaz : ≥ 0,20 m
- Eau potable / électricité : ≥ 0,20 m

Croisements entre réseaux :
- Distance verticale minimale : 0,20 m (avec fourreau de protection)
- Fourreau obligatoire à tout croisement
"""),

    _entry("Assainissement NF DTU 64.1", "Dispositifs d'assainissement non collectif (ANC)",
           "VRD - Voirie", "Élevée",
           """
Règles techniques pour les installations d'assainissement autonome (fosses toutes eaux + épuration).

Filière classique (fosse + épandage) :
- Fosse toutes eaux : volume minimal 3 m³ jusqu'à 5 pièces, +1 m³ par pièce supplémentaire
- Fosse septique : accepte seulement les eaux vannes, déconseillée
- Épandage souterrain : tranchées d'infiltration en tuyaux annelés ∅100 mm, lit de gravier

Dimensionnement des tranchées d'épandage :
- Surface d'épandage : selon capacité d'absorption du sol (test de perméabilité Ks)
- Ks > 150 mm/h : filtre à sable vertical
- 15 < Ks < 150 mm/h : épandage souterrain traditionnel
- Ks < 15 mm/h : filière agréée (lit bactérien, etc.)
- Tranchées : largeur 0,50 m, profondeur 0,60 m, longueur selon surface épandage
- Espacement tranchées : ≥ 1,50 m axe à axe
- Distance aux limites : ≥ 3 m ; aux arbres : ≥ 3 m ; aux puits : ≥ 35 m

Distances minimales réglementaires :
- Habitation : ≥ 5 m (fosse), ≥ 3 m (épandage)
- Limite propriété : ≥ 3 m
- Cours d'eau : ≥ 35 m
- Captage d'eau potable : ≥ 35 m (peut être majoré par SPANC)

Contrôle SPANC :
- Contrôle de conception avant travaux
- Contrôle de réalisation pendant travaux
- Contrôle de bon fonctionnement tous les 4 à 10 ans
- Vente immobilière : diagnostic ANC obligatoire (< 3 ans)

Entretien : vidange fosse toutes eaux tous les 4 ans maximum.
"""),

]

# ════════════════════════════════════════════════════════════
# SÉCURITÉ INCENDIE
# ════════════════════════════════════════════════════════════

DTU_INCENDIE = [

    _entry("Réglementation Incendie ERP", "Établissements Recevant du Public — Règles de sécurité incendie",
           "Sécu - Sécurité chantier", "Critique",
           """
Réglementation sécurité incendie pour les ERP (arrêté du 25 juin 1980 et modifications).

Classement des ERP :
- Types : L (salles), M (commerces), N (restaurants), O (hôtels), R (enseignement), S (bibliothèques), U (soins), W (administrations), etc.
- Catégories : 1ère (> 1500 pers), 2ème (de 701 à 1500), 3ème (de 301 à 700), 4ème (≤ 300), 5ème (petit ERP sous seuils)

Désenfumage :
- ERP > 300 m² en sous-sol : désenfumage mécanique obligatoire
- ERP en RDC ou étages : désenfumage naturel ou mécanique selon surface et hauteur
- Évacuation des fumées : débit minimal 0,5 m³/s par canton de désenfumage

Compartimentage :
- Parois coupe-feu (CF) selon résistance au feu : REI 30, REI 60, REI 120
- Portes coupe-feu : EI30, EI60 (avec ferme-porte obligatoire)
- Recoupement tous les 300 m² (locaux à risques) à 600 m² (usage courant)

Évacuation :
- 2 sorties minimum pour tout ERP (dès le seuil de la 5ème catégorie)
- Largeur minimale dégagement : UP (Unité de Passage = 0,60 m)
- Calcul : 1 UP pour 100 personnes (RDC), 1 UP pour 75 pers (étages/sous-sol)
- Distance maximale à une sortie : 30 m (sans recoupement), 50 m (avec)

Éclairage de sécurité :
- BAES (Blocs Autonomes d'Éclairage de Sécurité) : 1 lux minimum dans les circulations
- Autonomie : 1h (évacuation), 6h (ambiance anti-panique)

Sprinklers : obligatoires pour certains types (magasins > 3000 m², entrepôts, etc.)

Commission de sécurité : visite avant ouverture + périodiquement (1 à 5 ans selon catégorie).
"""),

    _entry("IT 246 — Réaction au feu des matériaux", "Classement Euroclasse et réaction au feu",
           "Sécu - Sécurité chantier", "Élevée",
           """
Classement européen de réaction au feu (Euroclasses) selon EN 13501-1.

Classes de réaction au feu :
- A1 : incombustible (béton, brique, pierre, verre, acier, laine minérale)
- A2 : quasi-incombustible (plâtre, certains composites)
- B : très difficilement inflammable
- C : difficilement inflammable
- D : moyennement inflammable
- E : facilement inflammable
- F : non classé (comportement inconnu)

Indices complémentaires :
- s (fumée) : s1 (peu de fumée), s2 (quantité limitée), s3 (beaucoup)
- d (gouttelettes) : d0 (pas de gouttelettes enflammées), d1 (limitées), d2 (beaucoup)
- Exemple : B-s1,d0 = très bonne réaction au feu, peu de fumée, pas de gouttelettes

Exigences réglementaires courantes :
- Façades ventilées : A2-s1,d0 ou B-s1,d0 pour parements extérieurs (IGH et ERP)
- Isolants en combles : A1 ou A2 si proximité source de chaleur
- Revêtements de sols : Bfl-s1 minimum en ERP catégories 1 à 3
- Faux-plafonds : B-s2,d0 minimum en ERP

Correspondance anciens classements français → Euroclasses :
- M0 → A1 ou A2
- M1 → B ou C
- M2 → C ou D
- M3 → D ou E
- M4 → E
"""),

]

# ════════════════════════════════════════════════════════════
# ENVIRONNEMENT
# ════════════════════════════════════════════════════════════

DTU_ENVIRONNEMENT = [

    _entry("Gestion des déchets de chantier", "Réglementation tri et élimination des déchets BTP",
           "Env - Environnement", "Élevée",
           """
Réglementation française sur les déchets de chantier du BTP (loi AGEC, décret 2020-1573).

Obligation de tri à la source (décret 5 flux + 10 flux BTP depuis 2023) :
- Fraction minérale : béton, briques, tuiles, céramiques → déchèterie BTP ou réemploi
- Bois : palettes, coffrage, charpente → valorisation énergétique ou matière
- Métaux : ferrailles, câbles, profilés → recyclage (taux ≥ 98%)
- Plastiques : films, tuyaux, isolants → collecte séparée
- Verre : vitrage → filière verre
- Plâtre : plaques BA13, enduits → filière plâtre (décharge spécifique)
- Déchets dangereux (DD) : solvants, peintures, amiante, hydrocarbures → ISDD

Bordereau de Suivi des Déchets (BSD) :
- Obligatoire pour tout déchet dangereux
- Signé par producteur + transporteur + éliminateur
- Conservation 3 ans minimum

Diagnostic Déchets avant démolition :
- Obligatoire pour démolitions > 1000 m² ou démolitions de bâtiments structurés
- Réalisé avant dépôt de PC de démolition
- Inventaire et estimation des tonnages par catégorie

Traçabilité :
- Tickets de pesée des déchèteries à conserver
- Rapport de gestion des déchets dans le DIUO (dossier des ouvrages exécutés)

Objectifs nationaux (SNDS 2020-2027) :
- 70% des déchets BTP valorisés (matière ou énergie)
- Réduction de 30% des déchets non dangereux non inertes mis en décharge
"""),

    _entry("Réglementation Acoustique NRA", "Nouvelle Réglementation Acoustique des bâtiments d'habitation",
           "SO - Isolation", "Élevée",
           """
Arrêté du 30 juin 1999 (NRA) — Réglementation acoustique applicable aux logements neufs.

Isolement aux bruits aériens entre logements :
- DnT,A ≥ 53 dB (entre logements voisins horizontaux)
- DnT,A ≥ 53 dB (entre logements superposés)
- DnT,A ≥ 45 dB (entre logement et cage d'escalier)
- DnT,A ≥ 30 dB (entre logement et local à ordures/parking)

Isolement vis-à-vis des bruits extérieurs :
- DnT,A,tr selon classement acoustique de la voie (1 à 5)
- De 28 dB (voie peu bruyante) à 45 dB (voie très bruyante, autoroute)

Bruit des équipements collectifs (LnAT) :
- Équipements individuels dans le logement : 35 dB(A)
- Équipements collectifs (VMC, ascenseur) : 30 dB(A) dans les chambres
- Équipements individuels dans autre logement : 30 dB(A)

Bruits d'impact (LnT,w) :
- Entre logements superposés : LnT,w ≤ 58 dB

Solutions techniques courantes :
- Doubles parois avec lame d'air ≥ 3 cm + désolidarisation complète
- Plancher acoustique : chape flottante sur résilient ΔLw ≥ 20 dB
- Entrées d'air acoustiques en façade (Dn,e,w ≥ valeur requise)
- Portes palières acoustiques : Rw+C ≥ 32 dB minimum

Contrôle : mesures acoustiques de réception possibles (CSTB ou acousticien certifié).
"""),

]

# ════════════════════════════════════════════════════════════
# ASSEMBLAGE FINAL
# ════════════════════════════════════════════════════════════

def get_all_knowledge_chunks() -> List[Dict[str, Any]]:
    """Retourne l'ensemble des chunks de la base de connaissances BTP."""
    all_chunks = (
        DTU_GROS_OEUVRE +
        DTU_ETANCHEITE +
        DTU_ISOLATION +
        DTU_PLOMBERIE +
        DTU_ELECTRICITE +
        DTU_CVC +
        NORMES_REGLEMENTATION +
        DTU_VRD +
        DTU_INCENDIE +
        DTU_ENVIRONNEMENT
    )

    # Corriger le total_chunks pour chaque entrée
    for i, chunk in enumerate(all_chunks):
        chunk["metadata"]["total_chunks"] = len(all_chunks)
        chunk["metadata"]["chunk_index"]  = i

    return all_chunks


KNOWLEDGE_SUMMARY = {
    "dtu_gros_oeuvre":     len(DTU_GROS_OEUVRE),
    "dtu_etancheite":      len(DTU_ETANCHEITE),
    "dtu_isolation":       len(DTU_ISOLATION),
    "dtu_plomberie":       len(DTU_PLOMBERIE),
    "dtu_electricite":     len(DTU_ELECTRICITE),
    "dtu_cvc":             len(DTU_CVC),
    "normes_reglementation": len(NORMES_REGLEMENTATION),
    "dtu_vrd":             len(DTU_VRD),
    "dtu_incendie":        len(DTU_INCENDIE),
    "dtu_environnement":   len(DTU_ENVIRONNEMENT),
    "total":               len(get_all_knowledge_chunks()),
}
