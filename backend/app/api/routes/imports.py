from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.import_schema import ImportResponse, ImportListResponse
from app.models import ImportType
from app.services import import_service
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.post("/feedbacks", response_model=ImportResponse)
async def upload_feedbacks(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format CSV")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Le fichier est vide")

    org_id = current_user["organization_id"]
    file_path = import_service.save_file(content, file.filename)

    import_record = import_service.create_import_record(
        db=db,
        organization_id=org_id,
        import_type=ImportType.feedbacks,
        filename=file.filename,
        file_path=file_path,
    )

    import_service.process_feedbacks_csv(
        db=db,
        import_record=import_record,
        organization_id=org_id,
    )

    db.refresh(import_record)
    return import_record


@router.post("/orders", response_model=ImportResponse)
async def upload_orders(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format CSV")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Le fichier est vide")

    org_id = current_user["organization_id"]
    file_path = import_service.save_file(content, file.filename)

    import_record = import_service.create_import_record(
        db=db,
        organization_id=org_id,
        import_type=ImportType.orders,
        filename=file.filename,
        file_path=file_path,
    )

    import_service.process_orders_csv(
        db=db,
        import_record=import_record,
        organization_id=org_id,
    )

    db.refresh(import_record)
    return import_record


@router.get("", response_model=ImportListResponse)
def list_imports(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    imports = import_service.get_imports(db, current_user["organization_id"])
    return ImportListResponse(imports=imports, total=len(imports))


@router.get("/{import_id}", response_model=ImportResponse)
def get_import(
    import_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    import_record = import_service.get_import_by_id(
        db, import_id, current_user["organization_id"]
    )
    if not import_record:
        raise HTTPException(status_code=404, detail="Import non trouvé")
    return import_record


@router.post("/preview/{import_type}")
async def preview_import(
    import_type: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Analyse le CSV et retourne les colonnes détectées + mapping suggéré.
    Ne crée rien en base — c'est juste une prévisualisation.
    """
    if import_type not in ["feedbacks", "orders"]:
        raise HTTPException(status_code=400, detail="Type d'import invalide")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format CSV")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Le fichier est vide")

    try:
        result = import_service.preview_csv(content, import_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/feedbacks/with-mapping")
async def upload_feedbacks_with_mapping(
    file: UploadFile = File(...),
    mapping: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Import feedbacks avec un mapping de colonnes personnalisé.
    Le mapping est un JSON string : {"email": "requester_email", "body": "description", ...}
    """
    import json

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format CSV")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Le fichier est vide")

    column_mapping = json.loads(mapping) if mapping else None
    org_id = current_user["organization_id"]
    file_path = import_service.save_file(content, file.filename)

    import_record = import_service.create_import_record(
        db=db,
        organization_id=org_id,
        import_type=ImportType.feedbacks,
        filename=file.filename,
        file_path=file_path,
    )

    import_service.process_feedbacks_csv(
        db=db,
        import_record=import_record,
        organization_id=org_id,
        column_mapping=column_mapping,
    )

    db.refresh(import_record)
    return import_record


@router.delete("/{import_id}")
def delete_import(
    import_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Supprime un import et toutes ses données associées."""
    success = import_service.delete_import(
        db, import_id, current_user["organization_id"]
    )
    if not success:
        raise HTTPException(status_code=404, detail="Import non trouvé")
    return {"message": "Import supprimé"}