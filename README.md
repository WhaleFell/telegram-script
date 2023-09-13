# Telegram script make by myself

The Scripts base Pyrogram framework!

## start

```shell
git clone https://github.com/WhaleFell/telegram-script.git
cd telegram-script
docker build . -t tgbase

docker run -d --name=bulkReportUser \
-v /wfwork/telegram-script:/wkdir/ \
-v /root/snap/脚本/举报脚本/sessions:/wkdir/sessions \
tgbase python -u bulkReportUser.py start "@shenxian"

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
```
