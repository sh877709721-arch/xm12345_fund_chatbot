import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.rule.dialog_state import RegionSlots, ResponseIntent

# 编写测试用例

def test_response_intent():
    """测试 ResponseIntent 类的意图识别功能"""
    print("=== 测试 ResponseIntent 意图识别 ===")

    intent = ResponseIntent()

    # 测试操作方式询问
    print("\n1. 测试操作方式询问 (how):")
    how_queries = [
        "这个政策怎么申请？",
        "如何办理医保？",
        "具体的流程是什么？",
        "需要提交什么材料？",
        "办理指南在哪里？",
        "申请步骤有哪些？"
    ]

    for query in how_queries:
        found = [keyword for keyword in intent.how if keyword in query]
        print(f"  查询: {query}")
        print(f"  匹配关键词: {found}")
        print(f"  意图类型: 操作方式询问")
        print("-" * 50)

    # 测试政策内容询问
    print("\n2. 测试政策内容询问 (what):")
    what_queries = [
        "这个政策是什么？",
        "医保有哪些福利？",
        "具体的补贴内容是什么？",
        "政策的适用对象是谁？",
        "申请条件是什么？",
        "包含哪些权益？"
    ]

    for query in what_queries:
        found = [keyword for keyword in intent.what if keyword in query]
        print(f"  查询: {query}")
        print(f"  匹配关键词: {found}")
        print(f"  意图类型: 政策内容询问")
        print("-" * 50)

    # 测试原因询问
    print("\n3. 测试原因询问 (why):")
    why_queries = [
        "为什么要实施这个政策？",
        "申请失败的原因是什么？",
        "这个政策的意义是什么？",
        "有什么好处？"
    ]

    for query in why_queries:
        found = [keyword for keyword in intent.why if keyword in query]
        print(f"  查询: {query}")
        print(f"  匹配关键词: {found}")
        print(f"  意图类型: 原因询问")
        print("-" * 50)

    # 测试时间询问
    print("\n4. 测试时间询问 (when):")
    when_queries = [
        "政策什么时候开始？",
        "申请截止时间是什么时候？",
        "有效期是多久？",
        "需要多长时间处理？"
    ]

    for query in when_queries:
        found = [keyword for keyword in intent.when if keyword in query]
        print(f"  查询: {query}")
        print(f"  匹配关键词: {found}")
        print(f"  意图类型: 时间询问")
        print("-" * 50)

    # 测试地点询问
    print("\n5. 测试地点询问 (where):")
    where_queries = [
        "在哪里可以办理？",
        "要去哪个部门？",
        "现场办理地址是什么？",
        "可以线上申请吗？"
    ]

    for query in where_queries:
        found = [keyword for keyword in intent.where if keyword in query]
        print(f"  查询: {query}")
        print(f"  匹配关键词: {found}")
        print(f"  意图类型: 地点询问")
        print("-" * 50)

    # 测试费用询问
    print("\n6. 测试费用询问 (how_much):")
    how_much_queries = [
        "办理需要多少钱？",
        "收费吗？",
        "费用标准是多少？",
        "是免费的吗？"
    ]

    for query in how_much_queries:
        found = [keyword for keyword in intent.how_much if keyword in query]
        print(f"  查询: {query}")
        print(f"  匹配关键词: {found}")
        print(f"  意图类型: 费用询问")
        print("-" * 50)

    # 测试资格询问
    print("\n7. 测试资格询问 (can):")
    can_queries = [
        "我可以申请吗？",
        "能否享受这个政策？",
        "符合什么条件？",
        "有资格限制吗？"
    ]

    for query in can_queries:
        found = [keyword for keyword in intent.can if keyword in query]
        print(f"  查询: {query}")
        print(f"  匹配关键词: {found}")
        print(f"  意图类型: 资格询问")
        print("-" * 50)

    # 测试状态询问
    print("\n8. 测试状态询问 (status):")
    status_queries = [
        "申请进度如何？",
        "审核通过了吗？",
        "现在处理状态是什么？",
        "什么时候能有结果？"
    ]

    for query in status_queries:
        found = [keyword for keyword in intent.status if keyword in query]
        print(f"  查询: {query}")
        print(f"  匹配关键词: {found}")
        print(f"  意图类型: 状态询问")
        print("-" * 50)

def test_region():
    region_state = RegionSlots()
    in_xm=region_state.get_region_statement('我在厦门')
    print(in_xm) # 本地
    in_fj=region_state.get_region_statement('我在厦门交医保，泉州')
    print(in_fj)
    in_cn=region_state.get_region_statement('我在厦门交医保，去成都')
    print(in_cn)


if __name__ == '__main__':
    # 测试意图识别
    test_response_intent()

    print("\n" + "="*80 + "\n")

    # 测试地区识别
    test_region()