from langchain_openai import ChatOpenAI
from .config import settings

llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.7,
    api_key=settings.OPENAI_API_KEY
)

judge_llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0.2,
    api_key=settings.OPENAI_API_KEY
)
