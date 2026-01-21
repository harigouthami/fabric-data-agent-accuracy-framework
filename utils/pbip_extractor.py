"""
PBIP Extractor Utility
Extract knowledge from Power BI Project (.pbip) files to create agent examples.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional


def extract_knowledge_from_pbip(pbip_path: str) -> Dict:
    """
    Extract business logic and measures from a .pbip report folder.
    
    Args:
        pbip_path: Path to the .pbip report folder
    
    Returns:
        Dictionary containing:
        - measures: List of DAX measures
        - tables: List of tables
        - relationships: List of relationships
        - custom_measures: Measures from reportExtensions
    """
    report_path = Path(pbip_path)
    
    knowledge = {
        "measures": [],
        "tables": [],
        "relationships": [],
        "custom_measures": [],
        "visuals": []
    }
    
    # Read reportExtensions.json for custom measures
    extensions_path = report_path / "reportExtensions.json"
    if extensions_path.exists():
        with open(extensions_path, encoding='utf-8') as f:
            try:
                extensions = json.load(f)
                knowledge["custom_measures"] = extensions.get("measures", [])
            except json.JSONDecodeError:
                pass
    
    # Read definition/model.tmdl or model.json for model info
    model_tmdl_path = report_path / "definition" / "model.tmdl"
    model_json_path = report_path / "definition" / "model.json"
    
    if model_tmdl_path.exists():
        knowledge["measures"] = extract_measures_from_tmdl(model_tmdl_path)
    elif model_json_path.exists():
        with open(model_json_path, encoding='utf-8') as f:
            try:
                model = json.load(f)
                knowledge["tables"] = model.get("tables", [])
                knowledge["relationships"] = model.get("relationships", [])
            except json.JSONDecodeError:
                pass
    
    # Read report.json for visual information
    report_json_path = report_path / "definition" / "report.json"
    if report_json_path.exists():
        with open(report_json_path, encoding='utf-8') as f:
            try:
                report = json.load(f)
                knowledge["visuals"] = extract_visual_info(report)
            except json.JSONDecodeError:
                pass
    
    return knowledge


def extract_measures_from_tmdl(tmdl_path: Path) -> List[Dict]:
    """
    Extract measures from TMDL (Tabular Model Definition Language) file.
    
    Args:
        tmdl_path: Path to the .tmdl file
    
    Returns:
        List of measure dictionaries
    """
    measures = []
    
    with open(tmdl_path, encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex to extract measures
    # Pattern: measure Name = DAX_EXPRESSION
    measure_pattern = r'measure\s+(\w+)\s*=\s*([^\n]+(?:\n\s+[^\n]+)*)'
    
    matches = re.findall(measure_pattern, content, re.MULTILINE)
    
    for name, expression in matches:
        measures.append({
            "name": name.strip(),
            "expression": expression.strip()
        })
    
    return measures


def extract_visual_info(report_json: Dict) -> List[Dict]:
    """
    Extract visual information from report.json.
    
    Args:
        report_json: The parsed report.json content
    
    Returns:
        List of visual information dictionaries
    """
    visuals = []
    
    for section in report_json.get("sections", []):
        for visual_container in section.get("visualContainers", []):
            config = visual_container.get("config", "{}")
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except:
                    continue
            
            visual_type = config.get("singleVisual", {}).get("visualType", "unknown")
            
            visuals.append({
                "type": visual_type,
                "page": section.get("displayName", "Unknown"),
                "config": config
            })
    
    return visuals


def create_agent_examples_from_pbip(pbip_knowledge: Dict) -> List[Dict]:
    """
    Convert Power BI DAX measures to Data Agent few-shot examples.
    
    Args:
        pbip_knowledge: Knowledge extracted from .pbip
    
    Returns:
        List of example dictionaries with question and SQL
    """
    examples = []
    
    all_measures = pbip_knowledge.get("measures", []) + pbip_knowledge.get("custom_measures", [])
    
    for measure in all_measures:
        name = measure.get("name", "")
        expression = measure.get("expression", "")
        
        if not expression:
            continue
        
        example = convert_dax_to_example(name, expression)
        if example:
            examples.append(example)
    
    return examples


def convert_dax_to_example(measure_name: str, dax_expression: str) -> Optional[Dict]:
    """
    Convert a single DAX measure to a SQL example.
    
    Args:
        measure_name: Name of the measure
        dax_expression: DAX expression
    
    Returns:
        Example dictionary or None if conversion not possible
    """
    dax_upper = dax_expression.upper()
    
    # Pattern: DISTINCTCOUNT(Table[Column])
    if "DISTINCTCOUNT" in dax_upper:
        match = re.search(r"DISTINCTCOUNT\((\w+)\[(\w+)\]\)", dax_expression, re.IGNORECASE)
        if match:
            table, column = match.groups()
            return {
                "question": f"How many total {measure_name.lower()}?",
                "sql": f"SELECT COUNT(DISTINCT {column}) AS {measure_name} FROM dbo.{table}",
                "source": "pbip_measure",
                "original_dax": dax_expression
            }
    
    # Pattern: SUM(Table[Column])
    elif "SUM(" in dax_upper and "SUMX" not in dax_upper:
        match = re.search(r"SUM\((\w+)\[(\w+)\]\)", dax_expression, re.IGNORECASE)
        if match:
            table, column = match.groups()
            return {
                "question": f"What is the total {measure_name.lower()}?",
                "sql": f"SELECT SUM({column}) AS {measure_name} FROM dbo.{table}",
                "source": "pbip_measure",
                "original_dax": dax_expression
            }
    
    # Pattern: AVERAGE(Table[Column])
    elif "AVERAGE(" in dax_upper:
        match = re.search(r"AVERAGE\((\w+)\[(\w+)\]\)", dax_expression, re.IGNORECASE)
        if match:
            table, column = match.groups()
            return {
                "question": f"What is the average {measure_name.lower()}?",
                "sql": f"SELECT AVG(CAST({column} AS FLOAT)) AS {measure_name} FROM dbo.{table}",
                "source": "pbip_measure",
                "original_dax": dax_expression
            }
    
    # Pattern: COUNT(Table[Column])
    elif "COUNT(" in dax_upper and "DISTINCTCOUNT" not in dax_upper:
        match = re.search(r"COUNT\((\w+)\[(\w+)\]\)", dax_expression, re.IGNORECASE)
        if match:
            table, column = match.groups()
            return {
                "question": f"How many {measure_name.lower()}?",
                "sql": f"SELECT COUNT({column}) AS {measure_name} FROM dbo.{table}",
                "source": "pbip_measure",
                "original_dax": dax_expression
            }
    
    # Pattern: MAX(Table[Column])
    elif "MAX(" in dax_upper:
        match = re.search(r"MAX\((\w+)\[(\w+)\]\)", dax_expression, re.IGNORECASE)
        if match:
            table, column = match.groups()
            return {
                "question": f"What is the maximum {measure_name.lower()}?",
                "sql": f"SELECT MAX({column}) AS {measure_name} FROM dbo.{table}",
                "source": "pbip_measure",
                "original_dax": dax_expression
            }
    
    # Pattern: MIN(Table[Column])
    elif "MIN(" in dax_upper:
        match = re.search(r"MIN\((\w+)\[(\w+)\]\)", dax_expression, re.IGNORECASE)
        if match:
            table, column = match.groups()
            return {
                "question": f"What is the minimum {measure_name.lower()}?",
                "sql": f"SELECT MIN({column}) AS {measure_name} FROM dbo.{table}",
                "source": "pbip_measure",
                "original_dax": dax_expression
            }
    
    return None


if __name__ == "__main__":
    # Example usage
    print("PBIP Extractor Utility")
    print("=" * 50)
    
    # Test with sample measures
    sample_measures = [
        {"name": "TotalUsers", "expression": "DISTINCTCOUNT(UsageMetrics[UserId])"},
        {"name": "TotalSessions", "expression": "SUM(UsageMetrics[Sessions])"},
        {"name": "AvgSatisfaction", "expression": "AVERAGE(UsageMetrics[SatisfactionRate])"}
    ]
    
    for measure in sample_measures:
        example = convert_dax_to_example(measure["name"], measure["expression"])
        if example:
            print(f"\nDAX: {measure['expression']}")
            print(f"Question: {example['question']}")
            print(f"SQL: {example['sql']}")
