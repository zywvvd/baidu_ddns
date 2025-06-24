from vvdutils import log_init
from vvdutils import Path
from lib import DDNS
from lib import get_date_str
import time


if __name__ == "__main__":
    # 建立对象
    config_json_path = 'assets/config.json'
    ddns_obj = DDNS.from_cofig(config_json_path)
    
    # 检测间隔时间，建议600秒
    sync=600 

    # IP 更新类型, 可选 ipv4 ipv6
    ip_type = 'ipv4'

    # 更新二级域名, 如 www.baidu.com 中的 www
    domain_name = "uipv4"

    # 日志文件
    logger_file = Path('log') / (get_date_str() + '.log')
    logger = log_init(logger_file)
    logger("*" * 60)
    logger("*" * 18 + '  Baidu DDNS start !!!  ' + "*" * 18 )
    logger("*" * 60)

    # 循环更新
    first = True
    while True:
        try:
            ddns_obj.SET(domain_name, ip_type, logger)
        except Exception as e:
            logger(f"ddns_obj SET failed: {e}")
        time.sleep(sync)
