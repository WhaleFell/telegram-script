#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time : 2023/1/31 10:05
# @Author : zxiaosi
# @desc : 全局异常捕获
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from urllib.parse import parse_qsl

# ALL Exception
from starlette.exceptions import (
    HTTPException as StarletteHTTPException,
)

from sqlalchemy.exc import SQLAlchemyError
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

from app.utils.custom_log import logger
from app.schemas import BaseResp

from typing import Optional, Any


async def get_request_params(request: Request) -> dict:
    """获取请求参数"""
    params: dict = {}  # 存储结果

    path_params = request.get("path_params")  # 路径参数
    if path_params:
        params.update(path_params)

    query_string = request.get("query_string")
    if query_string:
        query_params = parse_qsl(str(query_string, "utf-8"))  # 查询参数
        params.update(query_params)

    methods = ["POST", "PUT", "PATCH"]
    content_type = request.headers.get("content-type")
    if request.method in methods and "application/json" in content_type:  # type: ignore
        # "request.json()" hangs indefinitely in middleware
        # no way fix now: https://github.com/tiangolo/fastapi/issues/5386

        # body_params = await request.json()  # 请求体参数
        # body_params = await request.
        # params.update(body_params)
        pass

    return params


def response_body(
    request: Request,
    content: Any = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> ORJSONResponse:
    """返回响应体"""

    response = {
        "content": content,
        "status_code": status_code,
        "headers": {  # 解决跨域问题(仿照500错误的响应头)
            "access-control-allow-origin": request.headers.get("origin") or "*",
            "access-control-allow-credentials": "true",
            "content-type": "application/json",
            "vary": "Origin",
        },
    }

    return ORJSONResponse(**jsonable_encoder(response))


def register_exception(app: FastAPI):
    """
    全局异常捕获 -- https://fastapi.tiangolo.com/tutorial/handling-errors/
    starlette 服务器在返回500时删除了请求头信息, 从而导致了cors跨域问题, 前端无法获取到响应头信息
    详见: https://github.com/encode/starlette/issues/1175#issuecomment-1225519424
    """

    @app.exception_handler(SQLAlchemyError)
    async def validation_exception_handler(  # type: ignore
        request: Request, exc: SQLAlchemyError
    ) -> ORJSONResponse:
        """SQLAlchemy错误"""
        params = await get_request_params(request)
        logger.error(
            f"SQL ERROR:{exc} URL:{request.url} Request Parameter:{params}"
        )

        return response_body(
            request=request,
            content=BaseResp(code=500, msg=f"SQL ERROR:{exc}").model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(  # type: ignore
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        """请求参数验证错误"""
        logger.error(
            f"Requests Validation Error:{exc} URL:{request.url} Request Parameter:{await get_request_params(request)}"
        )

        return response_body(
            request=request,
            content=BaseResp(
                code=500, msg=f"Requests Validation Error:{exc}"
            ).model_dump(),
        )

    # @app.exception_handler(HTTPException)
    # async def http_exception_handler(  # type: ignore
    #     request: Request, exc: HTTPException
    # ) -> ORJSONResponse:
    #     """HTTP通信错误"""
    #     logger.error(f"HTTP Error:{exc} URL:{request.url}")

    #     return ORJSONResponse(
    #         BaseResp(code=500, msg=f"HTTP Error:{exc}").model_dump()
    #     )

    @app.exception_handler(Exception)
    async def http_exception_handler(
        request: Request, exc: Exception
    ) -> ORJSONResponse:
        """全局异常"""
        logger.exception(f"Global Error: {exc} URL:{request.url}")

        return response_body(
            request=request,
            content=BaseResp(code=500, msg=f"Global Error:{exc}").model_dump(),
        )
