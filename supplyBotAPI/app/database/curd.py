#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# curd/curd.py
# 数据库操作

from .connect import AsyncSessionMaker
from .model import User
from typing import Optional, List, Sequence, Union

# sqlalchemy type
from sqlalchemy import (
    ForeignKey,
    func,
    select,
    update,
    String,
    DateTime,
)

from sqlalchemy.ext.asyncio import AsyncSession

# generate AsyncSession in function

# async def getUserByID(user_id: int) -> Optional[User]:
#     async with AsyncSessionMaker() as session:
#         result = await session.get(User, ident=user_id)
#         return result
# async def registerUser(user: User) -> User:
#     async with AsyncSessionMaker() as session:
#         pass


async def getUserByID(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.get(User, ident=user_id)
    return result


async def registerUser(session: AsyncSession, user: User) -> Optional[User]:
    """注册用户,并返回注册后的用户"""
    session.add(user)
    await session.commit()
    # 刷新（以便它包含数据库中的任何新数据，例如生成的 ID）。
    # reference: https://fastapi.tiangolo.com/tutorial/sql-databases/#create-data
    await session.refresh(user)
    return user


async def dumpUsers(session: AsyncSession) -> Union[Sequence[User], List]:
    result = await session.execute(select(User))
    return result.scalars().all()


async def authenticateUser(
    session: AsyncSession, username: str, password: str
) -> Union[bool, User]:
    """验证一个用户
    authenticate /ɔːˈθen.tɪ.keɪt/ v. 验证
    """
    result = await session.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if user:
        if user.password == password:
            return user

    return False
