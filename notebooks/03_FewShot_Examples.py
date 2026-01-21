# Fabric Notebook: 03_FewShot_Examples
# Purpose: Add few-shot examples to train the Data Agent

# %% [markdown]
# # 03 - Few-Shot Examples
# 
# This notebook adds example question-SQL pairs to train the agent.
# 
# **Key Concepts:**
# - Categorize examples by use case
# - Validate SQL before adding
# - Extract examples from existing .pbip reports

# %% Setup
import json
import pyodbc
from typing import Dict, List, Optional

with open("../config/agent_config.json", "r") as f:
    CONFIG = json.load(f)

from fabric_data_agent_sdk import FabricDataAgentClient

client = FabricDataAgentClient(
    workspace_id=CONFIG["workspace_id"],
    agent_id=CONFIG["agent_id"]
)

# %% Define SQL Endpoint connection (for validation)
SQL_ENDPOINT = "YOUR_SQL_ENDPOINT.datawarehouse.fabric.microsoft.com"
DATABASE = "YOUR_DATABASE"

def get_sql_connection():
    """Create connection to SQL Endpoint for query validation"""
    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={SQL_ENDPOINT};"
        f"Database={DATABASE};"
        f"Authentication=ActiveDirectoryInteractive;"
        f"Encrypt=Yes;"
    )
    return pyodbc.connect(connection_string)

# %% SQL Validation Function
def validate_sql_query(sql: str, timeout: int = 30) -> Dict:
    """
    Validate SQL query by executing against SQL Endpoint.
    
    Args:
        sql: The SQL query to validate
        timeout: Query timeout in seconds
    
    Returns:
        Dict with validation results
    """
    try:
        conn = get_sql_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # Fetch first row to verify query works
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        
        cursor.close()
        conn.close()
        
        return {
            "valid": True,
            "columns": columns,
            "sample_row": row
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }

# %% Define Few-Shot Examples by Category
FEWSHOT_EXAMPLES = {
    "core_metrics": [
        {
            "question": "How many total users?",
            "sql": """SELECT COUNT(DISTINCT UserId) AS TotalUsers 
FROM dbo.UsageMetrics"""
        },
        {
            "question": "How many active users today?",
            "sql": """SELECT SUM(ActiveUsers) AS TodayActiveUsers 
FROM dbo.UsageMetrics 
WHERE Date = CAST(GETDATE() AS DATE)"""
        },
        {
            "question": "What is the total session count?",
            "sql": """SELECT SUM(Sessions) AS TotalSessions 
FROM dbo.UsageMetrics"""
        }
    ],
    
    "regional_analysis": [
        {
            "question": "Show users by region",
            "sql": """SELECT Region, 
       COUNT(DISTINCT UserId) AS Users
FROM dbo.UsageMetrics
GROUP BY Region
ORDER BY Users DESC"""
        },
        {
            "question": "Which region has the highest satisfaction?",
            "sql": """SELECT TOP 1 Region, 
       AVG(SatisfactionRate) AS AvgSatisfaction
FROM dbo.UsageMetrics
GROUP BY Region
ORDER BY AvgSatisfaction DESC"""
        }
    ],
    
    "time_analysis": [
        {
            "question": "Show last 7 days trend",
            "sql": """SELECT TOP 7 Date, 
       SUM(ActiveUsers) AS DailyActiveUsers,
       SUM(Sessions) AS DailySessions
FROM dbo.UsageMetrics
WHERE Date >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
GROUP BY Date
ORDER BY Date DESC"""
        },
        {
            "question": "Show monthly active users",
            "sql": """SELECT DATEPART(YEAR, Date) AS Year,
       DATEPART(MONTH, Date) AS Month,
       COUNT(DISTINCT UserId) AS MonthlyActiveUsers
FROM dbo.UsageMetrics
GROUP BY DATEPART(YEAR, Date), DATEPART(MONTH, Date)
ORDER BY Year DESC, Month DESC"""
        }
    ],
    
    "product_analysis": [
        {
            "question": "Show usage by product area",
            "sql": """SELECT ProductArea, 
       COUNT(DISTINCT UserId) AS Users,
       SUM(Sessions) AS TotalSessions
FROM dbo.UsageMetrics
GROUP BY ProductArea
ORDER BY Users DESC"""
        },
        {
            "question": "Which product has the best satisfaction?",
            "sql": """SELECT TOP 1 ProductArea, 
       AVG(SatisfactionRate) AS AvgSatisfaction
FROM dbo.UsageMetrics
GROUP BY ProductArea
ORDER BY AvgSatisfaction DESC"""
        }
    ],
    
    "quick_stats": [
        {
            "question": "Summary statistics",
            "sql": """SELECT 
    COUNT(DISTINCT UserId) AS TotalUsers,
    SUM(Sessions) AS TotalSessions,
    AVG(SatisfactionRate) AS AvgSatisfaction,
    MIN(Date) AS DataStartDate,
    MAX(Date) AS DataEndDate
FROM dbo.UsageMetrics"""
        }
    ]
}

# %% Add examples with validation
def add_examples_with_validation(
    client: FabricDataAgentClient,
    examples: Dict[str, List[Dict]],
    validate: bool = True
):
    """
    Add few-shot examples to the agent with optional SQL validation.
    
    Args:
        client: The FabricDataAgentClient instance
        examples: Dictionary of categorized examples
        validate: Whether to validate SQL before adding
    """
    added = 0
    failed = 0
    
    for category, category_examples in examples.items():
        print(f"\n📂 Category: {category}")
        
        for ex in category_examples:
            question = ex["question"]
            sql = ex["sql"]
            
            # Validate if requested
            if validate:
                result = validate_sql_query(sql)
                if not result["valid"]:
                    print(f"   ❌ {question}")
                    print(f"      Error: {result['error']}")
                    failed += 1
                    continue
            
            # Add to agent
            try:
                client.add_example(question=question, sql=sql)
                print(f"   ✅ {question}")
                added += 1
            except Exception as e:
                print(f"   ❌ {question} - {str(e)}")
                failed += 1
    
    print(f"\n📊 Summary: {added} added, {failed} failed")
    return {"added": added, "failed": failed}

# %% Run example addition (set validate=False for demo without connection)
# Set validate=True when you have SQL Endpoint configured
add_examples_with_validation(client, FEWSHOT_EXAMPLES, validate=False)

# %% Extract examples from .pbip (Power BI Project)
def extract_examples_from_pbip(pbip_path: str) -> List[Dict]:
    """
    Extract DAX measures from .pbip and convert to SQL examples.
    
    Args:
        pbip_path: Path to the .pbip report folder
    
    Returns:
        List of example dictionaries
    """
    from pathlib import Path
    
    examples = []
    report_path = Path(pbip_path)
    
    # Read reportExtensions.json for measures
    extensions_path = report_path / "reportExtensions.json"
    if extensions_path.exists():
        with open(extensions_path) as f:
            extensions = json.load(f)
            
        for measure in extensions.get("measures", []):
            # Convert DAX to SQL (simplified example)
            if "DISTINCTCOUNT" in measure.get("expression", ""):
                examples.append({
                    "question": f"How many {measure['name'].lower()}?",
                    "sql": f"SELECT COUNT(DISTINCT column) AS {measure['name']} FROM dbo.table",
                    "source": "pbip",
                    "original_dax": measure["expression"]
                })
    
    return examples

# %% Publish agent with examples
def publish_agent(client: FabricDataAgentClient):
    """Publish the agent to make it available for use"""
    try:
        client.publish()
        print("✅ Agent published successfully!")
    except Exception as e:
        print(f"❌ Error publishing: {str(e)}")

# Uncomment to publish
# publish_agent(client)

# %%
print("\n🎉 Examples added! Proceed to 04_Query_Agent notebook.")
