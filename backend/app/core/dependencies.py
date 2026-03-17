from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token
from app.core.config import db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Dependency: lấy user hiện tại từ JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    from bson import ObjectId
    user = await db.get_db()["users"].find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception

    user["_id"] = str(user["_id"])
    user.pop("password", None)
    return user


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency: chỉ cho phép user có role='admin'."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không có quyền truy cập. Yêu cầu quyền Admin."
        )
    return current_user
