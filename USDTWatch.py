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

################ Config ##############

amount_filter = 1000  # 需要过滤的金额
# USDT 地址
token = "TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi"
# 起始时间,一定要按照以下格式
start_times = "2023-9-14 00:00:00"
end_times = "2023-9-15 00:00:00"

##################### Config End ##############

ROOTPATH: Path = Path(__file__).parent.absolute()


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
        print(f"获取到{int(index)+limit}的记录 耗时:{end_time-start_time}")

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
                print(f"出现异常(可以忽略):{e}")
                break

        print("更新完成")


def main():
    apikey = "bc521e3d-efc5-4d46-b775-3202558e7e9f"
    usdt = USDTAPI(apikey=apikey)
    usdt.firstUpdate()
    print("更新成功!")


if __name__ == "__main__":

    while True:
        try:
            main()
            time.sleep(1)
        except Exception as e:
            print(f"更新失败:{e}")
