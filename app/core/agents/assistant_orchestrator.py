"""
Orchestrator-Worker

"""
import logging
from typing import List, Dict,Optional
from app.config.llm_client import embedding_client, chat_client_bot
from app.core.rag.rag_search import RAGSearch



class OrchestratorAgent:
    """基于知识图谱+搜索策略的Agent"""

    def __init__(self):
        self.rag_search = RAGSearch()
        self.client = chat_client_bot

        # 预定义的类别体系
        self.intent_categories = {
            "职工基本医疗保险": {
                "参保缴费": ["参保对象", "缴费标准", "参保缴费方式", "参保缴费纠纷处理", "重复参保处理", "退费"],
                "医疗待遇": ["待遇生效时间", "连续参保机制", "医保账户划拨", "大病医保", "医疗救助", "待遇标准", "就医使用"],
                "办事指南": ["转移接续手续办理", "医疗费用报销办理", "异地就医备案办理", "家庭共济办理", "医保退休办理", "个人账户一次性支取办理"]
            },
            "城乡居民医疗保险": {
                "参保缴费": ["参保对象", "缴费标准", "参保缴费方式", "重复参保", "退费"],
                "医疗待遇": ["待遇生效时间", "参保长效机制", "医保账户划拨", "大病医保", "医疗救助", "待遇标准", "就医使用"],
                "办事指南": ["医疗费用报销办理", "异地就医备案办理", "家庭共济办理", "转移接续手续办理"]
            },
            "生育保险": {
                "参保缴费": ["参保对象", "缴费标准", "参保缴费方式", "参保缴费纠纷处理"],
                "生育待遇": ["生育津贴待遇", "男职工未就业配偶生育医疗费用待遇", "其他待遇"],
                "办事指南": ["生育津贴办理", "男职工未就业配偶生育医疗费用办理"]
            },
            "其他医药政策": {
                "药品（含项目、耗材）政策": ["药品目录", "医疗服务项目目录", "医用耗材目录"],
                "DRG收费及按病种收费政策": ["厦门市定点医疗机构就医", "省内异地定点医疗机构就医"],
                "辅助生殖政策": ["福建省辅助生殖类医疗服务价格项目及省属公立医院项目价格表", "辅助生殖医保支付政策"],
                "补充医疗保险": ["惠厦保"],
                "长期护理险政策": ["未分类"]
            }
        }
        # self.workser_agent = WorkerAgent()
        # self.intent_optimizer = IntentOptimizer()  """意图分类优化器"""

        
        

    def call_worker(self, query: str):
        """调用另外一个LLM进行答题"""
        

