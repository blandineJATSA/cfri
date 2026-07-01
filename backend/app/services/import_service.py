"""
Service d'import CSV.

Responsabilités :
- Valider que le fichier est bien un CSV
- Sauvegarder le fichier sur le disque
- Créer l'enregistrement Import en base de données
- Lire et parser le CSV pour créer les feedbacks/commandes/clients
- Déduplication — on ne réimporte pas un feedback déjà existant
"""

import os
import uuid
import hashlib
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Import, ImportType, ImportStatus, Customer, Feedback, Order


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def make_feedback_hash(email: str, body: str) -> str:
    """
    Crée un hash unique pour identifier un feedback.
    Si email + body sont identiques → c'est un doublon.
    """
    content = f"{email.lower().strip()}::{body.strip()}"
    return hashlib.md5(content.encode()).hexdigest()


def save_file(file_content: bytes, filename: str) -> str:
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
    Déduplique automatiquement — un feedback identique n'est jamais importé deux fois.

    Colonnes attendues :
    - email        : email du client (obligatoire)
    - body         : texte du feedback (obligatoire)
    - subject      : sujet (optionnel)
    - rating       : note (optionnel)
    - channel      : canal source (optionnel)
    - feedback_date: date du feedback (optionnel)
    """
    try:
        import_record.status = ImportStatus.processing
        db.commit()

        df = pd.read_csv(import_record.file_path)
        import_record.rows_total = len(df)
        db.commit()

        rows_processed = 0
        rows_skipped = 0  # doublons ignorés

        for _, row in df.iterrows():
            try:
                email = str(row.get("email", "")).strip().lower()
                body = str(row.get("body", "")).strip()

                # Ignorer les feedbacks sans texte
                if not body or body == "nan":
                    continue

                # Ignorer les feedbacks trop courts (moins de 5 mots)
                if len(body.split()) < 5:
                    continue

                # Déduplication — vérifier si ce feedback existe déjà
                feedback_hash = make_feedback_hash(email or "", body)
                existing = db.query(Feedback).filter(
                    Feedback.organization_id == organization_id,
                    Feedback.content_hash == feedback_hash,
                ).first()

                if existing:
                    rows_skipped += 1
                    continue  # Doublon — on skip silencieusement

                # Récupérer ou créer le client
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
                            name=str(row.get("name", "")).strip() or None,
                        )
                        db.add(customer)
                        db.flush()

                # Créer le feedback
                feedback = Feedback(
                    organization_id=organization_id,
                    customer_id=customer.id if customer else None,
                    import_id=import_record.id,
                    body=body,
                    content_hash=feedback_hash,
                    subject=str(row.get("subject", "")).strip() or None,
                    channel=str(row.get("channel", "")).strip() or None,
                    rating=float(row["rating"]) if pd.notna(row.get("rating")) else None,
                    feedback_date=pd.to_datetime(row["feedback_date"]) if pd.notna(row.get("feedback_date")) else None,
                )
                db.add(feedback)
                rows_processed += 1

            except Exception:
                continue

        db.commit()

        import_record.status = ImportStatus.completed
        import_record.rows_processed = rows_processed
        import_record.error_message = f"{rows_skipped} doublons ignorés" if rows_skipped > 0 else None
        import_record.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        import_record.status = ImportStatus.failed
        import_record.error_message = str(e)
        db.commit()


def process_orders_csv(db: Session, import_record: Import, organization_id: str):
    """
    Parse le CSV de commandes.
    Déduplique par external_order_id si présent.

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
        rows_skipped = 0

        for _, row in df.iterrows():
            try:
                email = str(row.get("email", "")).strip().lower()
                external_order_id = str(row.get("order_id", "")).strip() or None

                # Déduplication par order_id si présent
                if external_order_id and external_order_id != "nan":
                    existing = db.query(Order).filter(
                        Order.organization_id == organization_id,
                        Order.external_order_id == external_order_id,
                    ).first()
                    if existing:
                        rows_skipped += 1
                        continue

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

                    amount = float(row.get("total_amount", 0) or 0)
                    customer.total_spent = (customer.total_spent or 0) + amount
                    customer.orders_count = (customer.orders_count or 0) + 1

                order = Order(
                    organization_id=organization_id,
                    customer_id=customer.id if customer else None,
                    external_order_id=external_order_id if external_order_id != "nan" else None,
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
        import_record.error_message = f"{rows_skipped} doublons ignorés" if rows_skipped > 0 else None
        import_record.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        import_record.status = ImportStatus.failed
        import_record.error_message = str(e)
        db.commit()


def delete_import(db: Session, import_id: str, organization_id: str) -> bool:
    """
    Supprime un import et toutes ses données associées.
    Retourne True si supprimé, False si non trouvé.
    """
    from app.models import FeedbackAnalysis

    import_record = db.query(Import).filter(
        Import.id == import_id,
        Import.organization_id == organization_id,
    ).first()

    if not import_record:
        return False

    # Supprimer les analyses des feedbacks de cet import
    feedbacks = db.query(Feedback).filter(
        Feedback.import_id == import_id
    ).all()

    for feedback in feedbacks:
        db.query(FeedbackAnalysis).filter(
            FeedbackAnalysis.feedback_id == feedback.id
        ).delete()

    # Supprimer les feedbacks
    db.query(Feedback).filter(Feedback.import_id == import_id).delete()

    # Supprimer l'import
    db.delete(import_record)
    db.commit()
    return True


def get_imports(db: Session, organization_id: str) -> list[Import]:
    return (
        db.query(Import)
        .filter(Import.organization_id == organization_id)
        .order_by(Import.created_at.desc())
        .all()
    )


def get_import_by_id(db: Session, import_id: str, organization_id: str) -> Import | None:
    return (
        db.query(Import)
        .filter(
            Import.id == import_id,
            Import.organization_id == organization_id,
        )
        .first()
    )