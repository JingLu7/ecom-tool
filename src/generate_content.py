import json
import requests
import os
from typing import Annotated, Optional
from pydantic import Field, BaseModel

from .settings import settings

# 导入 FastMCP 类型
# 确保您已经正确安装 fast-mcp
from fastmcp import FastMCP 

# --- 1. 定义输出类型 ---
class ContentResult(BaseModel):
    """
    营销内容生成结果，返回包含文案、要素、评分和图像指令的JSON字符串。
    """
    file_content: Annotated[str, Field(description="包含文案、要素、评分和图像指令的JSON字符串")]
    filename: Annotated[str, Field(description="生成结果文件名，例如: content_plan.json")]
    mime_type: Annotated[str, Field(description="返回的文件MIME类型, 必须是 application/json")]


# --- 2. 配置和 Prompt Engineering ---

# # 统一使用 OpenAI 兼容模式的 Endpoint
# AI_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
# # 使用支持结构化输出和多模态的 Qwen 模型
# MODEL_NAME = "qwen2.5-omni-7b" 

SYSTEM_PROMPT = """
你是一位资深的营销专家AI。你的任务是根据提供的商品信息和目标平台，生成高转化文案，并输出严格的JSON结构：
{"copywriting": "文案", "key_elements": ["卖点", "标签"], "image_prompt": "图像指令 (英文)", "score": 8.5}
请确保你的回复中只包含一个完整的JSON对象，不要有任何前言、解释或额外的文本。
"""

# --- 3. 工具注册函数：register_content_tools (含多模态可选逻辑) ---
def register_content_tools(mcp: FastMCP) -> None:
    """
    注册电商内容中台的文案生成工具。
    """
    
    
    @mcp.tool(
        annotations={"title": "generate_marketing_content", "readOnlyHint": False}
    )
    async def generate_marketing_content(
        product_name: Annotated[str, Field(description="商品名称，如：极光无线降噪耳机")],
        product_features: Annotated[str, Field(description="核心卖点或特点描述，如：轻至20g，主动降噪45dB")],
        target_platform: Annotated[str, Field(description="目标推广平台，如：小红书, 抖音, 淘宝")],
        target_audience: Annotated[str, Field(description="目标受众，如：都市白领, 学生党")],
        # ❗ 设置为可选参数，默认为 None
        product_image_url: Annotated[Optional[str], Field(description="可选：原始产品图片URL，用于模型分析视觉元素和生成图像指令。")] = None 
    ) -> ContentResult:
        """
        根据商品信息和可选的图片，一键生成结构化的营销文案、爆款要素、吸引力评分和图像生成指令。
        """
        
        # ❗ 在这里引用配置中的值
        AI_API_URL = settings.qwen_api_endpoint
        MODEL_NAME = settings.qwen_model_name
        API_KEY = settings.ai_api_key.get_secret_value()
        
        
        # 1. 构建基础的用户指令文本
        user_prompt = f"""
        --- 商品信息 ---
        商品名: {product_name}
        核心特点: {product_features}
        --- 营销目标 ---
        目标平台: {target_platform}
        目标受众: {target_audience}
        
        请严格遵循系统提示中的 JSON 格式输出。
        """
        
        # 2. 动态构建用户消息内容数组
        user_content_array = []

        if product_image_url:
            # 强化 Prompt，告知模型已提供图片
            user_prompt += "\n\n请注意：您已收到原始图片，请结合图片的风格和氛围，给出高度相关的图像生成指令(image_prompt)。"
            
            # 添加图片对象 (多模态输入结构)
            user_content_array.append(
                {"type": "image_url", "image_url": {"url": product_image_url}}
            )
        else:
            # 强化 Prompt，告知模型未提供图片
             user_prompt += "\n\n请注意：未收到原始图片，请仅根据文字描述，发挥创造力给出图像生成指令(image_prompt)。"

        # 始终添加文本指令
        user_content_array.append(
            {"type": "text", "text": user_prompt}
        )
        
        # --- 3. 构建并发送请求 Payload ---
        try:
            # 遵循 OpenAI 兼容 API 结构
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content_array}
                ],
                "response_format": {"type": "json_object"}, 
                "stream": False,
                "top_p": 0.8,
                "temperature": 0.7,
            }
            


            headers = {
                "Authorization": f"Bearer {API_KEY}", 
                "Content-Type": "application/json"
            }
            
            response = requests.post(AI_API_URL, headers=headers, json=payload, timeout=30)
            response_data = response.json()
            
            # 检查 DashScope 错误码
            if response_data.get('code'):
                error_code = response_data.get('code')
                error_message = response_data.get('message', '未知API错误')
                # 使用 HTTPError 封装 DashScope 错误，便于统一处理
                raise requests.HTTPError(f"DashScope API Error: [{error_code}] {error_message}", response=response)

            response.raise_for_status() # 检查 HTTP 状态码

            # 提取路径：choices[0] -> message -> content
            # 注意：content 是模型最终生成的 JSON 字符串
            ai_response_json_string = response_data.get('choices', [{}])[0].get('message', {}).get('content', '{}')

            # 验证模型返回的内容是否为有效的 JSON
            try:
                json_content = json.loads(ai_response_json_string)
                # 重新封装为美化的 JSON 字符串（可选）
                final_json_string = json.dumps(json_content, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                # 如果返回的不是严格的 JSON
                raise ValueError(f"AI返回内容格式错误，不是有效的JSON: {ai_response_json_string[:100]}...")

            # --- 结果封装与返回 ---
            return ContentResult(
                file_content=final_json_string,
                filename=f"{product_name}_content_plan.json",
                mime_type="application/json"
            )

        except requests.HTTPError as http_e:
            error_msg = f"API调用失败 (HTTP/DashScope Error): {str(http_e)}"
            if http_e.response and http_e.response.text:
                 error_msg += f"\n详细信息: {http_e.response.text}"
            
            return ContentResult(
                file_content=json.dumps({"error": error_msg}, ensure_ascii=False, indent=2),
                filename="error_report.json",
                mime_type="application/json"
            )
        except Exception as e:
            # 处理其他如网络、解析或Key未设置错误
            return ContentResult(
                file_content=json.dumps({"error": f"内容生成过程中发生内部错误: {str(e)}"}, ensure_ascii=False, indent=2),
                filename="error_report.json",
                mime_type="application/json"
            )