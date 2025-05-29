from typing import Optional, AsyncGenerator
from openai import OpenAI
from app.config import settings


class AIService:
    @staticmethod
    def _get_client() -> Optional[OpenAI]:
        """获取OpenAI客户端"""
        if not settings.DASHSCOPE_API_KEY:
            return None
        
        return OpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.QWEN_BASE_URL,
        )
    
    @staticmethod
    async def get_ai_response(message: str, conversation_history: Optional[list] = None) -> str:
        """调用通义千问API获取AI回复（非流式）"""
        client = AIService._get_client()
        
        # 如果没有配置API密钥，返回模拟响应
        if not client:
            return f"这是对 '{message}' 的模拟AI回复。请配置DASHSCOPE_API_KEY以使用真实的AI服务。"
        
        # 构建消息列表
        messages = [{"role": "system", "content": "你是一个有用的AI助手。"}]
        
        # 添加历史对话（如果有）
        if conversation_history:
            for msg in conversation_history[-10:]:  # 只保留最近10条消息作为上下文
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": message
        })
        
        try:
            completion = client.chat.completions.create(
                model=settings.QWEN_MODEL,
                messages=messages,
                stream=False
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            return f"抱歉，调用AI服务时发生错误：{str(e)}"
    
    @staticmethod
    async def get_ai_response_stream(message: str, conversation_history: Optional[list] = None) -> AsyncGenerator[str, None]:
        """调用通义千问API获取AI回复（流式）"""
        client = AIService._get_client()
        
        # 如果没有配置API密钥，返回模拟响应
        if not client:
            yield f"这是对 '{message}' 的模拟AI回复。请配置DASHSCOPE_API_KEY以使用真实的AI服务。"
            return
        
        # 构建消息列表
        messages = [{"role": "system", "content": "你是一个有用的AI助手。"}]
        
        # 添加历史对话（如果有）
        if conversation_history:
            for msg in conversation_history[-10:]:  # 只保留最近10条消息作为上下文
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": message
        })
        
        try:
            completion = client.chat.completions.create(
                model=settings.QWEN_MODEL,
                messages=messages,
                stream=True
            )
            
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"抱歉，调用AI服务时发生错误：{str(e)}" 