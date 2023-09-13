# 全能转载王需求文档

1. 要求友好的 inline keyboard 操作
2. /start 简介
请拉入傀儡号:@wwww 进入对应的群聊
请确保群聊 ID 的正确性，如不知道，就把傀儡号拉入群聊并发送 /getID
下面的按钮
添加转载 管理转载
返回主页

管理转载:选择你要管理的任务 键盘选择
选择后弹出任务详细，下面按钮 编辑 删除
编辑 接收配置文本

添加转载 提示如何添加 接收配置文本

## 数据库设计

tgconfigs tables

```sql
CREATE TABLE forward_configs (
id INT PRIMARY KEY COMMENT '主键',
user_id VARCHAR(20) NOT NULL COMMENT '傀儡号的唯一标识符' DEFAULT get_user_id(),
source VARCHAR(20) NOT NULL COMMENT '源群聊ID',
dest VARCHAR(20) NOT NULL COMMENT '目标群聊ID',
forward_history_count INT COMMENT '转发历史信息的数量',
forward_history_state BOOL DEFAULT FALSE COMMENT '转发历史信息的状态',
interval_second INT NOT NULL COMMENT '间隔时间单位 s' DEFAULT 20,
remove_word VARCHAR(100) COMMENT '删除的文字,用,分隔',
cut_word VARCHAR(100) COMMENT '截断词,用 , 分隔',
skip_word VARCHAR(100) COMMENT '跳过词,用 , 分隔',
add_text VARCHAR(100) COMMENT '跳过语,用 , 分隔',
create_at DATETIME NOT NULL DEFAULT NOW() COMMENT '创建时间',
create_id VARCHAR(20) COMMENT '设置机器人的用户ID'
) COMMENT '转载配置表';
```
