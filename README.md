# Ecom-Tool 项目 README 文档

## 📝 项目简介

Ecom-Tool 是一个专为电商和社交媒体设计的 AI 内容策略与生成工具。它能够根据商品信息，一键生成高转化文案、宣传图片以及专业的投放指导方案。 

本项目基于 FastMCP 框架构建，提供了三个核心工具，帮助电商运营人员快速生成优质的营销内容。

## ✨ 功能特性

### 1. 营销文案生成
- 根据商品名称、特点、目标平台和受众自动生成高转化文案
- 支持多模态输入（可选提供产品图片进行分析）
- 输出包含文案、关键卖点、吸引力评分和图像生成指令的结构化 JSON 

### 2. 产品图片生成/编辑
- 基于原始图片和文案工具生成的图像指令，自动生成或编辑宣传图片
- 使用通义万相图像生成服务，支持风格转换和场景优化
- 一次可生成多张图片供选择 

### 3. 投放策略指导
- 提供专业的内容投放策略和合规建议
- 分析文案和图片的视觉风格、平台契合度
- 给出最佳发布时间、互动策略和合规风险提示 

## 🛠 技术栈

- **框架**: FastMCP (Model Context Protocol)
- **AI 服务**: 
  - 阿里云 DashScope - 通义千问 (文案生成和策略指导)
  - 阿里云 DashScope - 通义万相 (图像生成/编辑)
- **传输协议**: SSE (Server-Sent Events)
- **配置管理**: Pydantic Settings
- **依赖管理**: uv 
## 📦 安装说明

### 前置要求
- Python 3.8+
- uv 包管理器

### 安装步骤

1. 克隆项目仓库
```bash
git clone <repository-url>
cd ecom-tool
```

2. 安装依赖
```bash
uv sync
```

## ⚙️ 配置说明

### 环境变量配置

创建 `.env` 文件并配置以下参数：

```env
# AI API 密钥（必填）
AI_API_KEY=your_dashscope_api_key

# 日志级别（可选，默认：INFO）
LOG_LEVEL=INFO

# 通义千问配置（可选）
QWEN_API_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
QWEN_MODEL_NAME=qwen2.5-omni-7b

# 通义万相配置（可选）
WANX_API_ENDPOINT=https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
WANX_MODEL_NAME=qwen-image-edit-plus
``` 
### 关键配置项说明

- `AI_API_KEY`: 阿里云 DashScope 服务的 API 密钥（**必须配置**）
- `LOG_LEVEL`: 支持 DEBUG, INFO, WARNING, ERROR, CRITICAL
- `QWEN_MODEL_NAME`: 用于文案和策略生成的多模态模型
- `WANX_MODEL_NAME`: 用于图像生成的模型
  
## 🚀 使用方法

### 启动服务

```bash
uv run main.py
```

服务将在 `http://0.0.0.0:8080` 启动，使用 SSE 协议提供 MCP 服务。 

### 中间件配置

服务器配置了以下中间件以确保稳定性和可观测性：
- 错误处理中间件
- 速率限制（10 请求/秒）
- 性能计时中间件
- 日志记录中间件 

## 🔧 API 工具说明

### 1. generate_marketing_content

**功能**: 生成营销文案及策略

**输入参数**:
- `product_name`: 商品名称
- `product_features`: 核心卖点或特点描述
- `target_platform`: 目标平台（小红书、抖音、淘宝等）
- `target_audience`: 目标受众
- `product_image_url`: （可选）产品图片 URL

**输出**: JSON 格式的文案、关键要素、评分和图像指令 

### 2. generate_product_image

**功能**: 生成或编辑产品宣传图片

**输入参数**:
- `base_image_url`: 原始图片 URL
- `image_prompt`: 图像生成指令（通常由文案工具生成）

**输出**: 生成的图片 URL 列表（JSON 格式） 
### 3. get_launch_strategy

**功能**: 获取投放策略和合规指导

**输入参数**:
- `generated_copywriting`: 生成的文案内容
- `target_platform`: 目标平台
- `generated_image_url`: （可选）生成的图片 URL

**输出**: 包含发布时间建议、视觉评估、互动策略、合规风险和检查清单的 JSON 

## ⚠️ 注意事项

1. **API 密钥安全**: 请妥善保管 DashScope API 密钥，不要将其提交到版本控制系统
2. **速率限制**: 服务器配置了 10 请求/秒的速率限制，请合理安排请求频率
3. **超时设置**: 
   - 文案生成接口超时时间为 30 秒
   - 图像生成接口超时时间为 90 秒
   - 策略指导接口超时时间为 60 秒
4. **多模态支持**: 文案和策略工具支持可选的图片输入，以提供更精准的分析
5. **平台适配**: 目前主要支持小红书、抖音、淘宝等主流电商和社交平台

## 📄 输出格式说明

所有工具的输出均为 JSON 格式，便于后续处理和集成：

- **文案工具**: 返回结构化的营销内容方案 
- **图片工具**: 返回图片 URL 列表 
- **策略工具**: 返回详细的投放指导方案 

## 📝 Notes

- 本项目使用阿里云 DashScope 服务，需要有效的 API 密钥才能运行
- 服务器名称为 "ecom-content-agent-server" 
- 项目采用模块化设计，各功能工具独立注册，便于扩展和维护 
- 所有 AI 调用都经过错误处理，确保在 API 失败时返回友好的错误信息而不是崩溃
