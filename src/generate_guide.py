import json
import requests
import os
from typing import Annotated, Optional
from pydantic import Field, BaseModel

from .settings import settings

# 导入 FastMCP 类型
from fastmcp import FastMCP 

# --- 1. 定义输出类型 (保持不变) ---
class GuideResult(BaseModel):
    """
    营销指导方案结果，返回包含投放策略、合规建议等的JSON字符串。
    """
    file_content: Annotated[str, Field(description="包含指导方案、策略和建议的JSON字符串")]
    filename: Annotated[str, Field(description="生成结果文件名，例如: launch_guide.json")]
    mime_type: Annotated[str, Field(description="返回的文件MIME类型, 必须是 application/json")]


# --- 2. 配置和 Prompt Engineering ---
# # 统一使用 OpenAI 兼容模式的 Endpoint
# AI_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
# # 推荐使用支持多模态的 Qwen-Omni 或 Qwen-VL-Plus
# MODEL_NAME = "qwen2.5-omni-7b" 

GUIDE_SYSTEM_PROMPT = """
你是一位资深的电商内容投放顾问，熟悉小红书、抖音、淘宝等平台的最新运营和合规规则。
你的任务是根据提供的文案、图片URL和目标平台，提供一个详细的落地指导方案。你需要重点分析：视觉风格是否符合平台趋势、图片与文案是否一致、以及图片展示的合规性。

**输出格式要求 (严格遵循 JSON 格式):**
1. "timing_suggestion": "最佳发布时间建议和理由。"
2. "visual_assessment": "基于图片URL对视觉风格、构图和转化潜力的评估及改进建议。"
3. "interaction_strategy": ["如何引导用户评论和互动。", "如何设置话题标签。"]
4. "compliance_risk": ["根据文案和图片，潜在的合规风险提示（如绝对化用语、图片版权）。"]
5. "launch_checklist": ["发布前需检查的事项清单。"]
"""

# --- 3. 工具注册函数：register_guide_tools (已集成 OpenAI 兼容多模态 API) ---
def register_guide_tools(mcp: FastMCP) -> None:
    """
    注册电商内容中台的落地指导方案工具。
    """

    
    @mcp.tool(
        annotations={"title": "get_launch_strategy", "readOnlyHint": True}
    )
    async def get_launch_strategy(
        generated_copywriting: Annotated[str, Field(description="文案工具生成的最终文案主体内容")],
        target_platform: Annotated[str, Field(description="目标推广平台，如：小红书, 抖音, 淘宝")],
        generated_image_url: Annotated[Optional[str], Field(description="可选，图片生成工具返回的宣传图片公开访问URL")] = None
    ) -> GuideResult:
        """
        根据生成的文案、图片URL和目标平台，提供专业的投放策略和合规指导方案。
        """
        
        AI_API_URL = settings.qwen_api_endpoint
        MODEL_NAME = settings.qwen_model_name
        API_KEY = settings.ai_api_key.get_secret_value()
        

        image_analysis_instruction = ""
        user_content_array = []

        if generated_image_url and generated_image_url.strip():
            image_analysis_instruction = "请结合图片URL对视觉风格、构图和转化潜力进行详细评估。"
            user_content_array.append(
                {"type": "image_url", "image_url": {"url": generated_image_url}}
            )
        else:
            # 图片缺失，仅文本分析
            user_analysis_instruction = "图片URL未提供，请重点评估文案与平台规则的契合度，跳过视觉风格评估部分。"

            
        # 1. 构建用户输入 Prompt/指令
        user_instruction = f"""
        请分析以下内容，并提供指导方案：
        目标平台: {target_platform}
        待分析文案: {generated_copywriting}
        请严格遵循系统提示中的 JSON 格式输出。
        {image_analysis_instruction}
        """
        
        user_content_array.append(
            {"type": "text", "text": user_instruction}
        )

        # --- 2. 遵循 OpenAI 兼容 API 结构构建 Payload (多模态输入) ---
        try:
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": GUIDE_SYSTEM_PROMPT},
                    {"role": "user","content": user_content_array}
                ],
                # 关键：开启 JSON 结构化输出
                "response_format": {"type": "json_object"}, 
                
                # 可选参数
                "stream": False,
                "top_p": 0.8,
                "temperature": 0.7,
            }
            
            headers = {
                "Authorization": f"Bearer {API_KEY}", 
                "Content-Type": "application/json"
            }
            
            response = requests.post(AI_API_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status() 
            
            response_data = response.json()
            
            # 提取路径：choices[0] -> message -> content
            ai_response_json_string = response_data.get('choices', [{}])[0].get('message', {}).get('content', '{}')

            # --- 结果封装与返回 ---
            # 尝试解析 JSON 以确认格式，如果解析失败则返回错误提示
            try:
                json.loads(ai_response_json_string) 
                return GuideResult(
                    file_content=ai_response_json_string,
                    filename=f"{target_platform}_launch_guide.json",
                    mime_type="application/json"
                )
            except json.JSONDecodeError:
                 return GuideResult(
                    file_content=json.dumps({"error": "AI返回的指导方案格式不正确。"}),
                    filename="error_guide.json",
                    mime_type="application/json"
                )

        except Exception as e:
            # 处理网络或 API 调用错误
            error_details = json.dumps({"error": f"指导方案生成失败: {str(e)}"})
            return GuideResult(
                file_content=error_details,
                filename="error_report.json",
                mime_type="application/json"
            )