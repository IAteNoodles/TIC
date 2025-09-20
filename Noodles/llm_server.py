from fastmcp import FastMCP
import socket

mcp = FastMCP("TIC")

@mcp.tool("say_hello")
def say_hello(name: str) -> str:
    """
    A simple function to say hello.

    Args:
        name (str): The name to greet.

    Returns:
        str: A greeting message.
    """
    return f"Hello, {name}!"

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8005

    # Get local IP address
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"Server running at http://{host}:{port}")
    print(f"Local network URL: http://{local_ip}:{port}")

    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        log_level="debug"
    )