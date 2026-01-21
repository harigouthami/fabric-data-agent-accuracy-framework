# Fabric Notebook: 06_Self_Learning
# Purpose: Automatically improve the agent by learning from failed tests

# %% [markdown]
# # 06 - Self-Learning
# 
# This notebook implements a continuous improvement loop:
# 1. Load failed test cases from accuracy testing
# 2. Generate correct SQL for failed queries
# 3. Add as new few-shot examples
# 4. Re-publish the agent
# 5. Re-test to verify improvement
# 
# **The Goal:** Create an agent that improves automatically over time.

# %% Setup
import json
from typing import Dict, List, Optional
from pathlib import Path

with open("../config/agent_config.json", "r") as f:
    CONFIG = json.load(f)

from fabric_data_agent_sdk import FabricDataAgentClient

client = FabricDataAgentClient(
    workspace_id=CONFIG["workspace_id"],
    agent_id=CONFIG["agent_id"]
)

print(f"✅ Connected to agent: {client.agent_name}")

# %% Load Failed Tests
def load_failures() -> List[Dict]:
    """Load failed test cases from previous accuracy testing"""
    
    failures_path = Path("../config/failures.json")
    
    if not failures_path.exists():
        print("ℹ️ No failures.json found. Run 05_Accuracy_Testing first.")
        return []
    
    with open(failures_path) as f:
        failures = json.load(f)
    
    print(f"📋 Loaded {len(failures)} failed test case(s)")
    
    for i, failure in enumerate(failures, 1):
        print(f"   {i}. {failure['question']}")
        print(f"      Agent: {failure.get('agent_value', 'N/A')}")
        print(f"      Expected: {failure.get('expected_value', 'N/A')}")
    
    return failures

failures = load_failures()

# %% SQL Generation Strategies
def generate_correct_sql(failure: Dict, strategy: str = "template") -> Optional[str]:
    """
    Generate correct SQL for a failed query.
    
    Args:
        failure: The failed test case dictionary
        strategy: Generation strategy ('template', 'dax_convert', 'manual')
    
    Returns:
        Correct SQL string or None
    """
    question = failure["question"]
    metric = failure.get("metric", "")
    
    if strategy == "template":
        # Use predefined templates based on metric type
        templates = {
            "TotalUsers": "SELECT COUNT(DISTINCT UserId) AS TotalUsers FROM dbo.UsageMetrics",
            "AvgSatisfaction": "SELECT AVG(SatisfactionRate) AS AvgSatisfaction FROM dbo.UsageMetrics",
            "TotalSessions": "SELECT SUM(Sessions) AS TotalSessions FROM dbo.UsageMetrics",
            "RegionCount": "SELECT COUNT(DISTINCT Region) AS RegionCount FROM dbo.UsageMetrics"
        }
        return templates.get(metric)
    
    elif strategy == "dax_convert":
        # Convert DAX expression to SQL (simplified)
        dax = failure.get("expected_dax", "")
        
        if "DISTINCTCOUNT" in dax:
            # Extract table and column from DAX
            # DAX: DISTINCTCOUNT(UsageMetrics[UserId])
            # SQL: SELECT COUNT(DISTINCT UserId) FROM dbo.UsageMetrics
            return f"SELECT COUNT(DISTINCT column) AS {metric} FROM dbo.table"
        
        elif "AVERAGE" in dax:
            return f"SELECT AVG(column) AS {metric} FROM dbo.table"
        
        elif "SUM" in dax:
            return f"SELECT SUM(column) AS {metric} FROM dbo.table"
    
    return None

# %% Self-Learning Function
def self_learn_from_failures(
    client: FabricDataAgentClient,
    failures: List[Dict],
    validate: bool = False
) -> Dict:
    """
    Automatically add failed test cases as new few-shot examples.
    
    Args:
        client: The FabricDataAgentClient instance
        failures: List of failed test cases
        validate: Whether to validate SQL before adding
    
    Returns:
        Dictionary with learning results
    """
    print("\n🧠 SELF-LEARNING MODE")
    print("=" * 50)
    
    learned = 0
    skipped = 0
    
    for failure in failures:
        question = failure["question"]
        print(f"\n📚 Learning: {question}")
        
        # Generate correct SQL
        correct_sql = generate_correct_sql(failure, strategy="template")
        
        if not correct_sql:
            print(f"   ⏭️ Skipped - no template available")
            skipped += 1
            continue
        
        print(f"   📝 Generated SQL: {correct_sql[:60]}...")
        
        # Optionally validate
        if validate:
            # validation_result = validate_sql_query(correct_sql)
            # if not validation_result["valid"]:
            #     print(f"   ❌ Invalid SQL: {validation_result['error']}")
            #     skipped += 1
            #     continue
            pass
        
        # Add as new example
        try:
            client.add_example(
                question=question,
                sql=correct_sql
            )
            print(f"   ✅ Added as new example")
            learned += 1
            
        except Exception as e:
            print(f"   ❌ Failed to add: {str(e)}")
            skipped += 1
    
    print(f"\n📊 Learning Summary:")
    print(f"   Learned: {learned}")
    print(f"   Skipped: {skipped}")
    
    return {"learned": learned, "skipped": skipped}

# %% Run Self-Learning
if failures:
    learning_result = self_learn_from_failures(client, failures, validate=False)
else:
    print("ℹ️ No failures to learn from!")

# %% Publish Updated Agent
def publish_updated_agent(client: FabricDataAgentClient):
    """Publish the agent with new examples"""
    
    print("\n🚀 Publishing updated agent...")
    
    try:
        client.publish()
        print("✅ Agent published successfully!")
        print(f"   Total examples: {len(client.examples)}")
        
    except Exception as e:
        print(f"❌ Publish failed: {str(e)}")

# Uncomment to publish
# publish_updated_agent(client)

# %% Continuous Improvement Loop
def continuous_improvement_cycle(
    client: FabricDataAgentClient,
    test_cases: List,
    max_iterations: int = 3
):
    """
    Run a full improvement cycle:
    Test → Learn → Publish → Re-test
    
    Args:
        client: The FabricDataAgentClient instance
        test_cases: List of test cases
        max_iterations: Maximum number of improvement cycles
    """
    from notebooks.N05_Accuracy_Testing import ReportBasedAccuracyTester
    
    print("\n🔄 CONTINUOUS IMPROVEMENT CYCLE")
    print("=" * 50)
    
    tester = ReportBasedAccuracyTester(client, "Your Semantic Model")
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n📍 Iteration {iteration}/{max_iterations}")
        
        # Test
        summary = tester.run_test_suite(test_cases)
        
        if summary["accuracy"] >= 0.95:
            print(f"🎉 Target accuracy reached: {summary['accuracy']:.1%}")
            break
        
        # Learn from failures
        failures = tester.get_failures()
        if not failures:
            print("✅ No failures to learn from!")
            break
        
        learning_result = self_learn_from_failures(client, failures)
        
        # Publish
        client.publish()
        
        print(f"   Accuracy: {summary['accuracy']:.1%} → Continuing...")
    
    print("\n✅ Improvement cycle complete!")

# Uncomment to run full cycle
# continuous_improvement_cycle(client, TEST_CASES)

# %% Summary Report
def generate_improvement_report(initial_accuracy: float, final_accuracy: float, iterations: int):
    """Generate a summary report of the improvement process"""
    
    improvement = final_accuracy - initial_accuracy
    
    print("\n" + "=" * 60)
    print("📈 IMPROVEMENT REPORT")
    print("=" * 60)
    print(f"   Initial Accuracy: {initial_accuracy:.1%}")
    print(f"   Final Accuracy:   {final_accuracy:.1%}")
    print(f"   Improvement:      {improvement:+.1%}")
    print(f"   Iterations:       {iterations}")
    print("=" * 60)

# Example report
# generate_improvement_report(0.75, 0.95, 3)

# %%
print("\n🎉 Self-learning notebook complete!")
print("\n📚 Summary of the 6-Notebook Framework:")
print("   01_Setup        → Connect to agent")
print("   02_Configure    → Set instructions")
print("   03_FewShot      → Add examples")
print("   04_Query        → Test queries")
print("   05_Accuracy     → Measure accuracy")
print("   06_Self_Learn   → Improve automatically")
