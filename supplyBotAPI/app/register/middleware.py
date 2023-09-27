#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# register/middleware.py 中间件

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
import time


def register_middleware(app: FastAPI):
    """请求拦截与响应拦截 -- https://fastapi.tiangolo.com/tutorial/middleware/"""

    @app.middleware("http")
    async def intercept(request: Request, call_next) -> Response:
        """
        intercept /ˌɪn.təˈsept/ v. 拦截
        使用了自定义路由 APIRoute 的 Class 会导致
        在这里获取 request.body() 出现了问题...
        https://fastapi.tiangolo.com/advanced/custom-request-and-route/#custom-apiroute-class-in-a-router
        """

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
