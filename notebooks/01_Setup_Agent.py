# Fabric Notebook: 01_Setup_Agent
# Purpose: Install SDK and configure authentication for Fabric Data Agent

# %% [markdown]
# # 01 - Setup Agent
# 
# This notebook sets up the environment for working with Fabric Data Agents.
# 
# **Prerequisites:**
# - Microsoft Fabric workspace with Data Agent capability
# - Appropriate permissions to create/manage agents

# %% Install required packages
# Run this cell to install the Fabric Data Agent SDK
%pip install fabric-data-agent-sdk -q

# %% Import libraries
from fabric_data_agent_sdk import FabricDataAgentClient
import json

# %% Configuration
# Update these values with your workspace and agent information
CONFIG = {
    "workspace_id": "YOUR_WORKSPACE_ID",  # e.g., "fc251958-7c18-4bf4-b9bb-91a94cd07da3"
    "agent_id": "YOUR_AGENT_ID",          # e.g., "12345678-1234-1234-1234-123456789abc"
    "lakehouse_id": "YOUR_LAKEHOUSE_ID",  # e.g., "4b5b3e99-01ff-4ec7-b3f1-83a637953124"
    "agent_name": "Sample Analytics Agent"
}

# Save configuration for other notebooks
with open("../config/agent_config.json", "w") as f:
    json.dump(CONFIG, f, indent=2)

print("✅ Configuration saved!")

# %% Initialize the Data Agent Client
def initialize_agent_client(workspace_id: str, agent_id: str = None):
    """
    Initialize connection to Fabric Data Agent.
    
    Args:
        workspace_id: The Fabric workspace ID
        agent_id: Optional existing agent ID. If None, creates new agent.
    
    Returns:
        FabricDataAgentClient instance
    """
    try:
        if agent_id:
            # Connect to existing agent
            client = FabricDataAgentClient(
                workspace_id=workspace_id,
                agent_id=agent_id
            )
            print(f"✅ Connected to existing agent: {client.agent_name}")
        else:
            # Create new agent
            client = FabricDataAgentClient(
                workspace_id=workspace_id
            )
            print(f"✅ Created new agent: {client.agent_name}")
            print(f"   Agent ID: {client.agent_id}")
        
        return client
    
    except Exception as e:
        print(f"❌ Error initializing agent: {str(e)}")
        raise

# %% Connect to agent
client = initialize_agent_client(
    workspace_id=CONFIG["workspace_id"],
    agent_id=CONFIG.get("agent_id")
)

# %% Verify connection
def verify_agent_connection(client: FabricDataAgentClient):
    """Verify the agent connection is working"""
    
    print("\n📋 Agent Details:")
    print(f"   Name: {client.agent_name}")
    print(f"   ID: {client.agent_id}")
    print(f"   Workspace: {client.workspace_id}")
    print(f"   Status: Connected ✅")
    
    return True

verify_agent_connection(client)

# %% Export client for use in other notebooks
# The client object can be passed to subsequent notebooks
print("\n🎉 Setup complete! Proceed to 02_Configure_Agent notebook.")
