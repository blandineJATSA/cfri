"""
Service d'import CSV.

Responsabilités :
- Valider que le fichier est bien un CSV
- Sauvegarder le fichier sur le disque
- Créer l'enregistrement Import en base de données
- Lire et parser le CSV pour créer les feedbacks/commandes/clients
"""

import os
import uuid
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Import, ImportType, ImportStatus, Customer, Feedback, Order


# Dossier où on stocke les fichiers uploadés
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_file(file_content: bytes, filename: str) -> str:
    """
    Sauvegarde le fichier sur le disque.
    Retourne le chemin du fichier sauvegardé.
    On ajoute un UUID pour éviter les conflits de noms.
    """
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as f:
        f.write(file_content)
    return file_path


def create_import_record(
    db: Session,
    organization_id: str,
    import_type: ImportType,
    filename: str,
    file_path: str,
) -> Import:
    """
    Crée l'enregistrement Import en base avec status 'pending'.
    Le worker va ensuite le passer à 'processing' puis 'completed'.
    """
    import_record = Import(
        organization_id=organization_id,
        type=import_type,
        filename=filename,
        file_path=file_path,
        status=ImportStatus.pending,
    )
    db.add(import_record)
    db.commit()
    db.refresh(import_record)
    return import_record


def process_feedbacks_csv(db: Session, import_record: Import, organization_id: str):
    """
    Parse le CSV de feedbacks et crée les enregistrements en base.

    Colonnes attendues dans le CSV :
    - email        : email du client (obligatoire)
    - body         : texte du feedback (obligatoire)
    - subject      : sujet (optionnel)
    - rating       : note (optionnel)
    - channel      : canal source (optionnel)
    - feedback_date: date du feedback (optionnel)
    """
    try:
        # Passer le status à 'processing'
        import_record.status = ImportStatus.processing
        db.commit()

        # Lire le CSV avec pandas
        df = pd.read_csv(import_record.file_path)
        import_record.rows_total = len(df)
        db.commit()

        rows_processed = 0

        for _, row in df.iterrows():
            try:
                # Récupérer ou créer le client
                email = str(row.get("email", "")).strip().lower()
                customer = None

                if email and email != "nan":
                    # Chercher si le client existe déjà
                    customer = db.query(Customer).filter(
                        Customer.organization_id == organization_id,
                        Customer.email == email,
                    ).first()

                    # Sinon le créer
                    if not customer:
                        customer = Customer(
                            organization_id=organization_id,
                            email=email,
                            name=str(row.get("name", "")).strip() or None,
                        )
                        db.add(customer)
                        db.flush()  # Pour obtenir l'ID sans committer

                # Créer le feedback
                body = str(row.get("body", "")).strip()
                if not body or body == "nan":
                    continue  # On ignore les feedbacks sans texte

                feedback = Feedback(
                    organization_id=organization_id,
                    customer_id=customer.id if customer else None,
                    import_id=import_record.id,
                    body=body,
                    subject=str(row.get("subject", "")).strip() or None,
                    channel=str(row.get("channel", "")).strip() or None,
                    rating=float(row["rating"]) if pd.notna(row.get("rating")) else None,
                    feedback_date=pd.to_datetime(row["feedback_date"]) if pd.notna(row.get("feedback_date")) else None,
                )
                db.add(feedback)
                rows_processed += 1

            except Exception:
                continue  # On ignore les lignes avec erreurs

        db.commit()

        # Mettre à jour le statut
        import_record.status = ImportStatus.completed
        import_record.rows_processed = rows_processed
        import_record.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        import_record.status = ImportStatus.failed
        import_record.error_message = str(e)
        db.commit()


def process_orders_csv(db: Session, import_record: Import, organization_id: str):
    """
    Parse le CSV de commandes.

    Colonnes attendues :
    - email         : email du client (obligatoire)
    - total_amount  : montant de la commande (obligatoire)
    - order_date    : date de la commande (optionnel)
    - refund_amount : montant remboursé (optionnel)
    - status        : statut de la commande (optionnel)
    - product_name  : nom du produit (optionnel)
    - order_id      : ID externe (optionnel)
    """
    try:
        import_record.status = ImportStatus.processing
        db.commit()

        df = pd.read_csv(import_record.file_path)
        import_record.rows_total = len(df)
        db.commit()

        rows_processed = 0

        for _, row in df.iterrows():
            try:
                email = str(row.get("email", "")).strip().lower()
                customer = None

                if email and email != "nan":
                    customer = db.query(Customer).filter(
                        Customer.organization_id == organization_id,
                        Customer.email == email,
                    ).first()

                    if not customer:
                        customer = Customer(
                            organization_id=organization_id,
                            email=email,
                        )
                        db.add(customer)
                        db.flush()

                    # Mettre à jour les stats du client
                    amount = float(row.get("total_amount", 0) or 0)
                    customer.total_spent = (customer.total_spent or 0) + amount
                    customer.orders_count = (customer.orders_count or 0) + 1

                order = Order(
                    organization_id=organization_id,
                    customer_id=customer.id if customer else None,
                    external_order_id=str(row.get("order_id", "")).strip() or None,
                    total_amount=float(row.get("total_amount", 0) or 0),
                    refund_amount=float(row.get("refund_amount", 0) or 0),
                    status=str(row.get("status", "")).strip() or None,
                    product_name=str(row.get("product_name", "")).strip() or None,
                    order_date=pd.to_datetime(row["order_date"]) if pd.notna(row.get("order_date")) else None,
                )
                db.add(order)
                rows_processed += 1

            except Exception:
                continue

        db.commit()

        import_record.status = ImportStatus.completed
        import_record.rows_processed = rows_processed
        import_record.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        import_record.status = ImportStatus.failed
        import_record.error_message = str(e)
        db.commit()


def get_imports(db: Session, organization_id: str) -> list[Import]:
    """Retourne tous les imports d'une organisation, du plus récent au plus ancien."""
    return (
        db.query(Import)
        .filter(Import.organization_id == organization_id)
        .order_by(Import.created_at.desc())
        .all()
    )


def get_import_by_id(db: Session, import_id: str, organization_id: str) -> Import | None:
    """Retourne un import spécifique."""
    return (
        db.query(Import)
        .filter(
            Import.id == import_id,
            Import.organization_id == organization_id,
        )
        .first()
    )