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


def get_field(row, field: str, mapping: dict = None) -> str:
    """Récupère la valeur d'un champ en tenant compte du mapping."""
    if mapping and mapping.get(field):
        return str(row.get(mapping[field], ""))
    return str(row.get(field, ""))


def process_feedbacks_csv(
    db: Session,
    import_record: Import,
    organization_id: str,
    column_mapping: dict = None,
):
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
                email = get_field(row, "email", column_mapping).strip().lower()
                body = get_field(row, "body", column_mapping).strip()

                # Ignorer les feedbacks sans texte
                if not body or body == "nan":
                    continue

                # Ignorer les feedbacks trop courts
                if len(body.split()) < 5:
                    continue

                # Déduplication
                feedback_hash = make_feedback_hash(email or "", body)
                existing = db.query(Feedback).filter(
                    Feedback.organization_id == organization_id,
                    Feedback.content_hash == feedback_hash,
                ).first()

                if existing:
                    rows_skipped += 1
                    continue

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
                            name=get_field(row, "name", column_mapping).strip() or None,
                        )
                        db.add(customer)
                        db.flush()

                # Récupérer les champs optionnels avec mapping
                subject = get_field(row, "subject", column_mapping).strip() or None
                if subject == "nan":
                    subject = None

                channel = get_field(row, "channel", column_mapping).strip() or None
                if channel == "nan":
                    channel = None

                # Rating — champ numérique
                raw_rating = row.get(column_mapping.get("rating") if column_mapping else "rating")
                rating = float(raw_rating) if pd.notna(raw_rating) else None

                # Date — champ datetime
                raw_date = row.get(column_mapping.get("feedback_date") if column_mapping else "feedback_date")
                feedback_date = pd.to_datetime(raw_date) if pd.notna(raw_date) else None

                # Créer le feedback
                feedback = Feedback(
                    organization_id=organization_id,
                    customer_id=customer.id if customer else None,
                    import_id=import_record.id,
                    body=body,
                    content_hash=feedback_hash,
                    subject=subject,
                    channel=channel,
                    rating=rating,
                    feedback_date=feedback_date,
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

# ── Mapping de colonnes ──────────────────────────────────────────────────────

FEEDBACK_SYNONYMS = {
    "email": ["email", "requester_email", "customer_email", "mail", "e-mail", "from_email", "user_email", "courriel"],
    "body": ["body", "description", "message", "content", "text", "comment", "feedback", "ticket_body", "texte", "contenu", "commentaire"],
    "subject": ["subject", "title", "objet", "titre", "topic", "sujet", "summary"],
    "rating": ["rating", "note", "score", "satisfaction", "nps", "stars", "etoiles", "grade"],
    "channel": ["channel", "source", "canal", "via", "type", "origin", "origine"],
    "feedback_date": ["feedback_date", "created_at", "date", "timestamp", "submitted_at", "opened_at", "date_creation", "created", "date_created"],
}

ORDER_SYNONYMS = {
    "email": ["email", "customer_email", "requester_email", "mail", "e-mail", "buyer_email"],
    "total_amount": ["total_amount", "amount", "total", "price", "montant", "order_total", "subtotal", "revenue"],
    "order_date": ["order_date", "date", "created_at", "timestamp", "purchase_date", "ordered_at", "date_commande"],
    "refund_amount": ["refund_amount", "refund", "remboursement", "refunded", "refund_total"],
    "status": ["status", "statut", "state", "etat", "order_status"],
    "product_name": ["product_name", "product", "item", "produit", "name", "article", "sku_name"],
    "order_id": ["order_id", "id", "order_number", "numero_commande", "reference", "ref", "external_id"],
}


def suggest_mapping(columns: list[str], synonyms: dict) -> dict:
    """
    Suggère automatiquement un mapping entre les colonnes du fichier
    et les colonnes attendues par CFRI.
    
    Retourne un dict : { "colonne_cfri": "colonne_fichier" ou None }
    """
    columns_lower = {col.lower().strip(): col for col in columns}
    mapping = {}

    for cfri_field, synonyms_list in synonyms.items():
        matched = None
        for synonym in synonyms_list:
            if synonym in columns_lower:
                matched = columns_lower[synonym]
                break
        mapping[cfri_field] = matched

    return mapping


def preview_csv(file_content: bytes, import_type: str) -> dict:
    """
    Lit le CSV, détecte les colonnes, suggère le mapping.
    Retourne un aperçu des premières lignes + le mapping suggéré.
    """
    import io

    try:
        # Détecter l'encodage
        try:
            df = pd.read_csv(io.BytesIO(file_content), nrows=5, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_content), nrows=5, encoding="latin-1")

        columns = list(df.columns)
        synonyms = FEEDBACK_SYNONYMS if import_type == "feedbacks" else ORDER_SYNONYMS

        mapping = suggest_mapping(columns, synonyms)

        # Aperçu des 3 premières lignes
        preview_rows = df.head(3).fillna("").to_dict(orient="records")

        # Colonnes obligatoires manquantes
        required = ["email", "body"] if import_type == "feedbacks" else ["email", "total_amount"]
        missing_required = [field for field in required if mapping.get(field) is None]

        return {
            "columns": columns,
            "mapping": mapping,
            "preview_rows": preview_rows,
            "missing_required": missing_required,
            "can_import": len(missing_required) == 0,
            "total_rows": None,  # On ne lit pas tout le fichier pour le preview
        }

    except Exception as e:
        raise ValueError(f"Impossible de lire le fichier CSV : {str(e)}")