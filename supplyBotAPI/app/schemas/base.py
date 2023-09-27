#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# schemas/base.py
# API 基模型

from pydantic import BaseModel, Field
from typing import Optional, Any
from pydantic import ConfigDict


class BaseResp(BaseModel):
    code: int = Field(default=200, description="响应状态码")
    msg: Optional[str] = Field(default=None, description="响应信息")

    # Pydantic V2 changes
    # https://docs.pydantic.dev/latest/migration/#changes-to-config
    # class Config:
    # no only trying to get the id value from a dict
    # also try to get it from an attribute,
    # id = data["id"] 或者 id = data.id

    # class Config:
    #     orm_mode = True

    content: Any = None

    model_config = ConfigDict(from_attributes=True)
