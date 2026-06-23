from pydantic import BaseModel, Field


class AIConfig(BaseModel):
    """人工智能（OpenAI 兼容接口，如豆包 Ark）配置。"""

    api_key: str = Field(default="", description="AI 接口 API Key")
    base_url: str = Field(default="", description="AI 接口 Base URL")
    model: str = Field(default="", description="默认模型（可选）")


class TTSConfig(BaseModel):
    """语音合成（火山引擎）配置。音色改为单独的列表管理。"""

    api_key: str = Field(default="", description="语音合成 API Key")


class VoicePresetItem(BaseModel):
    """单个音色配置：音色（speaker_id）与资源 ID 一对一。"""

    voice_id: str = Field(default="", description="音色 / Speaker ID")
    name: str = Field(default="", description="显示名称")
    lang: str = Field(default="", description="擅长语言（仅展示用）")
    resource_id: str = Field(default="", description="火山资源 ID")


class VoicePresetList(BaseModel):
    """音色列表（整表覆盖）。"""

    voices: list[VoicePresetItem] = Field(default_factory=list)


class IntegrationConfig(BaseModel):
    """供客户端拉取的聚合配置（按用户）。"""

    ai: AIConfig
    tts: TTSConfig
    voices: list[VoicePresetItem] = Field(default_factory=list)
