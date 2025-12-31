# -*- coding: utf-8 -*-
"""
编码测试文件
测试中文字符显示是否正常
"""

def test_chinese_encoding():
    """
    测试函数
    包含中文注释和字符串
    """
    chinese_text = "这是一个测试字符串"
    more_chinese = "包含特殊字符：①②③④⑤"

    print(f"测试文本: {chinese_text}")
    print(f"更多中文: {more_chinese}")

    return {
        "status": "成功",
        "message": "编码测试通过",
        "chinese_count": len(chinese_text),
        "encoding": "UTF-8"
    }

# 类定义示例
class 测试类:
    """这是一个测试类，类名包含中文"""

    def __init__(self, 名称):
        self.名称 = 名称

    def 获取名称(self):
        """获取对象名称"""
        return self.名称

# 主程序入口
if __name__ == "__main__":
    result = test_chinese_encoding()
    print(result)

    # 创建测试对象
    test_obj = 测试类("测试实例")
    print(f"对象名称: {test_obj.获取名称()}")