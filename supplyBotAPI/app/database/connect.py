#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# curd/connect.py
# 数据库连接

from typing import AsyncIterator  # 异步迭代器
from typing_extensions import Annotated
from sqlalchemy.exc import SQLAlchemyError  # sqlalchemy error
from app.utils.custom_log import logger
from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    async_sessionmaker,
    AsyncSession,
    create_async_engine,
)
from app.config import settings

# reference: https://fastapi.tiangolo.com/tutorial/sql-databases/#note
# is needed only for SQLite. It's not needed for other databases.
# connect_args={"check_same_thread": False}


async_engine = create_async_engine(
    url=settings.DATABASE_URI,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=600,
    future=True,
)

# 在引擎初始化时指定 echo=True 将使我们能够在控制台中看到生成的 SQL 查询。我们应该使用 expire_on_commit=False 禁用会话的“提交时过期”行为。这是因为在异步设置中，我们不希望 SQLAlchemy 在访问已提交的对象时向数据库发出新的 SQL 查询。
AsyncSessionMaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    async_engine, expire_on_commit=False
)


# FastAPI Dependent
async def get_session() -> AsyncSession:
    async with AsyncSessionMaker() as session:
        yield session  # type: ignore
