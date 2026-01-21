# Fabric Notebook: 04_Query_Agent
# Purpose: Interactive testing and querying of the Data Agent

# %% [markdown]
# # 04 - Query Agent
# 
# This notebook provides interactive testing capabilities for the Data Agent.
# 
# **Features:**
# - Send natural language questions
# - View generated SQL
# - Test conversation history

# %% Setup
import json
from typing import Optional

with open("../config/agent_config.json", "r") as f:
    CONFIG = json.load(f)

from fabric_data_agent_sdk import FabricDataAgentClient

client = FabricDataAgentClient(
    workspace_id=CONFIG["workspace_id"],
    agent_id=CONFIG["agent_id"]
)

print(f"✅ Connected to agent: {client.agent_name}")

# %% Query Function
def query_agent(client: FabricDataAgentClient, question: str, verbose: bool = True) -> dict:
    """
    Send a natural language question to the Data Agent.
    
    Args:
        client: The FabricDataAgentClient instance
        question: Natural language question
        verbose: Whether to print detailed output
    
    Returns:
        Dictionary with response details
    """
    if verbose:
        print(f"\n🗣️ Question: {question}")
        print("-" * 50)
    
    try:
        response = client.query(question)
        
        if verbose:
            print(f"📝 Generated SQL:")
            print(f"   {response.get('sql', 'N/A')}")
            print(f"\n📊 Result Preview:")
            if response.get('data'):
                for i, row in enumerate(response['data'][:5]):
                    print(f"   {row}")
                if len(response['data']) > 5:
                    print(f"   ... and {len(response['data']) - 5} more rows")
            print(f"\n⏱️ Execution time: {response.get('execution_time', 'N/A')}ms")
        
        return response
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"error": str(e)}

# %% Test queries
# Core metric queries
print("=" * 60)
print("📊 TESTING CORE METRICS")
print("=" * 60)

query_agent(client, "How many total users?")
query_agent(client, "What is the total session count?")

# %% Regional analysis queries
print("\n" + "=" * 60)
print("🌍 TESTING REGIONAL ANALYSIS")
print("=" * 60)

query_agent(client, "Show users by region")
query_agent(client, "Which region has the highest satisfaction?")

# %% Time-based queries
print("\n" + "=" * 60)
print("📅 TESTING TIME ANALYSIS")
print("=" * 60)

query_agent(client, "Show last 7 days trend")
query_agent(client, "Show monthly active users")

# %% Conversation History
def get_conversation_history(client: FabricDataAgentClient, limit: int = 10):
    """
    Retrieve recent conversation history.
    
    Args:
        client: The FabricDataAgentClient instance
        limit: Maximum number of conversations to retrieve
    """
    try:
        history = client.get_conversation_history(limit=limit)
        
        print(f"\n📜 Recent Conversations (last {limit}):")
        print("-" * 50)
        
        for i, conv in enumerate(history, 1):
            print(f"\n{i}. Question: {conv['question']}")
            print(f"   SQL: {conv['sql'][:80]}..." if len(conv.get('sql', '')) > 80 else f"   SQL: {conv.get('sql', 'N/A')}")
            print(f"   Time: {conv.get('timestamp', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error getting history: {str(e)}")

# Uncomment to view history
# get_conversation_history(client)

# %% Interactive Testing Mode
def interactive_mode(client: FabricDataAgentClient):
    """
    Start an interactive Q&A session with the agent.
    Press 'quit' to exit.
    """
    print("\n🤖 Interactive Mode Started")
    print("   Type your questions below. Type 'quit' to exit.\n")
    
    while True:
        question = input("You: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not question:
            continue
            
        query_agent(client, question)

# Uncomment to start interactive mode
# interactive_mode(client)

# %%
print("\n🎉 Query testing complete! Proceed to 05_Accuracy_Testing notebook.")
