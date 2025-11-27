from pydantic import Field, field_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    
    log_level: str = Field(default="INFO", description="日志等级")

    @field_validator("log_level")
    @classmethod
    def available_log_level(cls, v: str) -> str:
        """
        log_level字段的校验器，检查是否为有效的日志等级
        """
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in allowed_levels:
            raise ValueError(f"log level must be one of {allowed_levels}")
        return v
    

# ----------------------------------------
    # II. AI 接口配置 (基于 DashScope/通义)
    # ----------------------------------------
    
    # --- 通用 API Key ---
    # 使用 SecretStr 确保密钥在打印时不被泄露
    # 注意：在 .env 文件中，键名为 AI_API_KEY
    ai_api_key: SecretStr = Field(default="sk-0ccbc1d7a10e4e22b07b8a5fd3082010", description="访问阿里云DashScope服务的API密钥")

    # --- 文本/多模态 Chat 配置 (Content & Guide Tools) ---
    # 对应于原文中的 ai_text_api_url
    qwen_api_endpoint: str = Field(
        # 默认使用 OpenAI 兼容模式的端点
        default="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", 
        description="通义千问Chat的OpenAI兼容API端点URL"
    )
    # 新增模型名称配置
    qwen_model_name: str = Field(
        default="qwen2.5-omni-7b", 
        description="用于文案生成和指导的多模态模型名称"
    )
    
    # --- 图像生成/编辑配置 (Img Tool) ---
    # 对应于原文中的 ai_image_api_url
    wanx_api_endpoint: str = Field(
        # 默认使用 DashScope 协议的图像生成端点
        default="https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation", 
        description="通义万相图像服务的API端点URL"
    )
    # 新增模型名称配置
    wanx_model_name: str = Field(
        default="qwen-image-edit-plus", 
        description="用于图像生成或编辑的模型名称"
    )

    # ----------------------------------------
    # III. Pydantic 配置 
    # ----------------------------------------

    model_config = SettingsConfigDict(
        # 启用从环境变量和 .env 文件加载
        env_file='.env', 
        env_file_encoding='utf-8', 
        # 允许忽略 .env 中未在类中定义的其他字段
        extra='ignore' 
    )

settings = Settings()