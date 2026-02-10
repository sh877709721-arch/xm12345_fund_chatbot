from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json5

# Initialize FastMCP server
mcp = FastMCP("medical_insurance")

@mcp.tool()
def get_current_time():
    """获取当前时间"""

    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return json5.dumps({'current_time': current_time_str}, ensure_ascii=False)

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')    


if __name__ == '__main__':
    main()