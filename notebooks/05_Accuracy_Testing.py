# Fabric Notebook: 05_Accuracy_Testing
# Purpose: Test Data Agent accuracy against Power BI reports as ground truth

# %% [markdown]
# # 05 - Accuracy Testing
# 
# This notebook compares Data Agent responses against Power BI report queries
# to measure accuracy.
# 
# **Key Concept:** 
# Use DAX queries against your existing Power BI semantic model as "ground truth"
# to validate that the Data Agent's SQL produces correct results.

# %% Setup
import json
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass

with open("../config/agent_config.json", "r") as f:
    CONFIG = json.load(f)

from fabric_data_agent_sdk import FabricDataAgentClient

client = FabricDataAgentClient(
    workspace_id=CONFIG["workspace_id"],
    agent_id=CONFIG["agent_id"]
)

# Import sempy for DAX execution
try:
    import sempy.fabric as fabric
    SEMPY_AVAILABLE = True
except ImportError:
    print("⚠️ sempy not available. Install with: pip install sempy-fabric")
    SEMPY_AVAILABLE = False

# %% Configuration
SEMANTIC_MODEL_NAME = "Your Semantic Model"  # Power BI dataset name
TOLERANCE = 0.01  # 1% tolerance for numeric comparisons

# %% Test Case Data Class
@dataclass
class TestCase:
    """Represents a single accuracy test case"""
    question: str
    expected_dax: str
    metric_name: str
    description: Optional[str] = None

# %% Define Test Cases
# Load from config or define inline
TEST_CASES = [
    TestCase(
        question="How many total users?",
        expected_dax='EVALUATE ROW("TotalUsers", DISTINCTCOUNT(UsageMetrics[UserId]))',
        metric_name="TotalUsers",
        description="Count of unique users"
    ),
    TestCase(
        question="What is the average satisfaction rate?",
        expected_dax='EVALUATE ROW("AvgSatisfaction", AVERAGE(UsageMetrics[SatisfactionRate]))',
        metric_name="AvgSatisfaction",
        description="Average satisfaction score"
    ),
    TestCase(
        question="What is the total session count?",
        expected_dax='EVALUATE ROW("TotalSessions", SUM(UsageMetrics[Sessions]))',
        metric_name="TotalSessions",
        description="Sum of all sessions"
    ),
    TestCase(
        question="How many regions do we have?",
        expected_dax='EVALUATE ROW("RegionCount", DISTINCTCOUNT(UsageMetrics[Region]))',
        metric_name="RegionCount",
        description="Count of unique regions"
    )
]

# Save test cases to config
with open("../config/test_cases.json", "w") as f:
    test_data = [{"question": tc.question, "dax": tc.expected_dax, "metric": tc.metric_name} for tc in TEST_CASES]
    json.dump(test_data, f, indent=2)

# %% Accuracy Tester Class
class ReportBasedAccuracyTester:
    """
    Test Data Agent accuracy by comparing against Power BI report (DAX) ground truth.
    """
    
    def __init__(self, agent_client: FabricDataAgentClient, semantic_model: str):
        """
        Initialize the accuracy tester.
        
        Args:
            agent_client: The FabricDataAgentClient instance
            semantic_model: Name of the Power BI semantic model
        """
        self.agent = agent_client
        self.dataset = semantic_model
        self.results = []
    
    def query_report_dax(self, dax_query: str) -> pd.DataFrame:
        """
        Execute DAX query against the Power BI semantic model.
        
        Args:
            dax_query: The DAX query string
        
        Returns:
            DataFrame with query results
        """
        if not SEMPY_AVAILABLE:
            raise RuntimeError("sempy not available")
        
        print(f"   📝 Executing DAX: {dax_query[:80]}...")
        
        df = fabric.evaluate_dax(
            dataset=self.dataset,
            dax_string=dax_query
        )
        
        print(f"   📊 DAX Result Shape: {df.shape}")
        print(f"   📊 DAX Result:\n{df}")
        
        return df
    
    def extract_numeric_value(self, response: dict) -> float:
        """Extract numeric value from agent response"""
        # Try to get from data
        if response.get('data') and len(response['data']) > 0:
            first_row = response['data'][0]
            if isinstance(first_row, (list, tuple)) and len(first_row) > 0:
                return float(first_row[0])
            elif isinstance(first_row, dict):
                return float(list(first_row.values())[0])
        return 0.0
    
    def test_single_case(self, test_case: TestCase, tolerance: float = 0.01) -> Dict:
        """
        Run a single accuracy test.
        
        Args:
            test_case: The test case to run
            tolerance: Acceptable difference ratio (default 1%)
        
        Returns:
            Dictionary with test results
        """
        print(f"\n🧪 Testing: {test_case.question}")
        
        result = {
            "question": test_case.question,
            "metric": test_case.metric_name,
            "status": "unknown",
            "agent_value": None,
            "expected_value": None,
            "difference": None
        }
        
        try:
            # Get agent response
            agent_response = self.agent.query(test_case.question)
            agent_value = self.extract_numeric_value(agent_response)
            result["agent_value"] = agent_value
            print(f"   🤖 Agent Result: {agent_value:,.2f}")
            
            # Get Power BI ground truth
            dax_result = self.query_report_dax(test_case.expected_dax)
            expected_value = float(dax_result.iloc[0, 0])
            result["expected_value"] = expected_value
            print(f"   📊 Report Result: {expected_value:,.2f}")
            
            # Compare
            if expected_value == 0:
                is_match = agent_value == 0
            else:
                difference = abs(agent_value - expected_value) / expected_value
                result["difference"] = difference
                is_match = difference <= tolerance
            
            if is_match:
                result["status"] = "pass"
                print(f"   ✅ PASS")
            else:
                result["status"] = "fail"
                print(f"   ❌ FAIL (difference: {result['difference']:.2%})")
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"   ⚠️ ERROR: {str(e)}")
        
        self.results.append(result)
        return result
    
    def run_test_suite(self, test_cases: List[TestCase]) -> Dict:
        """
        Run all test cases and return summary.
        
        Args:
            test_cases: List of TestCase objects
        
        Returns:
            Dictionary with test suite summary
        """
        print("=" * 60)
        print("📊 RUNNING ACCURACY TEST SUITE")
        print("=" * 60)
        
        self.results = []
        
        for test_case in test_cases:
            self.test_single_case(test_case)
        
        # Calculate summary
        passed = sum(1 for r in self.results if r["status"] == "pass")
        failed = sum(1 for r in self.results if r["status"] == "fail")
        errors = sum(1 for r in self.results if r["status"] == "error")
        total = len(self.results)
        
        accuracy = passed / total if total > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 TEST SUITE SUMMARY")
        print("=" * 60)
        print(f"   Total Tests: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⚠️ Errors: {errors}")
        print(f"   📈 Accuracy: {accuracy:.1%}")
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "accuracy": accuracy,
            "results": self.results
        }
    
    def get_failures(self) -> List[Dict]:
        """Get list of failed test cases"""
        return [r for r in self.results if r["status"] == "fail"]

# %% Run Accuracy Tests
# Note: This requires sempy and a valid Power BI semantic model connection

if SEMPY_AVAILABLE:
    tester = ReportBasedAccuracyTester(client, SEMANTIC_MODEL_NAME)
    summary = tester.run_test_suite(TEST_CASES)
    
    # Get failures for self-learning
    failures = tester.get_failures()
    if failures:
        print(f"\n⚠️ {len(failures)} test(s) failed - consider adding as few-shot examples")
        
        # Save failures for self-learning notebook
        with open("../config/failures.json", "w") as f:
            json.dump(failures, f, indent=2)
else:
    print("⚠️ Skipping accuracy tests - sempy not available")
    print("   To run tests, install sempy: pip install sempy-fabric")

# %% Manual Testing (without sempy)
def manual_accuracy_test(client: FabricDataAgentClient, question: str, expected_value: float):
    """
    Manually test a query when sempy is not available.
    
    Args:
        client: The FabricDataAgentClient instance
        question: Natural language question
        expected_value: The expected numeric result
    """
    print(f"\n🧪 Manual Test: {question}")
    
    response = client.query(question)
    
    print(f"   📝 Generated SQL: {response.get('sql', 'N/A')}")
    print(f"   🤖 Agent Result: {response.get('data', 'N/A')}")
    print(f"   📊 Expected: {expected_value}")
    
    return response

# Example manual test
# manual_accuracy_test(client, "How many total users?", 304671)

# %%
print("\n🎉 Accuracy testing complete! Proceed to 06_Self_Learning notebook.")
