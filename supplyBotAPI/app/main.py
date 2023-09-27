#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py


import uvicorn
from fastapi import FastAPI
import asyncio
from app.database import init_table

from app.config import settings
from app.register import (
    register_cors,
    register_router,
    register_exception,
    register_middleware,
)
from app.utils.custom_log import logger

# Optimize Python Aysncio
# to fix: ValueError: too many file descriptors in select()
# reference: https://blog.csdn.net/qq_36759224/article/details/123084133
import selectors
import asyncio
import sys

if sys.platform == "win32":
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    selector = selectors.PollSelector()
    loop = asyncio.SelectorEventLoop(selector)
    asyncio.set_event_loop(loop)

app = FastAPI(
    description=settings.PROJECT_DESC, version=settings.PROJECT_VERSION
)

# register
register_cors(app)  # 注册跨域请求
register_router(app)  # 注册路由
register_exception(app)  # 注册异常捕获
register_middleware(app)  # 注册请求响应拦截


try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_table(is_drop=False))
except Exception as e:
    # run with uvicorn add the async function to main event loop
    logger.info(f"run in uvicorn {e}")
    asyncio.ensure_future(init_table(is_drop=False))

logger.info("The FastAPI Start Success!")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
