import json
import requests
import os
from typing import Annotated, List
from pydantic import Field, BaseModel

from .settings import settings

# 导入 FastMCP 类型
from fastmcp import FastMCP 

# --- 1. 定义输出类型 (返回图像 URL) ---
class ImageResult(BaseModel):
    """
    图像生成结果，返回图片公开访问的URL列表和文件MIME类型。
    """
    file_content: Annotated[List[str], Field(description="生成的图片公开访问URL列表")]
    filename: Annotated[str, Field(description="生成结果文件名，例如: product_image.json")]
    mime_type: Annotated[str, Field(description="返回的文件MIME类型, 必须是 application/json")]


# # --- 2. 配置和 Prompt Engineering (保持不变) ---
# AI_IMAGE_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
# MODEL_NAME = "qwen-image-edit-plus" 

# --- 3. 工具注册函数：register_image_tools (已修正提取逻辑) ---
def register_image_tools(mcp: FastMCP) -> None:
    
    
    @mcp.tool(
        annotations={"title": "generate_product_image", "readOnlyHint": False}
    )
    async def generate_product_image(
        base_image_url: Annotated[str, Field(description="用于编辑或作为参考的原始图片URL")],
        image_prompt: Annotated[str, Field(description="图像生成工具生成的英文指令，包含风格和场景描述")]
    ) -> ImageResult:
        """
        根据文案工具提供的图像指令和基础图片，调用通义万相生成或编辑宣传图片。
        """
                
        # ❗ 在这里引用配置中的值
        AI_IMAGE_API_URL = settings.wanx_api_endpoint
        MODEL_NAME = settings.wanx_model_name
        API_KEY = settings.ai_api_key.get_secret_value()

        # ... (Payload 构建逻辑保持不变)
        try:
            user_text_prompt = f"根据以下英文指令生成最终图片，如果原始图不符合要求，请进行编辑或重绘：{image_prompt}"
            
            payload = {
                "model": MODEL_NAME,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"image": base_image_url}, 
                                {"text": user_text_prompt} 
                            ]
                        }
                    ]
                },
                "parameters": {
                    "n": 2, 
                    "negative_prompt": "blurry, low quality, distorted, bad contrast", 
                    "prompt_extend": True,
                    "watermark": False
                }
            }
            
            headers = {
                # ❗ 使用配置中获取的密钥
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            }
            
            response = requests.post(AI_IMAGE_API_URL, headers=headers, json=payload, timeout=90)
            response_data = response.json()
            
            # --- ❗ 重点修正：处理 API 错误响应 ---
            # 如果请求返回了 DashScope 的错误码 (如 InvalidApiKey)，则直接抛出异常
            if response_data.get('code'):
                error_code = response_data.get('code')
                error_message = response_data.get('message', '未知API错误')
                raise requests.HTTPError(f"DashScope API Error: [{error_code}] {error_message}", response=response)

            # 确保 HTTP 状态码在 200-299 之间
            response.raise_for_status() 

            # --- ❗ 重点修正：提取生成的图片 URL 列表 ---
            image_urls = []
            
            # 路径：output -> choices[0] -> message -> content (这是一个图片对象数组)
            content_array = response_data.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', [])
            
            # 遍历 content 数组，提取每个 { "image": "URL" } 中的 URL
            for item in content_array:
                if isinstance(item, dict) and 'image' in item:
                    image_urls.append(item['image'])
                
            if not image_urls:
                 raise ValueError("AI图像服务成功返回，但未找到任何有效的图片URL。")


            # --- 结果封装与返回 ---
            return ImageResult(
                file_content=image_urls,
                filename="generated_images.json",
                mime_type="application/json"
            )

        except requests.HTTPError as http_e:
            # 处理 HTTP 或 API 错误
            error_details = [f"图像生成失败 (HTTP/API 错误): {str(http_e)}", f"API 返回信息: {http_e.response.text if http_e.response else 'N/A'}"]
            return ImageResult(
                file_content=error_details,
                filename="error_report.json",
                mime_type="application/json"
            )
        except Exception as e:
            # 处理其他如网络或解析错误
            error_details = [f"图像生成过程中发生错误: {str(e)}"]
            return ImageResult(
                file_content=error_details,
                filename="error_report.json",
                mime_type="application/json"
            )