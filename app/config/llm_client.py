from openai import AsyncOpenAI, OpenAI
from app.core.rag.rerank import RerankClient
from app.config.settings import settings




# chat_client = OpenAI(
#     base_url=settings.BASE_URL + '/api/llm1/v1', 
#     api_key=settings.API_KEY or '123456'
# )

# chat_client_small = OpenAI(
#     base_url=settings.BASE_URL + '/api/llm2/v1', 
#     api_key=settings.API_KEY or '123456'
# )


embedding_client = OpenAI(
    base_url=settings.BASE_URL + "/api/nlp-model/v1", 
    api_key=settings.API_KEY or ""
)


# 创建全局 rerank 客户端实例
rerank_client_instance = RerankClient(
    base_url=settings.BASE_URL + "/api/bge-reranker/v1"
) 

chat_client_bot = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
)