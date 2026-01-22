from mcp.server.fastmcp import FastMCP
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser as date_parser
from typing import Optional, Union
import json5
import pytz

# Initialize FastMCP server
mcp = FastMCP("base_tools")

# 时区配置
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')

def _parse_date_input(date_input: Union[str, float, int]) -> Optional[datetime]:
    """
    解析各种格式的日期输入

    支持的格式:
    - ISO 格式: "2024-01-15", "2024-01-15 10:30:00"
    - 时间戳: 1705305600 (int/float)
    - 相对时间: "today", "now", "yesterday"
    - 其他常见格式: "2024/01/15", "15-01-2024"

    Args:
        date_input: 日期输入，可以是字符串或时间戳

    Returns:
        datetime对象或None（解析失败时）
    """
    if date_input is None:
        return None

    try:
        # 处理时间戳
        if isinstance(date_input, (int, float)):
            return datetime.fromtimestamp(date_input, SHANGHAI_TZ)

        # 处理字符串
        if isinstance(date_input, str):
            date_str = date_input.strip()

            # 处理相对时间
            if date_str.lower() in ['today', 'now']:
                return datetime.now(SHANGHAI_TZ)
            elif date_str.lower() == 'yesterday':
                return datetime.now(SHANGHAI_TZ) - relativedelta(days=1)

            # 使用 dateutil 解析
            parsed_date = date_parser.parse(date_str, fuzzy=True)

            # 如果解析出的日期没有时区信息，添加上海时区
            if parsed_date.tzinfo is None:
                parsed_date = SHANGHAI_TZ.localize(parsed_date)

            return parsed_date

    except Exception:
        return None


@mcp.tool()
def get_current_time():
    """获取当前时间（Asia/Shanghai时区）"""
    current_time = datetime.now(SHANGHAI_TZ)
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

    return json5.dumps({
        'current_time': current_time_str,
        'timezone': 'Asia/Shanghai',
        'timestamp': current_time.timestamp()
    }, ensure_ascii=False)


@mcp.tool()
def calculate_event_time(
    event_date: Union[str, float, int],
    deadline_date: Optional[Union[str, float, int]] = None,
    threshold_days: int = 90
):
    """
    计算事件时间相关的所有信息

    功能:
    - 计算事件发生至今的时间跨度（天、月）
    - 判断是否超过指定阈值（默认90天）
    - 如有截止日期，判断是否超期/过期，计算剩余或逾期天数

    Args:
        event_date: 事件发生日期（必需），支持多种格式:
            - ISO格式: "2024-01-15", "2024-01-15 10:30:00"
            - 时间戳: 1705305600
            - 相对时间: "today", "yesterday"
        deadline_date: 截止日期/有效期（可选），格式同event_date
        threshold_days: 计算阈值（天数），默认90天

    Returns:
        JSON格式的计算结果，包含以下字段:
        {
            "event_date": "2024-01-15 00:00:00",        # 事件日期（标准化格式）
            "current_date": "2024-04-15 14:30:00",      # 当前日期
            "days_elapsed": 91,                          # 已过天数
            "months_elapsed": 3,                         # 已过月数（整数）
            "is_threshold_exceeded": true,               # 是否超过阈值
            "deadline_info": {                           # 截止日期相关信息
                "deadline_date": "2024-04-01 00:00:00", # 截止日期
                "remaining_days": null,                  # 剩余天数（未超期时）
                "overdue_days": 14,                      # 逾期天数（已超期时）
                "is_overdue": true                       # 是否超期/过期
            },
            "is_future_event": false,                    # 是否为未来事件
            "error": null                                # 错误信息（如有）
        }

    Example:
        # 已过3个月的事件，有截止日期且已超期
        calculate_event_time("2024-01-15", "2024-04-01", 90)

        # 简单的时间跨度计算
        calculate_event_time("2024-01-15", threshold_days=60)

        # 使用时间戳
        calculate_event_time(1705305600, 1711929600)
    """
    # 解析事件日期
    event_dt = _parse_date_input(event_date)
    if event_dt is None:
        return json5.dumps({
            'error': f'无法解析事件日期: {event_date}',
            'event_date': str(event_date)
        }, ensure_ascii=False)

    # 获取当前时间
    current_dt = datetime.now(SHANGHAI_TZ)

    # 检查是否为未来事件
    is_future_event = event_dt > current_dt

    # 计算时间跨度
    time_diff = current_dt - event_dt if not is_future_event else event_dt - current_dt
    days_elapsed = abs(time_diff.days)

    # 计算月数（使用 relativedelta 精确计算）
    if not is_future_event:
        delta = relativedelta(current_dt, event_dt)
        months_elapsed = delta.years * 12 + delta.months
    else:
        delta = relativedelta(event_dt, current_dt)
        months_elapsed = -(delta.years * 12 + delta.months)

    # 判断是否超过阈值
    is_threshold_exceeded = days_elapsed > threshold_days

    # 构建基础结果
    result = {
        'event_date': event_dt.strftime("%Y-%m-%d %H:%M:%S"),
        'current_date': current_dt.strftime("%Y-%m-%d %H:%M:%S"),
        'days_elapsed': days_elapsed,
        'months_elapsed': months_elapsed,
        'is_threshold_exceeded': is_threshold_exceeded,
        'threshold_days': threshold_days,
        'is_future_event': is_future_event,
        'deadline_info': None,
        'error': None
    }

    # 如果提供了截止日期，处理截止日期相关信息
    if deadline_date is not None:
        deadline_dt = _parse_date_input(deadline_date)

        if deadline_dt is None:
            result['deadline_info'] = {
                'error': f'无法解析截止日期: {deadline_date}',
                'deadline_date': str(deadline_date)
            }
        else:
            is_overdue = current_dt > deadline_dt
            deadline_diff = current_dt - deadline_dt if is_overdue else deadline_dt - current_dt
            deadline_days = abs(deadline_diff.days)

            result['deadline_info'] = {
                'deadline_date': deadline_dt.strftime("%Y-%m-%d %H:%M:%S"),
                'is_overdue': is_overdue,
                'remaining_days': deadline_days if not is_overdue else None,
                'overdue_days': deadline_days if is_overdue else None,
                'event_to_deadline_days': abs((deadline_dt - event_dt).days),
                'error': None
            }

    return json5.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def parse_event_date(date_input: Union[str, float, int]):
    """
    解析各种格式的日期输入为标准格式

    这是一个辅助工具，用于验证和标准化日期输入

    Args:
        date_input: 日期输入，支持多种格式:
            - ISO格式: "2024-01-15", "2024-01-15 10:30:00"
            - 时间戳: 1705305600 (int/float)
            - 相对时间: "today", "now", "yesterday"
            - 其他格式: "2024/01/15", "15-01-2024"

    Returns:
        JSON格式的解析结果:
        {
            "success": true,
            "parsed_date": "2024-01-15 00:00:00",
            "iso_format": "2024-01-15T00:00:00+08:00",
            "timestamp": 1705305600.0,
            "timezone": "Asia/Shanghai",
            "input": "2024-01-15",
            "error": null
        }

    Example:
        parse_event_date("2024-01-15")
        parse_event_date(1705305600)
        parse_event_date("today")
    """
    parsed_dt = _parse_date_input(date_input)

    if parsed_dt is None:
        return json5.dumps({
            'success': False,
            'parsed_date': None,
            'input': str(date_input),
            'error': f'无法解析日期输入: {date_input}'
        }, ensure_ascii=False)

    return json5.dumps({
        'success': True,
        'parsed_date': parsed_dt.strftime("%Y-%m-%d %H:%M:%S"),
        'iso_format': parsed_dt.isoformat(),
        'timestamp': parsed_dt.timestamp(),
        'timezone': 'Asia/Shanghai',
        'input': str(date_input),
        'error': None
    }, ensure_ascii=False, indent=2)




def main():
    # Initialize and run the server
    mcp.run(transport='stdio')    


if __name__ == '__main__':
    main()