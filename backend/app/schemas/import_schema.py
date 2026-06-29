from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ImportResponse(BaseModel):
    """
    Ce que l'API retourne quand on parle d'un import.
    Pydantic valide automatiquement que les données ont le bon type.
    """
    id: str
    type: str
    filename: str
    status: str
    rows_total: int
    rows_processed: int
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ImportListResponse(BaseModel):
    """Liste d'imports avec le total."""
    imports: list[ImportResponse]
    total: int