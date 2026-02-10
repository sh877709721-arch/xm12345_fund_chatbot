

tools=[{
    "mcpServers": {
        "base_tools": {
            "command": "python",
            "args": [
                "-m",
                "app.core.mcp.base_tools"
            ]
        },
        "knowledge_graph": {
            "command": "python",
            "args": [
                "-m",
                "app.core.mcp.graphrag"
            ]
        },
        
        # "intent_recognition": {
        #     "command": "python",
        #     "args": [
        #         "-m",
        #         "app.core.mcp.intent"
        #     ]
        # }
    }
}]