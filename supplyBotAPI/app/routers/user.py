#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# user router 用户路由

"""
Reference:

Annotated 参数:
- https://fastapi.tiangolo.com/tutorial/body-multiple-params/#singular-values-in-body

OAuth2 validate security:
- https://fastapi.tiangolo.com/tutorial/security/
"""

from fastapi import APIRouter, HTTPException, status
from fastapi import Query, Body, Depends, Form
from app.schemas import UserResp, BMUser, Token
from typing_extensions import Annotated
from typing import List, Optional, Union, Dict
from datetime import timedelta, datetime
from app.config import settings

from app.utils.custom_log import logger

# database
from app.database import User
from app.database.curd import (
    registerUser,
    getUserByID,
    dumpUsers,
    authenticateUser,
)
from app.database.connect import get_session
from sqlalchemy.ext.asyncio import AsyncSession

# security n.安全
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/token/")


@router.post("/register/", tags=["user"], response_model=UserResp)
async def register(
    username: Annotated[str, Body(title="用户名", description="注册的用户名")],
    password: Annotated[
        str, Body(title="明文密码", description="明文密码 show password")
    ],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> UserResp:
    """注册用户并返回注册后的用户对象"""
    user = await registerUser(
        session=db, user=User(username=username, password=password)
    )
    return UserResp(code=200, msg="注册成功", content=BMUser.model_validate(user))


@router.get("/dumps/", tags=["user"], response_model=List[BMUser])
async def dump_users(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> List[BMUser]:
    """导出所有用户"""
    users = await dumpUsers(session=db)

    return [BMUser.model_validate(user) for user in users]


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.OAUTH2_SECRET, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def resolve_user_id(string: Optional[str]) -> Optional[int]:
    if string:
        return int(string.replace("user_id:", ""))

    return None


@router.post("/token/", response_model=Token)
async def login_get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Token:
    user = await authenticateUser(
        session=db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # The important thing to have in mind is that the sub key should have a unique identifier
    # across the entire application, and it should be a string.
    access_token = create_access_token(
        data={"sub": f"user_id:{user.id}"},  # type: ignore
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me/", response_model=BMUser, description="根据 token 获取用户对象")
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> BMUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload: Dict[str, str] = jwt.decode(
            token, settings.OAUTH2_SECRET, algorithms=settings.ALGORITHM
        )
        user_id_raw: Optional[str] = payload.get("sub")
        user_id: Optional[int] = resolve_user_id(user_id_raw)
        if user_id is None:
            logger.error("User not found!")
            raise credentials_exception
    except JWTError as exc:
        logger.exception(f"parser token error:{exc}")
        raise credentials_exception

    user = await getUserByID(session=db, user_id=user_id)
    if user is None:
        raise credentials_exception

    return BMUser.model_validate(user)
