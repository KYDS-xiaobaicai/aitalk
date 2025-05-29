from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    - **username**: 用户名（3-50个字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少6个字符）
    """
    user = AuthService.register_user(db, user_data)
    return user


@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    返回JWT访问令牌
    """
    user = AuthService.authenticate_user(db, login_data.username, login_data.password)
    access_token = AuthService.create_token(user)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login-form", response_model=Token)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录（表单格式）- 用于 OAuth2 兼容
    
    - **username**: 用户名
    - **password**: 密码
    
    返回JWT访问令牌
    """
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    access_token = AuthService.create_token(user)
    return {"access_token": access_token, "token_type": "bearer"} 