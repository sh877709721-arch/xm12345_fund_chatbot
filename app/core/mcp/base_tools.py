from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json5
import pytz

# Initialize FastMCP server
mcp = FastMCP("base_tools")

@mcp.tool()
def get_current_time():
    """获取当前时间（Asia/Shanghai时区）"""

    # 设置Asia/Shanghai时区
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(shanghai_tz)
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

    return json5.dumps({
        'current_time': current_time_str,
        'timezone': 'Asia/Shanghai',
        'timestamp': current_time.timestamp()
    }, ensure_ascii=False)

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')    


if __name__ == '__main__':
    main()