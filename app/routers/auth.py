from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import hashlib
import secrets
import random
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.models.registration_verification import RegistrationVerification
from app.schemas.user import (
    UserLogin,
    UserResponse,
    Token,
    ProfileUpdate,
    PasswordChange,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetTokenValidationResponse,
    RegisterRequest,
    RegisterResponse,
    VerifyEmailRequest,
    ResendVerificationRequest,
)
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.config import settings
from app.email import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

RESET_MESSAGE = (
    "If an account exists for that email address, "
    "you will receive a password reset link shortly."
)


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _hash_verification_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode()).hexdigest()


def _generate_verification_code() -> str:
    return f"{random.randint(0, 999999):06d}"


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    """Public student self-registration. Sends email verification code before account is created."""
    email = str(user_data.email).strip().lower()
    name = user_data.name.strip()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required",
        )

    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    db.query(RegistrationVerification).filter(
        RegistrationVerification.email == email
    ).delete(synchronize_session=False)

    code = _generate_verification_code()
    pending = RegistrationVerification(
        name=name,
        email=email,
        hashed_password=hash_password(user_data.password),
        code_hash=_hash_verification_code(code),
        expires_at=datetime.utcnow()
        + timedelta(minutes=settings.email_verification_expire_minutes),
    )
    db.add(pending)
    db.commit()

    emailed = send_verification_email(email, name, code)
    dev_code = code if not emailed else None

    return RegisterResponse(
        message="A verification code has been sent to your email address.",
        email=email,
        verification_required=True,
        dev_code=dev_code,
    )


@router.post("/verify-email", response_model=Token)
def verify_email(data: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Confirm email with verification code and create the student account."""
    email = str(data.email).strip().lower()
    code = data.code.strip().replace(" ", "")

    if len(code) != 6 or not code.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter the 6-digit verification code",
        )

    pending = (
        db.query(RegistrationVerification)
        .filter(RegistrationVerification.email == email)
        .first()
    )
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending registration found. Please register again.",
        )

    if pending.expires_at < datetime.utcnow():
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired. Please register again.",
        )

    if pending.attempts >= settings.email_verification_max_attempts:
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many failed attempts. Please register again.",
        )

    if _hash_verification_code(code) != pending.code_hash:
        pending.attempts += 1
        db.commit()
        remaining = settings.email_verification_max_attempts - pending.attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification code. {remaining} attempt(s) remaining.",
        )

    if db.query(User).filter(User.email == email).first():
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        name=pending.name,
        email=pending.email,
        hashed_password=pending.hashed_password,
        role="student",
    )
    db.add(user)
    db.delete(pending)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/resend-verification", response_model=RegisterResponse)
def resend_verification(data: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Resend the email verification code for a pending registration."""
    email = str(data.email).strip().lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please sign in.",
        )

    pending = (
        db.query(RegistrationVerification)
        .filter(RegistrationVerification.email == email)
        .first()
    )
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending registration found. Please register again.",
        )

    code = _generate_verification_code()
    pending.code_hash = _hash_verification_code(code)
    pending.expires_at = datetime.utcnow() + timedelta(
        minutes=settings.email_verification_expire_minutes
    )
    pending.attempts = 0
    db.commit()

    emailed = send_verification_email(email, pending.name, code)

    return RegisterResponse(
        message="A new verification code has been sent to your email.",
        email=email,
        verification_required=True,
        dev_code=code if not emailed else None,
    )


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    email = str(credentials.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the logged-in user's profile (name and/or email)."""
    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name cannot be empty",
            )
        current_user.name = name

    if data.email is not None:
        email = str(data.email).strip().lower()
        existing = (
            db.query(User)
            .filter(User.email == email, User.id != current_user.id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        current_user.email = email

    if data.name is None and data.email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the logged-in user's password."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return None


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request a password reset link. Always returns the same message (no email enumeration)."""
    email = str(data.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()

    reset_url: str | None = None
    email_sent = False

    if user:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).delete(synchronize_session=False)

        raw_token = secrets.token_urlsafe(32)
        token_record = PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_reset_token(raw_token),
            expires_at=datetime.utcnow()
            + timedelta(minutes=settings.password_reset_expire_minutes),
        )
        db.add(token_record)
        db.commit()

        reset_url = f"{settings.frontend_url.rstrip('/')}/reset-password?token={raw_token}"
        email_sent = send_password_reset_email(user.email, user.name, reset_url)
        if email_sent:
            reset_url = None

    return ForgotPasswordResponse(
        message=RESET_MESSAGE,
        reset_url=reset_url,
        email_sent=email_sent,
    )


@router.get("/reset-password/validate", response_model=ResetTokenValidationResponse)
def validate_reset_token(token: str, db: Session = Depends(get_db)):
    """Check whether a reset token is still valid before showing the reset form."""
    token_hash = _hash_reset_token(token)
    record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not record:
        return ResetTokenValidationResponse(valid=False)

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        return ResetTokenValidationResponse(valid=False)

    return ResetTokenValidationResponse(valid=True, email=user.email)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Set a new password using a valid reset token."""
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )

    token_hash = _hash_reset_token(data.token)
    record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset link",
        )

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset link",
        )

    user.hashed_password = hash_password(data.new_password)
    record.used_at = datetime.utcnow()
    db.commit()
    return None
