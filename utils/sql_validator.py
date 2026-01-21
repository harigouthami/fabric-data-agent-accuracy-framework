"""
SQL Validator Utility
Validates SQL queries against Fabric SQL Endpoint before adding as examples.
"""

import pyodbc
from typing import Dict, Optional


def get_sql_connection(
    sql_endpoint: str,
    database: str,
    timeout: int = 30
) -> pyodbc.Connection:
    """
    Create a connection to Fabric SQL Endpoint.
    
    Args:
        sql_endpoint: The SQL Endpoint hostname
        database: The database name
        timeout: Connection timeout in seconds
    
    Returns:
        pyodbc Connection object
    """
    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={sql_endpoint};"
        f"Database={database};"
        f"Authentication=ActiveDirectoryInteractive;"
        f"Encrypt=Yes;"
        f"Connection Timeout={timeout};"
    )
    return pyodbc.connect(connection_string)


def validate_sql_query(
    sql: str,
    sql_endpoint: str,
    database: str,
    timeout: int = 30
) -> Dict:
    """
    Validate SQL query by executing against SQL Endpoint.
    
    Args:
        sql: The SQL query to validate
        sql_endpoint: The SQL Endpoint hostname
        database: The database name
        timeout: Query timeout in seconds
    
    Returns:
        Dictionary with validation results:
        - valid: Boolean indicating if query is valid
        - columns: List of column names (if valid)
        - row_count: Number of rows returned (if valid)
        - sample_row: First row of results (if valid)
        - error: Error message (if invalid)
    """
    try:
        conn = get_sql_connection(sql_endpoint, database, timeout)
        cursor = conn.cursor()
        
        # Execute query
        cursor.execute(sql)
        
        # Get column info
        columns = [desc[0] for desc in cursor.description]
        
        # Fetch sample data
        rows = cursor.fetchall()
        sample_row = rows[0] if rows else None
        
        cursor.close()
        conn.close()
        
        return {
            "valid": True,
            "columns": columns,
            "row_count": len(rows),
            "sample_row": sample_row
        }
        
    except pyodbc.Error as e:
        return {
            "valid": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Unexpected error: {str(e)}"
        }


def validate_sql_syntax(sql: str) -> Dict:
    """
    Basic SQL syntax validation without database connection.
    Checks for common T-SQL patterns and potential issues.
    
    Args:
        sql: The SQL query to validate
    
    Returns:
        Dictionary with validation results
    """
    issues = []
    
    sql_upper = sql.upper()
    
    # Check for Spark SQL patterns that should be T-SQL
    if " LIMIT " in sql_upper:
        issues.append("Use 'TOP N' instead of 'LIMIT' for T-SQL")
    
    if "DATE_SUB(" in sql_upper:
        issues.append("Use 'DATEADD(DAY, -N, date)' instead of 'DATE_SUB' for T-SQL")
    
    if "DATE_ADD(" in sql_upper and "DATEADD(" not in sql_upper:
        issues.append("Use 'DATEADD()' instead of 'DATE_ADD()' for T-SQL")
    
    if "CURRENT_DATE" in sql_upper and "GETDATE()" not in sql_upper:
        issues.append("Use 'GETDATE()' or 'CAST(GETDATE() AS DATE)' instead of 'CURRENT_DATE' for T-SQL")
    
    # Check for basic SQL structure
    if not any(keyword in sql_upper for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE"]):
        issues.append("Query must start with SELECT, INSERT, UPDATE, or DELETE")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues
    }


def convert_spark_to_tsql(sql: str) -> str:
    """
    Convert common Spark SQL patterns to T-SQL.
    
    Args:
        sql: Spark SQL query
    
    Returns:
        T-SQL equivalent query
    """
    import re
    
    result = sql
    
    # LIMIT N -> TOP N
    limit_match = re.search(r'\sLIMIT\s+(\d+)', result, re.IGNORECASE)
    if limit_match:
        n = limit_match.group(1)
        # Remove LIMIT clause
        result = re.sub(r'\sLIMIT\s+\d+', '', result, flags=re.IGNORECASE)
        # Add TOP after SELECT
        result = re.sub(r'SELECT\s+', f'SELECT TOP {n} ', result, count=1, flags=re.IGNORECASE)
    
    # DATE_SUB(date, N) -> DATEADD(DAY, -N, date)
    result = re.sub(
        r"DATE_SUB\(([^,]+),\s*(\d+)\)",
        r"DATEADD(DAY, -\2, \1)",
        result,
        flags=re.IGNORECASE
    )
    
    # CURRENT_DATE -> CAST(GETDATE() AS DATE)
    result = re.sub(
        r"CURRENT_DATE",
        "CAST(GETDATE() AS DATE)",
        result,
        flags=re.IGNORECASE
    )
    
    return result


if __name__ == "__main__":
    # Example usage
    test_queries = [
        "SELECT * FROM dbo.Users LIMIT 10",
        "SELECT * FROM dbo.Users WHERE Date >= DATE_SUB(CURRENT_DATE, 7)",
        "SELECT TOP 10 * FROM dbo.Users WHERE Date >= DATEADD(DAY, -7, GETDATE())"
    ]
    
    for query in test_queries:
        print(f"\nOriginal: {query}")
        
        syntax_check = validate_sql_syntax(query)
        if not syntax_check["valid"]:
            print(f"Issues: {syntax_check['issues']}")
            converted = convert_spark_to_tsql(query)
            print(f"Converted: {converted}")
        else:
            print("✅ Valid T-SQL syntax")
