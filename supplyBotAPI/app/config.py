#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# config.py 配置文件

import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


# 应用路径
ROOTPATH: Path = Path().absolute().parent


# https://docs.pydantic.dev/usage/settings/
class Settings(BaseSettings):
    PROJECT_DESC: str = "🎉 接口汇总 🎉"  # 描述
    PROJECT_VERSION: str = "1.0"  # 版本

    STATIC_DIR: str = "static"  # 静态文件目录
    BASE_URL: AnyHttpUrl = "http://127.0.0.1:8000"  # type: ignore # 开发环境(为了存放图片全路径)
    API_PREFIX: str = "/api/"

    # 跨域请求(务必指定精确ip, 不要用localhost)
    CORS_ORIGINS: Union[List[AnyHttpUrl], List[str]] = ["*"]

    MD5_SALT: str = "9iJvchvS"  # md5 加密盐
    COOKIE_KEY: str = "sessionId"  # Cookie key name
    COOKIE_MAX_AGE: int = 24 * 60 * 60  # Cookie 有效时间
    COOKIE_NOT_CHECK: List[str] = [
        "/api/user/login",
        "/api/user/signup",
    ]  # 不校验 Cookie

    # OAuth2 Secret openssl rand -hex 32
    OAUTH2_SECRET: str = (
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    ALGORITHM: str = "HS256"  # algorithm n. 算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 9000  # 过期时间

    # database config
    # SQLTIE3 sqlite+aiosqlite:///database.db  # 数据库文件名为 database.db 不存在的新建一个
    # 异步 mysql+aiomysql://user:password@host:port/dbname
    # DB_URL = os.environ.get("DB_URL") or "mysql+aiomysql://root:123456@localhost/tgforward?charset=utf8mb4"
    DATABASE_URI: str = "sqlite+aiosqlite:///database.db"
    DATABASE_ECHO: bool = False  # 是否打印数据库日志 (可看到创建表、表数据增删改查的信息)

    # logger config
    LOGGER_SAVE: bool = False
    LOGGER_DIR: str = "logs"  # 日志文件夹名
    LOGGER_NAME: str = "{time:YYYY-MM-DD_HH-mm-ss}.log"  # 日志文件名 (时间格式)
    LOGGER_LEVEL: str = "DEBUG"  # 日志等级: ['DEBUG' | 'INFO']
    # 日志分片: 按 时间段/文件大小 切分日志. 例如 ["500 MB" | "12:00" | "1 week"]
    LOGGER_ROTATION: str = "00:00"
    LOGGER_RETENTION: str = "30 days"  # 日志保留的时间: 超出将删除最早的日志. 例如 ["1 days"]

    model_config = SettingsConfigDict(case_sensitive=True)  # 区分大小写


settings = Settings()
