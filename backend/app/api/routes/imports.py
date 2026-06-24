"""
Routes FastAPI pour l'import de fichiers CSV.

Endpoints :
- POST /imports/feedbacks  → upload un CSV de feedbacks
- POST /imports/orders     → upload un CSV de commandes
- GET  /imports            → liste tous les imports
- GET  /imports/{id}       → détail d'un import
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.import_schema import ImportResponse, ImportListResponse
from app.models import ImportType
from app.services import import_service

router = APIRouter(prefix="/imports", tags=["Imports"])

# Pour le MVP on utilise un organization_id fixe
# En V1 il viendra du token d'authentification
DEMO_ORG_ID = "00000000-0000-0000-0000-000000000001"


@router.post("/feedbacks", response_model=ImportResponse)
async def upload_feedbacks(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Reçoit un fichier CSV de feedbacks.
    Valide le format, sauvegarde, parse et crée les feedbacks en base.

    Colonnes attendues : email, body, subject, rating, channel, feedback_date
    """
    # Vérifier que c'est bien un CSV
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format CSV"
        )

    # Lire le contenu du fichier
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Le fichier est vide"
        )

    # Sauvegarder le fichier sur le disque
    file_path = import_service.save_file(content, file.filename)

    # Créer l'enregistrement en base
    import_record = import_service.create_import_record(
        db=db,
        organization_id=DEMO_ORG_ID,
        import_type=ImportType.feedbacks,
        filename=file.filename,
        file_path=file_path,
    )

    # Traiter le CSV directement pour le MVP
    # En V1 on enverra un job Redis à la place
    import_service.process_feedbacks_csv(
        db=db,
        import_record=import_record,
        organization_id=DEMO_ORG_ID,
    )

    # Recharger depuis la base pour avoir le statut final
    db.refresh(import_record)
    return import_record


@router.post("/orders", response_model=ImportResponse)
async def upload_orders(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Reçoit un fichier CSV de commandes.
    Colonnes attendues : email, total_amount, order_date, refund_amount, status, product_name
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format CSV"
        )

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Le fichier est vide"
        )

    file_path = import_service.save_file(content, file.filename)

    import_record = import_service.create_import_record(
        db=db,
        organization_id=DEMO_ORG_ID,
        import_type=ImportType.orders,
        filename=file.filename,
        file_path=file_path,
    )

    import_service.process_orders_csv(
        db=db,
        import_record=import_record,
        organization_id=DEMO_ORG_ID,
    )

    db.refresh(import_record)
    return import_record


@router.get("", response_model=ImportListResponse)
def list_imports(db: Session = Depends(get_db)):
    """Retourne tous les imports de l'organisation."""
    imports = import_service.get_imports(db, DEMO_ORG_ID)
    return ImportListResponse(imports=imports, total=len(imports))


@router.get("/{import_id}", response_model=ImportResponse)
def get_import(import_id: str, db: Session = Depends(get_db)):
    """Retourne le détail d'un import spécifique."""
    import_record = import_service.get_import_by_id(db, import_id, DEMO_ORG_ID)
    if not import_record:
        raise HTTPException(status_code=404, detail="Import non trouvé")
    return import_record