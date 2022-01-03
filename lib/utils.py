import time

def get_date_str():
    str_time = time.localtime(time.time())
    year = str_time.tm_year
    mounth = str_time.tm_mon
    day = str_time.tm_mday

    date_str = f"{year}-{mounth}-{day}"
    return date_str