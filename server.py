from datetime import datetime
from fastmcp import FastMCP



mcp = FastMCP("lab-server")

@mcp.tool
def simple_add(a : int, b: int) -> int:
    """Add two whole numbers and return the sum. Use this for any addition"""
    return a + b



@mcp.tool
def c_time() -> str:
    """Return the current local date and time on this computer (no time zone)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool
def c_word(s: str) -> int:
    """Enter a word and count how many letters are there"""
    return len(s)


if __name__ == "__main__":
    mcp.run()