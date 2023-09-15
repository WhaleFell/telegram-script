# /bin/python3
# 监听一个 USDT 地址
# 筛选出交易大于指定金额的交易
# 保持为一个文件并每隔 1s 更新一次文件
# 使用的是 https://tronscan.io/#/myaccount/apiKeys 的 API
import httpx
import time
from typing import List
import datetime
from pathlib import Path
import click
from loguru import logger
import sys
from tronpy.keys import PrivateKey
import tronpy
#### 使用教程 #####
# 1. 配置完以下参数
# 2. python USDTWatch.py watch # 监控USDT转账并保存到 USDT.txt tokens.txt 不间断运行不断更新
# 3. python USDTWatch.py transfer tokens.txt -a 金额 # 读取 tokens.txt 文件并转账对应的金额

################ Config ##############
amount_filter = 1000  # 需要过滤的金额
# USDT 地址
# token = "TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi"
token = "TYQHF8KVbptgzGuu74tDUphZWxkwkDRXMi"
# 设置私钥
private_key = 'YOUR_PRIVATE_KEY'
# 起始时间,一定要按照以下格式
start_times = "2023-9-14 00:00:00"
end_times = "2023-9-15 00:00:00"

DEBUG = True
##################### Config End ##############


apikey = "bc521e3d-efc5-4d46-b775-3202558e7e9f"
ROOTPATH: Path = Path(__file__).parent.absolute()

# logger
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | {name}:{function} {level} | <level>{message}</level>",
    level="DEBUG" if DEBUG else "INFO",
    backtrace=True,
    diagnose=True
)


@click.group()
def cli():
    pass


class USDTAPI(object):
    def __init__(self, apikey: str) -> None:
        self.apikey = apikey
        self.header = {
            "TRON-PRO-API-KEY": self.apikey,
            "User-Agent": "Andriod 6.0"
        }

    def reqAPI(self, token: str, index: str, limit: int):
        start_time = time.time()
        url = f"https://apilist.tronscanapi.com/api/transfer/trx?address={token}&start={index}&limit={limit}&direction=0&reverse=true&fee=true&db_version=1&start_timestamp={self.str_to_timestamp(start_times)}0&end_timestamp={self.str_to_timestamp(end_times)}"

        with httpx.Client(headers=self.header) as client:
            response = client.get(url)
            datas: List = response.json()["data"]

        for data in datas:
            # print(data)
            amount = data["amount"]
            timestamp: str = str(data["block_timestamp"])[:10]
            beijing_time = datetime.datetime.fromtimestamp(int(timestamp), datetime.timezone(
                datetime.timedelta(hours=8))).strftime(
                    '%Y-%m-%d %H:%M:%S'
            )
            from_: str = data["from"]
            if int(amount) < amount_filter:
                continue

            if from_ == token:
                from_ = ""
            else:
                from_ += " ==> "

            to = data["to"]

            if from_:
                self.appendTXT(from_.replace(" ==> ", "")+"\n",
                               path=Path(ROOTPATH, "tokens.txt"))

            string = f"金额:{amount} 地址:{from_} {to} 时间:{beijing_time}\n"
            self.appendTXT(string=string)

        end_time = time.time()
        logger.info(f"获取到{int(index)+limit}的记录 耗时:{end_time-start_time}")

    def appendTXT(self, string: str, path: Path = Path(ROOTPATH, "USDT.txt")):
        with open(path.as_posix(), encoding="utf8", mode="+a") as f:
            f.write(string)

    def str_to_timestamp(self, time_str: str):
        dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        timestamp = int(dt.timestamp())  # 转换为毫秒级时间戳
        return timestamp

    def firstUpdate(self):
        """首次更新获取全部"""
        i = 0
        limit = 50
        if Path(ROOTPATH, "USDT.txt").exists():
            Path(ROOTPATH, "USDT.txt").unlink()
        if Path(ROOTPATH, "tokens.txt").exists():
            Path(ROOTPATH, "tokens.txt").unlink()
        while True:
            try:
                self.reqAPI("TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi",
                            index=i, limit=limit)
                i += limit
            except Exception as e:
                logger.error(f"出现异常(可以忽略):{e}")
                break

        logger.success("更新完成")


@click.command(name="watch", help="监听 USDT 的交易")
def updateWatch():
    while True:
        try:
            usdt = USDTAPI(apikey=apikey)
            usdt.firstUpdate()
            logger.success("更新成功!")
            time.sleep(2)
        except Exception as e:
            logger.error(f"更新失败:{e}")


def transferTRX(to: str, amount: int) -> bool:
    """发送指定trx到地址"""
    # 初始化TronPy客户端
    client = tronpy.HTTPProvider("https://api.trongrid.io")
    tron = tronpy.Tron(client)

    # 使用私钥创建一个帐户对象
    private_key_bytes = PrivateKey(bytes.fromhex(private_key))
    account = private_key_bytes.to_account()

    # 检查帐户余额是否足够
    balance = tron.trx.get_balance(account.address.base58)
    if balance < amount:
        return "余额不足"

    # 构建转账交易
    tx = tron.transaction_builder.send_token(
        to_address=to,
        amount_sun=amount * 1_000_000,  # 将TRX转换为SUN（1 TRX = 1,000,000 SUN）
        from_address=account.address.base58,
        token_id="trx",  # TRX代币ID
    )

    # 签署交易
    signed_tx = tron.trx.sign(tx, private_key_bytes)

    # 发送交易
    result = tron.trx.broadcast(signed_tx)

    logger.success(f"交易已发送，交易哈希：{result['txid']}")
    return True


@click.command(name="transfer", help="批量转账,提供一个需要转账的列表txt文件,并用 -a 提供金额")
@click.argument('file')
@click.option('-a', "--amount", default=0.001)
def bulkTransfer(file: str, amount: int):
    """批量转账"""
    file = Path(file).as_posix()
    with open(file, encoding="utf8", mode="r") as f:
        addrs = f.readlines()

    for addr in addrs:
        addr = addr.replace("\n", "").strip()
        try:
            logger.info(f"{token} ==> {addr} amount:{amount}")
            transferTRX(addr, amount=amount)
        except Exception as e:
            logger.exception(f"{token} ==> {addr} amount:{amount} 出现错误!")


cli.add_command(updateWatch)
cli.add_command(bulkTransfer)

if __name__ == "__main__":
    cli()
