# Telegram script make by myself

The Scripts base Pyrogram framework!

恭喜你发现一个价值1k的仓库

## start

```shell
git clone https://github.com/WhaleFell/telegram-script.git
cd telegram-script
docker build . -t tgbase

docker run -d --name=qfxx \
-v /root/新币/群发消息9.17号.py:/wkdir/main.py \
-v /root/新币/sessions:/wkdir/sessions \
tgbase python -u main.py

docker logs -f getRedpacketBulk


docker run -d --name=getRedpacketBulk \
-v /wfwork/telegram-script:/wkdir/ \
-v /root/snap/生成txt/sessions:/wkdir/sessions \
tgbase python -u getRedpacketBulk.py

docker run -d --name=a1 \
-v /wfwork/telegram-script/getRedpacketBulk.py:/wkdir/getRedpacketBulk.py \
-v /root/snap/脚本一组/sessions:/wkdir/sessions \
tgbase python -u getRedpacketBulk.py

docker run -d --name=a2 \
-v /wfwork/telegram-script/getRedpacketBulk.py:/wkdir/getRedpacketBulk.py \
-v /root/snap/脚本二组/sessions:/wkdir/sessions \
tgbase python -u getRedpacketBulk.py



# 自动抢红包运行教程
# 1. 后台运行 Docker 并替换以下中文

docker run -d --name=自己起一个名称 \
-v /root/snap/汇旺红包/汇旺抢红包.py:/wkdir/汇旺抢红包.py \
-v 保存sessions的文件夹(绝对路径):/wkdir/sessions \
tgbase python -u 汇旺抢红包.py

# 2. 查看日志
`docker logs -f a1`
# 3. 控制启停
# 停止
`docker stop 自己起的名称`
# 开启
`docker start 自己起的名称`
# 重启
`docker restart 自己起的名称`

docker ps --format '{{.Names}} {{.Status}}'


docker run -d --name=supplybot_test \
-e NAME="WFTest8964Bot" \
-e DB_URL="mysql+aiomysql://root:lovehyy@172.17.0.2:3306/supplyTGBot?charset=utf8mb4" \
-v /wfwork/tgbot_base/telegram-script/supplyBot.py:/wkdir/main.py \
-v /wfwork/tgbot_base/telegram-script/sessions:/wkdir/sessions \
tgbot_base python -u main.py


# 抢注名字程序
docker run -d --name=robGroupName \
-e NAME="文件名称" \
-v 替换为脚本绝对目录:/wkdir/main.py \
-v 替换为Session文件夹绝对目录:/wkdir/sessions \
tgbot_base python -u main.py

# 查看日志
docker logs -f robGroupName

```

## USDT 支付接口平台搭建

```shell

```
