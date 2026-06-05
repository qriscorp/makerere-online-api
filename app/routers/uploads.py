import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])

UPLOAD_DIR = "/app/uploads"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a file (image). Returns the URL to access it."""
    if current_user.role not in ("super_admin", "admin", "lecturer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and lecturers can upload files",
        )

    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' not allowed. Allowed: JPEG, PNG, GIF, WebP, SVG",
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB.",
        )

    # Generate unique filename
    ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Write file
    with open(filepath, "wb") as f:
        f.write(content)

    # Return the URL path (will be served by static mount)
    return {
        "url": f"/uploads/{filename}",
        "filename": filename,
        "size": len(content),
        "content_type": file.content_type,
    }
