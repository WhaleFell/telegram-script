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
tgbase python bulkReportUser.py -u "@shenxian"

```
