# Fabric Notebook: 02_Configure_Agent
# Purpose: Configure AI instructions and data sources for the Data Agent

# %% [markdown]
# # 02 - Configure Agent
# 
# This notebook configures the Data Agent with:
# - AI instructions for accurate query generation
# - Data source connections (Lakehouse/Warehouse)
# - Behavioral rules to prevent over-interpretation

# %% Load configuration
import json

with open("../config/agent_config.json", "r") as f:
    CONFIG = json.load(f)

print(f"✅ Loaded configuration for workspace: {CONFIG['workspace_id']}")

# %% Initialize client (assumes 01_Setup has been run)
from fabric_data_agent_sdk import FabricDataAgentClient

client = FabricDataAgentClient(
    workspace_id=CONFIG["workspace_id"],
    agent_id=CONFIG["agent_id"]
)

# %% Define AI Instructions
# These instructions guide how the agent interprets questions and generates SQL

AI_INSTRUCTIONS = """
You are a data analytics assistant for product usage metrics.

## YOUR ROLE
Help users explore and analyze product usage data by generating accurate SQL queries.

## CRITICAL RULES - FOLLOW EXACTLY

### Rule 1: Literal Query Matching
- DO NOT expand or enrich simple questions
- If an exact few-shot example match exists, USE THAT SQL without modification
- Do not add extra columns, filters, or aggregations unless explicitly requested

### Rule 2: Clarification Over Assumption
- For ambiguous questions, ASK for clarification instead of guessing
- Example: If user asks "show metrics", ask "Which metrics would you like to see?"

### Rule 3: T-SQL Syntax (IMPORTANT)
- Always use T-SQL syntax, NOT Spark SQL
- Use TOP N instead of LIMIT
- Use DATEADD(DAY, -N, GETDATE()) instead of DATE_SUB
- Use CROSS APPLY for inline subqueries

## DATA CONTEXT

### Primary Table: UsageMetrics
| Column | Type | Description |
|--------|------|-------------|
| Date | DATE | Activity date |
| UserId | VARCHAR | Unique user identifier |
| ProductArea | VARCHAR | Product area name |
| Region | VARCHAR | Geographic region |
| ActiveUsers | INT | Count of active users |
| Sessions | INT | Number of sessions |
| SatisfactionRate | DECIMAL | User satisfaction (0-100) |

### Common Patterns
- User counts: COUNT(DISTINCT UserId)
- Daily metrics: GROUP BY Date ORDER BY Date
- Regional analysis: GROUP BY Region

## RESPONSE FORMAT
- Always return valid T-SQL
- Include meaningful column aliases
- Order results logically (by date DESC, or by metric DESC)
"""

# %% Update agent instructions
def update_agent_instructions(client: FabricDataAgentClient, instructions: str):
    """
    Update the AI instructions for the Data Agent.
    
    Args:
        client: The FabricDataAgentClient instance
        instructions: The instruction text
    """
    try:
        client.update_instructions(instructions)
        print("✅ Instructions updated successfully!")
        print(f"   Character count: {len(instructions)}")
        
    except Exception as e:
        print(f"❌ Error updating instructions: {str(e)}")
        raise

update_agent_instructions(client, AI_INSTRUCTIONS)

# %% Configure data sources
def add_data_source(client: FabricDataAgentClient, lakehouse_id: str, schema: str = "dbo"):
    """
    Add a Lakehouse/Warehouse as a data source for the agent.
    
    Args:
        client: The FabricDataAgentClient instance
        lakehouse_id: The Lakehouse or Warehouse ID
        schema: The schema name (default: dbo)
    """
    try:
        client.add_data_source(
            source_id=lakehouse_id,
            source_type="lakehouse",
            schema=schema
        )
        print(f"✅ Data source added: {lakehouse_id}")
        
    except Exception as e:
        print(f"❌ Error adding data source: {str(e)}")
        raise

# Add the lakehouse as data source
if CONFIG.get("lakehouse_id"):
    add_data_source(client, CONFIG["lakehouse_id"])

# %% Verify configuration
def verify_agent_configuration(client: FabricDataAgentClient):
    """Display current agent configuration"""
    
    print("\n📋 Agent Configuration:")
    print(f"   Name: {client.agent_name}")
    print(f"   Instructions: {len(client.instructions)} characters")
    print(f"   Data Sources: {len(client.data_sources)}")
    
    for ds in client.data_sources:
        print(f"      - {ds['source_type']}: {ds['source_id']}")
    
    print(f"   Examples: {len(client.examples)}")
    
    return True

verify_agent_configuration(client)

# %% 
print("\n🎉 Configuration complete! Proceed to 03_FewShot_Examples notebook.")
