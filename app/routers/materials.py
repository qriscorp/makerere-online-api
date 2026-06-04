from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.study_material import StudyMaterial
from app.schemas.study_material import StudyMaterialCreate, StudyMaterialResponse

router = APIRouter(prefix="/api/materials", tags=["Study Materials"])


@router.get("", response_model=List[StudyMaterialResponse])
def list_materials(
    course_unit_id: str = Query(..., description="Filter by course unit ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List study materials for a course unit. Any authenticated user can access."""
    materials = (
        db.query(StudyMaterial)
        .filter(StudyMaterial.course_unit_id == course_unit_id)
        .order_by(StudyMaterial.created_at.desc())
        .all()
    )
    return materials


@router.post("", response_model=StudyMaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    data: StudyMaterialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a study material. Only lecturer, admin, or super_admin can create."""
    if current_user.role not in ("super_admin", "admin", "lecturer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    material = StudyMaterial(
        course_unit_id=data.course_unit_id,
        title=data.title,
        description=data.description,
        type=data.type,
        file_url=data.file_url,
        file_size=data.file_size,
        uploaded_by=current_user.id,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a study material. Owner or admin can delete."""
    material = db.query(StudyMaterial).filter(StudyMaterial.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    if current_user.role not in ("super_admin", "admin") and material.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    db.delete(material)
    db.commit()
    return None
