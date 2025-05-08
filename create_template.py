import pandas as pd
from datetime import datetime

# Create a writer for the Excel file
with pd.ExcelWriter('data/excel/insurance_navigator_template.xlsx') as writer:
    # FMEA sheet
    fmea_df = pd.DataFrame({
        'Function': ['Policy Evaluation', 'Document Parsing', 'Compliance Check'],
        'Failure Mode': ['Missing Key Terms', 'OCR Failure', 'Outdated Rules'],
        'Effect of Failure': ['Incomplete Analysis', 'Missing Data', 'False Compliance'],
        'S': [7, 6, 8],
        'O': [4, 5, 3],
        'D': [3, 4, 5],
        'RPN': [84, 120, 120],
        'Cause': ['Incomplete Dictionary', 'Poor Image Quality', 'Regulatory Change'],
        'Current Controls': ['Manual Review', 'Error Logging', 'Regular Updates'],
        'Recommended Action': ['Expand Term Database', 'Image Pre-processing', 'Regulatory Monitoring']
    })
    fmea_df.to_excel(writer, sheet_name='dfmea_policy_compliance_evaluator', index=False)
    
    # Design sheet
    design_df = pd.DataFrame({
        'Category': ['Inputs', 'Outputs', 'Processing', 'Inputs', 'Outputs'],
        'Element': ['User-Submitted Documents', 'Compliance Report', 'NLP Analysis', 'User Preferences', 'Recommendations'],
        'Description': ['Policies, PDFs, forms uploaded via UI', 'Detailed compliance findings with citations', 'Text extraction and semantic analysis', 'User-defined risk tolerance and priorities', 'Actionable steps to address compliance gaps']
    })
    design_df.to_excel(writer, sheet_name='design_io_agent', index=False)

print('Template Excel file created at data/excel/insurance_navigator_template.xlsx') 