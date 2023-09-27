#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# register/cors.py 处理跨域请求

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.config import settings


def register_cors(app: FastAPI):
    """跨域请求 -- https://fastapi.tiangolo.com/zh/tutorial/cors/"""

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
