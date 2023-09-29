# ForwardMsgBot 需求文档

## 总述

一个转载传话的机器人,需要支持以下功能：

```text
@@启动巨能超级转载:      
@@来源群组(必)=-1001935250724
@@目标群组(必)=-1001963862221
@@转载数量(非必)=20
@@间隔时间(非必)=1
@@去除词(非必)=  
@@截断词(非必)=
@@跳过词(非必)=
@@纯文字=否
@@纯文字长度=2
@@追加文本=
```

## 具体需求

1. ~~读取源频道或群聊的N条历史信息，指定时间间隔转发到目标。~~（机器人Bot无法实现读取Group获取Channel的历史聊天记录）[how-to-get-specific-channel-chat-history-using-telegram-bot-api--stackoverflow](https://stackoverflow.com/questions/55901417/how-to-get-specific-channel-chat-history-using-telegram-bot-api#:~:text=You%20cannot%20get%20the%20chat%20history%20of%20a,but%20that%20is%20going%20to%20be%20too%20tedious.)
2. 监控源频道或群聊的信息，实时转发到目标。
3. 处理信息后转发。
4. [X] 私聊机器人设置参数。
5. 一个机器人需要支持 N 组转发任务。
6. 良好的异步 Asynchronous 编程。

## 技术栈

1. Python
2. Pyrogram
3. Database
    Python database ORM(Object Relational Mapping 对象关系映射)
    sqlalchemy[https://www.sqlalchemy.org/] alchemy [/ˈæl.kə.mi/] (炼金术，炼丹术 魔法)

## 数据库设计

TGForwardConfig 库
forward_config 表名

source: String (@wdqwsq) 源群聊
dest: String (@wbwbow) 目的群聊
forward_history_count: Int (21) 转发历史条数
interval_second: Int (20) 转发历史信息时间隔的秒数
remove_word: List[String] 字符串列表 去除的字符
cut_word: List[String] 截断词列表
skip_word: List[String] 跳过词列表
add_text: String 追加的文本

## sqlalchemy

[sqlalchemy tutorial](https://www.osgeo.cn/sqlalchemy/tutorial/index.html)

```text
@@来源群组(必)=-1001935250724
@@目标群组(必)=-1001963862221
@@转载数量(非必)=20
@@转载间隔时间(非必)=1
@@去除词(非必)=历史,化学
@@截断词(非必)=好像
@@跳过词(非必)=死亡
@@追加文本(非必)=
```

## requirements.txt

```text
pyrogram
tgcrypto
pydantic
loguru
sqlalchemy

# pyromod
# pyromod fix handle channel message version
git+https://github.com/usernein/pyromod.git
```

## Install by Docker

```shell
# 机器人管理,须在代码中配置管理员和傀儡号
docker run -d --name=forwardAdminBot \
-e DB_URL="mysql+aiomysql://root:lovehyy@172.18.0.6/tgforward?charset=utf8mb4" \
-e NAME=WFTest8964Bot \
-v /wfwork/telegram-script:/wkdir/ \
-v /wfwork/telegram-script/sessions:/wkdir/sessions \
tgbase python -u forwardBotAdmin.py

# 傀儡号
docker run -d --name=forwardPupetUser \
-e DB_URL="mysql+aiomysql://root:lovehyy@172.18.0.6/tgforward?charset=utf8mb4" \
-e NAME=user628 \
-v /wfwork/telegram-script:/wkdir/ \
-v /wfwork/telegram-script/sessions:/wkdir/sessions \
tgbase python -u forwardMsgBot.py
```
