

tools=[{
    "mcpServers": {
        "base_tools": {
            "command": "python3",
            "args": [
                "-m",
                "app.core.mcp.base_tools"
            ]
        },
        "knowledge_graph": {
            "command": "python3",
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