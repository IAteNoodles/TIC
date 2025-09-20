from connectors.mcp_connector import call_mcp_model

def get_mcp_prediction_tool(prompt: str) -> dict:
    """
    Tool to get a prediction from the MCP model.
    """
    return call_mcp_model(prompt)
