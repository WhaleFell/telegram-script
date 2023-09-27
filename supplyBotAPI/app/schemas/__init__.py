#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# schemas
# 储存 Pydantic 的模型
# 注意要和 SQLAlchemy 模型分开

from .base import BaseResp
from .user import UserResp, BMUser, Token
