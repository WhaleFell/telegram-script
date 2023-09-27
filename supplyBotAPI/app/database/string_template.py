#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# curd/string_template.py
# 文字模板
from dataclasses import dataclass
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# parameter
# 【每次消耗的USDT】
# 【发表次数】
# 【当前时间】
# 【用户内容】


class CustomParam(BaseModel):
    costAmount: int
    count: int
    currentTime: datetime = Field(default_factory=datetime.now)
    sendCountent: str


@dataclass
class StringTemplate:
    description: str = """
发布规则 付费广告 消耗 【每次消耗的USDT】 USDT

发布付费广告严格要求如下
1：行数限制15行内【超过百分百不通过】
2：禁止发布虚假内容，禁止诈骗欺骗用户🚫
3：无需备注累计广告次数，机器人会自动统计

请编写好广告词，点击下方【📝自助发布】

供给频道： https://t.me/gcccaasas
"""
    # 供应文案
    provide_desc: str = """
项目名称：
项目介绍：
价格：
联系人：
频道：【选填/没频道可以不填】
"""

    # 需求文案
    require_desc: str = """
需求：
预算：
联系人：
频道：【选填/没频道可以不填】
"""

    send_content: str = """
【用户内容】

该用户累计发布 【发表次数】 次，当前时间：【当前时间】
"""


# def loopReplace(string: str, customObj: CustomParam) -> str:
#     return string.replace("【每次消耗的USDT】", str(customObj.costAmount))


# def replace(self, customObj: CustomParam):
#     return self
