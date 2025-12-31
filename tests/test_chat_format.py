#!/usr/bin/env python3
"""
测试新的聊天消息格式，支持文件内容
"""

from app.router.chat import ChatMessage, ContentItem, extract_message_content, extract_files_from_content

def test_message_formats():
    """测试不同的消息格式"""

    print("=== 测试消息格式解析 ===")

    # 测试1: 纯文本消息
    text_message = ChatMessage(role="user", content="你好，我想知道医保缴交基数")
    extracted_text = extract_message_content(text_message.content)
    extracted_files = extract_files_from_content(text_message.content)
    print(f"测试1 - 纯文本消息:")
    print(f"  原始内容: {text_message.content}")
    print(f"  提取文本: {extracted_text}")
    print(f"  提取文件: {extracted_files}")
    print()

    # 测试2: 文件消息（如示例）
    file_message = ChatMessage(
        role="user",
        content=[
            ContentItem(text="介绍图一"),
            ContentItem(file="https://arxiv.org/pdf/1706.03762.pdf")
        ]
    )
    extracted_text = extract_message_content(file_message.content)
    extracted_files = extract_files_from_content(file_message.content)
    print(f"测试2 - 文件消息:")
    print(f"  原始内容: {[item.dict() for item in file_message.content]}")
    print(f"  提取文本: {extracted_text}")
    print(f"  提取文件: {extracted_files}")
    print()

    # 测试3: 混合消息（多个文件和文本）
    mixed_message = ChatMessage(
        role="user",
        content=[
            ContentItem(text="请分析这两个文档"),
            ContentItem(file="https://example.com/doc1.pdf"),
            ContentItem(file="https://example.com/doc2.pdf"),
            ContentItem(text="并给出总结")
        ]
    )
    extracted_text = extract_message_content(mixed_message.content)
    extracted_files = extract_files_from_content(mixed_message.content)
    print(f"测试3 - 混合消息:")
    print(f"  原始内容: {[item.dict() for item in mixed_message.content]}")
    print(f"  提取文本: {extracted_text}")
    print(f"  提取文件: {extracted_files}")
    print()

def test_request_format():
    """测试请求格式"""
    print("=== 测试请求格式 ===")

    from app.router.chat import ChatRequest

    # 测试新的请求格式
    request_data = {
        "chat_id": "595c6a2f-a8d4-4bbd-864c-722a790bc2ac",
        "model": "xmtelecom",
        "messages": [
            {"role": "user", "content": "你好，我想知道医保缴交基数"},
            {"role": "user", "content": [
                {"text": "介绍图一"},
                {"file": "https://arxiv.org/pdf/1706.03762.pdf"}
            ]}
        ],
        "max_tokens": 8192,
        "temperature": 0.2
    }

    try:
        chat_request = ChatRequest(**request_data)
        print("✅ 请求格式验证成功!")
        print(f"Chat ID: {chat_request.chat_id}")
        print(f"消息数量: {len(chat_request.messages)}")

        for i, msg in enumerate(chat_request.messages):
            print(f"  消息 {i+1}: {msg.role} - {extract_message_content(msg.content)}")

    except Exception as e:
        print(f"❌ 请求格式验证失败: {e}")

if __name__ == "__main__":
    test_message_formats()
    test_request_format()
    print("=== 测试完成 ===")