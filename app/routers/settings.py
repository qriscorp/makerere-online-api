from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.system_setting import SystemSetting
from app.models.user import User
from app.schemas.settings import SettingsUpdate, SettingsResponse

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all system settings as key-value dict. Only super_admin and admin can access."""
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    rows = db.query(SystemSetting).all()
    settings_dict = {row.key: row.value for row in rows}
    return SettingsResponse(settings=settings_dict)


@router.put("", response_model=SettingsResponse)
def update_settings(
    payload: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk update system settings. Only super_admin can update."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admin can update settings",
        )

    for key, value in payload.settings.items():
        existing = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if existing:
            existing.value = value
        else:
            setting = SystemSetting(key=key, value=value)
            db.add(setting)

    db.commit()

    # Return all settings after update
    rows = db.query(SystemSetting).all()
    settings_dict = {row.key: row.value for row in rows}
    return SettingsResponse(settings=settings_dict)
