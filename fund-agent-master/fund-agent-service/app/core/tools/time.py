from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import pytz


def get_current_time() ->str:
    """获取当前时间（Asia/Shanghai时区）"""

    # 设置Asia/Shanghai时区
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(shanghai_tz)
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

    return current_time_str


def get_three_month_ago() -> str:
    """获取三个月前的日期"""
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(shanghai_tz)
    three_month_ago = current_time - relativedelta(months=3)
    return three_month_ago.strftime("%Y-%m-%d")


def get_last_year() -> int:
    """获取去年年份"""
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(shanghai_tz)
    return current_time.year - 1


def get_current_year() -> int:
    """获取当前年份"""
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(shanghai_tz)
    return current_time.year
