#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# register/router.py 注册路由

from fastapi import FastAPI, Depends

from app.config import settings
from app.routers import index, user


def register_router(app: FastAPI):
    """注册路由"""

    # app.include_router(
    #     public.router, prefix=settings.API_PREFIX, tags=["Public"]
    # )

    app.include_router(index.router, tags=["index"])
    app.include_router(user.router, tags=["user"], prefix="/user")
