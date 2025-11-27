import sys

from src.server import create_mcp_server
from src.server import get_server_name_with_version


def main():
    try:
        mcp = create_mcp_server()
    except Exception as e:
        print(f'Error create server:{e}',file=sys.stderr)
        sys.exit(1)

    try:
        mcp.run(
            transport = "sse",
            port = 8000,
            host = "0.0.0.0",
            show_banner = False,
        )
    except KeyboardInterrupt:
        print(f"\nShutting down {get_server_name_with_version()}...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error start server:{e}", file=sys.stderr)
        sys.exit(1)
    


if __name__ == "__main__": 
    main()


