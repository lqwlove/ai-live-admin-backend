from pydantic import BaseModel, Field


class AIConfig(BaseModel):
    """人工智能（OpenAI 兼容接口，如豆包 Ark）配置。"""

    api_key: str = Field(default="", description="AI 接口 API Key")
    base_url: str = Field(default="", description="AI 接口 Base URL")
    model: str = Field(default="", description="默认模型（可选）")


class TTSConfig(BaseModel):
    """语音合成（火山引擎）配置。"""

    api_key: str = Field(default="", description="语音合成 API Key")
    speaker_id: str = Field(default="", description="音色 / Speaker ID")
    resource_id: str = Field(default="", description="资源 ID")


class IntegrationConfig(BaseModel):
    """供客户端拉取的聚合配置。"""

    ai: AIConfig
    tts: TTSConfig
