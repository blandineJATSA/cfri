"""
Générateur de données de démo réalistes pour CFRI.

Génère :
- 500 commandes avec montants réalistes
- 200 feedbacks variés (problèmes + positifs)

Usage :
    python generate_demo_data.py
"""

import csv
import random
from datetime import datetime, timedelta

# ── Configuration ─────────────────────────────────────────

random.seed(42)  # Résultats reproductibles

CLIENTS = [
    "sophie.martin@gmail.com",
    "thomas.bernard@outlook.com",
    "julie.dubois@gmail.com",
    "pierre.moreau@yahoo.fr",
    "marie.lefebvre@gmail.com",
    "nicolas.simon@hotmail.fr",
    "camille.laurent@gmail.com",
    "alexandre.michel@gmail.com",
    "emma.garcia@outlook.com",
    "lucas.david@gmail.com",
    "manon.bertrand@gmail.com",
    "hugo.roux@yahoo.fr",
    "lea.vincent@gmail.com",
    "mathieu.fournier@outlook.com",
    "chloe.morel@gmail.com",
    "romain.girard@hotmail.fr",
    "sarah.andre@gmail.com",
    "kevin.lefevre@gmail.com",
    "pauline.mercier@outlook.com",
    "florian.dupont@gmail.com",
    "aurelie.blanc@gmail.com",
    "jeremy.guerin@yahoo.fr",
    "laura.muller@gmail.com",
    "anthony.henry@outlook.com",
    "oceane.rousseau@gmail.com",
    "xavier.gauthier@hotmail.fr",
    "marine.perrin@gmail.com",
    "sebastien.colin@gmail.com",
    "jessica.lambert@outlook.com",
    "benjamin.fontaine@gmail.com",
]

PRODUITS = [
    ("Robe fleurie été", "ROB-001", 49.90),
    ("Jean slim fit", "JEAN-002", 69.90),
    ("Veste en cuir noir", "VEST-003", 149.90),
    ("Sneakers blanches", "SNEK-004", 89.90),
    ("Sac à main cuir", "SAC-005", 129.90),
    ("T-shirt coton bio", "TSH-006", 29.90),
    ("Manteau laine", "MAN-007", 189.90),
    ("Chemise oxford", "CHE-008", 59.90),
    ("Legging sport", "LEG-009", 39.90),
    ("Boots cuir marron", "BOOT-010", 119.90),
    ("Pull cachemire", "PULL-011", 99.90),
    ("Short bermuda", "SHO-012", 34.90),
    ("Robe de soirée", "ROB-013", 89.90),
    ("Sweat hoodie", "SWE-014", 54.90),
    ("Sandales été", "SAN-015", 44.90),
]

PROBLEMES_LIVRAISON = [
    "Ma commande est arrivée avec 10 jours de retard, aucune communication de votre part. Très déçue.",
    "Livraison prévue le 15, reçue le 23. Inacceptable pour un cadeau d'anniversaire.",
    "Colis marqué livré mais jamais reçu. Le livreur a dû le laisser chez un voisin sans prévenir.",
    "Troisième commande avec du retard. Je commence à perdre confiance en votre service de livraison.",
    "Commande passée il y a 3 semaines, toujours pas reçue. Le suivi ne se met pas à jour.",
    "Livraison très lente par rapport à ce qui était annoncé. 8 jours au lieu de 3.",
    "Colis reçu mais complètement écrasé. L'emballage était insuffisant pour protéger le produit.",
    "J'ai dû aller chercher mon colis à la poste car le livreur ne sonne jamais.",
    "Retard de 5 jours sans aucune explication. J'ai dû annuler le cadeau que je voulais offrir.",
    "La commande a été livrée à la mauvaise adresse malgré mes instructions claires.",
]

PROBLEMES_PRODUIT = [
    "La taille indiquée ne correspond pas du tout. J'ai commandé un M et c'est vraiment petit.",
    "Le produit reçu ne ressemble pas aux photos. La couleur est complètement différente.",
    "Coutures qui lâchent après seulement deux lavages. Très mauvaise qualité pour le prix.",
    "Le jean a une tache sur la jambe gauche à la réception. Produit défectueux.",
    "La fermeture éclair est cassée dès le premier essayage. Inacceptable.",
    "Matière beaucoup moins belle que sur le site. On voit que c'est du synthétique bas de gamme.",
    "Deux produits commandés, un seul reçu. L'autre n'est même pas mentionné dans le colis.",
    "Trous dans le tissu à la réception. Article clairement défectueux.",
    "La veste sent très mauvais à la réception, même après lavage l'odeur persiste.",
    "Boutons qui tombent après une seule utilisation. Qualité vraiment décevante.",
]

PROBLEMES_REMBOURSEMENT = [
    "Retour effectué il y a 3 semaines, toujours pas de remboursement sur mon compte.",
    "On m'a promis un remboursement sous 5 jours, je suis à J+15 et rien.",
    "Le service client m'a confirmé le remboursement par email mais l'argent n'arrive pas.",
    "J'ai renvoyé l'article il y a un mois. Ni remboursement ni échange. C'est scandaleux.",
    "Remboursement partiel reçu sans explication. On me doit encore 30 euros.",
    "Processus de retour très compliqué et long. Ça fait 4 semaines que j'attends.",
    "Impossible d'obtenir un bon de retour depuis une semaine. Le service client ne répond pas.",
]

PROBLEMES_SERVICE = [
    "Service client inaccessible. J'ai attendu 45 minutes au téléphone avant de raccrocher.",
    "Réponse automatique uniquement par email. Aucun humain ne traite ma demande.",
    "Le conseiller était très peu aimable et n'a pas résolu mon problème.",
    "Trois emails envoyés sans réponse depuis 10 jours. C'est vraiment décevant.",
    "On me renvoie d'un service à l'autre sans jamais résoudre mon problème.",
    "Le chat en ligne déconnecte systématiquement avant la fin de la conversation.",
]

AVIS_POSITIFS = [
    "Livraison ultra rapide, commande passée le lundi reçue le mercredi. Parfait !",
    "Qualité du produit excellente, exactement comme sur les photos. Je recommande.",
    "Service client réactif et agréable. Problème résolu en moins de 24h.",
    "Emballage soigné, produit bien protégé. Rien à redire sur la qualité.",
    "Correspond parfaitement à la description. La taille est exacte.",
    "Très bonne expérience d'achat. Je reviendrai certainement.",
    "Rapport qualité-prix excellent. Je suis vraiment satisfaite de mon achat.",
    "Livraison dans les délais, produit conforme. Tout s'est bien passé.",
    "Superbe qualité, je suis agréablement surprise. Merci !",
    "Commande parfaite du début à la fin. Client fidèle depuis 3 ans et toujours satisfait.",
]


def random_date(start_days_ago: int, end_days_ago: int) -> str:
    days = random.randint(end_days_ago, start_days_ago)
    d = datetime.now() - timedelta(days=days)
    return d.strftime("%Y-%m-%d")


def generate_orders(filename: str, n: int = 500):
    """Génère n commandes réalistes."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "email", "order_id", "total_amount", "refund_amount",
            "status", "product_name", "sku", "order_date"
        ])
        writer.writeheader()

        for i in range(n):
            client = random.choice(CLIENTS)
            produit = random.choice(PRODUITS)
            qty = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
            total = round(produit[2] * qty, 2)

            # 8% de chances de remboursement
            has_refund = random.random() < 0.08
            refund = round(total * random.uniform(0.5, 1.0), 2) if has_refund else 0.0

            status = "refunded" if has_refund else random.choices(
                ["completed", "completed", "completed", "cancelled"],
                weights=[85, 85, 85, 15]
            )[0]

            writer.writerow({
                "email": client,
                "order_id": f"ORD-{1000 + i}",
                "total_amount": total,
                "refund_amount": refund,
                "status": status,
                "product_name": produit[0],
                "sku": produit[1],
                "order_date": random_date(90, 1),
            })

    print(f"✅ {n} commandes générées dans {filename}")


def generate_feedbacks(filename: str, n: int = 200):
    """Génère n feedbacks réalistes."""

    # Distribution des types de feedbacks
    all_feedbacks = (
        [(f, "support_ticket", random.randint(1, 2)) for f in PROBLEMES_LIVRAISON] * 4 +
        [(f, "support_ticket", random.randint(1, 2)) for f in PROBLEMES_PRODUIT] * 3 +
        [(f, "email", random.randint(1, 2)) for f in PROBLEMES_REMBOURSEMENT] * 3 +
        [(f, "support_ticket", random.randint(1, 3)) for f in PROBLEMES_SERVICE] * 2 +
        [(f, "review", random.randint(4, 5)) for f in AVIS_POSITIFS] * 3
    )

    random.shuffle(all_feedbacks)
    selected = all_feedbacks[:n]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "email", "body", "subject", "rating", "channel", "feedback_date"
        ])
        writer.writeheader()

        for body, channel, rating in selected:
            client = random.choice(CLIENTS)
            writer.writerow({
                "email": client,
                "body": body,
                "subject": body[:50] + "...",
                "rating": rating,
                "channel": channel,
                "feedback_date": random_date(60, 1),
            })

    print(f"✅ {n} feedbacks générés dans {filename}")


if __name__ == "__main__":
    generate_orders("demo_orders.csv", 500)
    generate_feedbacks("demo_feedbacks.csv", 200)
    print("\n🎉 Dataset de démo généré !")
    print("   → demo_orders.csv    (500 commandes)")
    print("   → demo_feedbacks.csv (200 feedbacks)")