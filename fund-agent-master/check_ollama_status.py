#!/usr/bin/env python3
# 检查Ollama状态和已下载的模型

import requests
import json

# Ollama API地址
OLLAMA_BASE_URL = "http://localhost:11434"

print("=== 检查Ollama状态 ===")

# 检查Ollama服务是否在线
try:
    response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
    if response.status_code == 200:
        print("✅ Ollama服务在线")
        
        # 获取已下载的模型列表
        models = response.json().get("models", [])
        print(f"\n📋 已下载的模型列表 ({len(models)}个):")
        for model in models:
            name = model.get("name", "未知")
            size = model.get("size", 0) / (1024 * 1024 * 1024)  # 转换为GB
            modified_at = model.get("modified_at", "未知")
            print(f"  - {name} (大小: {size:.2f}GB, 修改时间: {modified_at})")
        
        if models:
            print(f"\n🎯 建议使用的模型: {models[0]['name']}")
        else:
            print("\n⚠️  没有已下载的模型，请使用以下命令下载:")
            print("   ollama pull 模型名称")
            print("   例如: ollama pull qwen2:latest")
    else:
        print(f"❌ Ollama服务响应异常，状态码: {response.status_code}")
        print(f"   响应内容: {response.text}")
        print("\n⚠️  请检查Ollama服务是否正在运行，以及是否开启了网络访问")
except requests.exceptions.ConnectionError:
    print("❌ 无法连接到Ollama服务")
    print("\n⚠️  请确保:")
    print("   1. Ollama服务已启动")
    print("   2. 已开启\"Expose Ollama to the network\"选项")
    print("   3. 防火墙允许访问11434端口")
except Exception as e:
    print(f"❌ 检查Ollama状态时出错: {e}")

print("\n=== 检查完成 ===")