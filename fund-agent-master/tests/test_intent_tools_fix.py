#!/usr/bin/env python3
"""
测试意图识别工具的集成
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



from app.core.intent import MedicalInsuranceIntentRecognizer

recognizer = MedicalInsuranceIntentRecognizer()
intent_result = recognizer.recognize_intent("我想了解生育津贴")

if intent_result.needs_clarification:
    print(f"需要澄清: {intent_result.clarification_question}")
else:
    print(f"识别结果: {intent_result.second_level} - {intent_result.third_level}")