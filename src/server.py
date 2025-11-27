from typing import cast
from fastmcp import FastMCP
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware
from fastmcp.utilities import logging
from fastmcp.utilities.logging import configure_logging
from fastmcp.settings import LOG_LEVEL


from .settings import settings
from .generate_content import register_content_tools
from .generate_img import register_image_tools
from .generate_guide import register_guide_tools

logger = logging.get_logger(__name__)


def get_server_name_with_version() -> str:
    return "ecom-content-agent-server"
def create_mcp_server() -> FastMCP:
    
    configure_logging(level=cast(LOG_LEVEL, settings.log_level))
    mcp_server = FastMCP(name=get_server_name_with_version(),
                         instructions="专为电商和社交媒体设计的AI内容策略与生成工具。可以根据商品信息，一键生成高转化文案、宣传图片URL以及专业的投放指导方案。"
                         )
    

    # Add middleware in logical order
    mcp_server.add_middleware(ErrorHandlingMiddleware(logger=logger))
    mcp_server.add_middleware(RateLimitingMiddleware(max_requests_per_second=10))
    mcp_server.add_middleware(TimingMiddleware())
    mcp_server.add_middleware(LoggingMiddleware())
    
    # Register all tools
    register_content_tools(mcp_server)
    register_image_tools(mcp_server)
    register_guide_tools(mcp_server)

    
    return mcp_server