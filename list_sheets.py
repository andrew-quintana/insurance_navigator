import pandas as pd
import sys

if len(sys.argv) < 2:
    print("Usage: python list_sheets.py <excel_file_path>")
    sys.exit(1)

excel_file_path = sys.argv[1]

try:
    xls = pd.ExcelFile(excel_file_path)
    print(f"\nSheets in {excel_file_path}:")
    print("-" * 50)
    for i, sheet_name in enumerate(xls.sheet_names):
        print(f"{i+1}. {sheet_name}")
    print("-" * 50)
    
    print("\nTo process these sheets with the Excel importer, they should be named with these prefixes:")
    print("- FMEA sheets: 'dfmea_' or 'pfmea_'")
    print("- Design sheets: 'design_'")
    print("\nFor example: 'dfmea_policy_compliance_evaluator' or 'design_io_agent'")
except Exception as e:
    print(f"Error reading Excel file: {str(e)}") 