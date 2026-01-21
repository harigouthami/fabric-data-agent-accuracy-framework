# Fabric Data Agent Accuracy Testing & Self-Learning Framework

[![Microsoft Fabric](https://img.shields.io/badge/Microsoft%20Fabric-Data%20Agent-blue)](https://learn.microsoft.com/fabric/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Build **production-ready, self-learning Fabric Data Agents** using the Fabric Data Agent SDK with accuracy testing against Power BI reports as ground truth.

## 📋 Overview

This sample demonstrates:
- Setting up a Fabric Data Agent using the Python SDK
- Configuring AI instructions for consistent query behavior  
- Adding few-shot examples with SQL validation
- Accuracy testing using DAX queries as ground truth
- Self-learning loop that auto-improves from failures

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE KNOWLEDGE TRIANGLE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│     ┌──────────────┐                    ┌──────────────┐        │
│     │   .pbip      │───Knowledge Base──▶│  Data Agent  │        │
│     │  Report      │                    │  (SDK)       │        │
│     │  (JSON/DAX)  │                    │              │        │
│     └──────┬───────┘                    └──────┬───────┘        │
│            │                                    │                │
│            │         Accuracy Testing           │                │
│            │◀──────────────────────────────────▶│                │
│            │                                    ▼                │
│     ┌──────────────┐                    ┌──────────────┐        │
│     │  DAX Query   │    Compare Results │  SQL Query   │        │
│     │  (Ground     │◀──────────────────▶│  (Agent      │        │
│     │   Truth)     │                    │   Response)  │        │
│     └──────────────┘                    └──────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Prerequisites

| Requirement | Details |
|-------------|---------|
| Microsoft Fabric Workspace | With Data Agent capability enabled |
| Lakehouse | With SQL Analytics Endpoint |
| Python | 3.9 or higher |
| Fabric Data Agent SDK | `pip install fabric-data-agent-sdk` |
| (Optional) Power BI Report | For accuracy testing against DAX |

## 📁 Repository Structure

```
Data-Agent-Accuracy-Framework/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── notebooks/
│   ├── 01_Setup_Agent.py        # Initialize Data Agent client
│   ├── 02_Configure_Agent.py    # Set AI instructions
│   ├── 03_FewShot_Examples.py   # Add validated examples
│   ├── 04_Query_Agent.py        # Interactive querying
│   ├── 05_Accuracy_Testing.py   # Test against Power BI
│   └── 06_Self_Learning.py      # Auto-improve loop
├── sample-data/
│   ├── sample_usage_data.csv    # Synthetic test data (35 rows)
│   └── sample_measures.json     # Sample DAX measures
├── config/
│   ├── agent_config.json        # Agent connection settings
│   └── test_cases.json          # Accuracy test definitions
└── utils/
    ├── sql_validator.py         # SQL Endpoint validator
    └── pbip_extractor.py        # Extract DAX from .pbip files
```

## 🚀 Deployment Steps

### Step 1: Create Fabric Resources

1. **Create a Fabric Workspace** with Data Agent capability
2. **Create a Lakehouse** to store your data
3. **Create a Data Agent** in the workspace
4. **Note down IDs:**
   - Workspace ID (from URL: `/groups/{workspace_id}/`)
   - Agent ID (from URL: `/agents/{agent_id}/`)
   - SQL Endpoint connection string

### Step 2: Upload Sample Data

1. Upload `sample-data/sample_usage_data.csv` to your Lakehouse
2. The data will appear in the SQL Analytics Endpoint

### Step 3: Configure the Sample

Edit `config/agent_config.json`:
```json
{
    "workspace_id": "YOUR-WORKSPACE-GUID",
    "agent_id": "YOUR-AGENT-GUID",
    "lakehouse_name": "YOUR-LAKEHOUSE-NAME",
    "sql_endpoint": "YOUR-SQL-ENDPOINT-CONNECTION-STRING"
}
```

### Step 4: Install Dependencies

```bash
pip install fabric-data-agent-sdk sempy-fabric pandas pyodbc
```

### Step 5: Run Notebooks in Order

| Order | Notebook | What It Does |
|-------|----------|--------------|
| 1 | 01_Setup_Agent.py | Authenticates and connects to agent |
| 2 | 02_Configure_Agent.py | Sets AI behavior instructions |
| 3 | 03_FewShot_Examples.py | Adds validated query examples |
| 4 | 04_Query_Agent.py | Tests interactive queries |
| 5 | 05_Accuracy_Testing.py | Validates against Power BI DAX |
| 6 | 06_Self_Learning.py | Runs auto-improvement loop |

## 💡 Key Concepts

### T-SQL vs Spark SQL

The Data Agent queries SQL Endpoint which uses **T-SQL**, not Spark SQL:

```sql
-- ✅ Correct (T-SQL)
SELECT TOP 10 * FROM dbo.UsageData
SELECT DATEADD(DAY, -7, GETDATE()) AS LastWeek

-- ❌ Incorrect (Spark SQL - will fail!)  
SELECT * FROM dbo.UsageData LIMIT 10
SELECT DATE_SUB(CURRENT_DATE, 7) AS LastWeek
```

### Accuracy Testing Pattern

```python
# Agent produces SQL result
agent_result = agent.query("How many active users last week?")

# Power BI produces DAX result (ground truth)
dax = 'EVALUATE ROW("Users", [ActiveUsersLastWeek])'
dax_result = fabric.evaluate_dax(dataset, dax)

# Compare with tolerance
difference_pct = abs(agent_result - dax_result) / dax_result * 100
assert difference_pct < 1.0, f"Difference: {difference_pct}%"
```

## 🧪 Sample Data

The `sample-data/` folder contains **synthetic data** for demonstration:

| File | Description |
|------|-------------|
| `sample_usage_data.csv` | 35 rows of synthetic product usage metrics |
| `sample_measures.json` | 8 sample DAX measure definitions |

> ⚠️ **Note:** Replace with your own data for production use.

## 🔗 Related Resources

- [Fabric Data Agent Documentation](https://learn.microsoft.com/fabric/data-science/data-agent)
- [Fabric Data Agent with GitHub Copilot Agent Mode](https://community.fabric.microsoft.com/t5/Data-Engineering-Community-Blog/Fabric-Data-Agent-with-GitHub-Copilot-Agent-Mode/ba-p/4791168)
- [Power BI Development with GitHub Copilot and .pbip](https://community.fabric.microsoft.com/t5/Power-BI-Community-Blog/Revolutionizing-Power-BI-Development-Create-Dashboards-in/ba-p/4906244)

## 🤝 Contributing

This project welcomes contributions. Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 👤 Author

**N.Hari Gouthami** - Microsoft  
[GitHub](https://github.com/harn_microsoft)
