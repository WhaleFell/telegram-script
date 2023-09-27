#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# schemas/user.py
# 响应 user 模型

from .base import BaseResp
from pydantic import Field, BaseModel, ConfigDict
from datetime import datetime


class BMUser(BaseModel):
    id: int = Field(description="数据库生成的 ID")
    username: str = Field(description="用户名")
    password: str = Field(description="密码")
    create_at: datetime = Field(description="注册时间")

    model_config = ConfigDict(from_attributes=True)


class UserResp(BaseResp):
    content: BMUser


class Token(BaseModel):
    access_token: str
    token_type: str
