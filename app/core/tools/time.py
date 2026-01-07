from datetime import datetime
import pytz


def get_current_time() ->str:
    """获取当前时间（Asia/Shanghai时区）"""

    # 设置Asia/Shanghai时区
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(shanghai_tz)
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

    return current_time_str
