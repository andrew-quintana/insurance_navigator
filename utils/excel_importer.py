import os
import json
import pandas as pd
from datetime import datetime

class ExcelImporter:
    """Simple Excel importer that converts sheets to JSON."""
    
    def __init__(self, excel_file_path):
        """Initialize the importer with the Excel file path."""
        self.excel_file_path = excel_file_path
        
        # Ensure output directories exist
        os.makedirs("docs/fmea", exist_ok=True)
        os.makedirs("docs/design", exist_ok=True)
    
    def list_sheets(self):
        """List all sheets in the Excel file."""
        try:
            xls = pd.ExcelFile(self.excel_file_path)
            sheet_list = [{'title': sheet, 'id': i} for i, sheet in enumerate(xls.sheet_names)]
            print(f"Found {len(sheet_list)} sheets in {self.excel_file_path}")
            return sheet_list
        except Exception as e:
            print(f"Error reading Excel file: {str(e)}")
            return []
    
    def get_sheet_data(self, sheet_name):
        """Get data from a specific sheet."""
        try:
            df = pd.read_excel(self.excel_file_path, sheet_name=sheet_name)
            print(f"Retrieved {len(df)} rows from {sheet_name}")
            return df
        except Exception as e:
            print(f"Error reading sheet {sheet_name}: {str(e)}")
            return pd.DataFrame()
    
    def convert_fmea_to_json(self, df, agent_name):
        """Convert FMEA DataFrame to structured JSON."""
        fmea_entries = []
        
        # Check if DataFrame has expected columns
        expected_cols = ["Function", "Failure Mode", "Effect of Failure", "S", "O", "D"]
        missing_cols = [col for col in expected_cols if col not in df.columns]
        
        if missing_cols:
            print(f"Warning: Missing expected FMEA columns: {missing_cols}")
            # Try to find similar columns
            column_mapping = {}
            for col in missing_cols:
                # Look for similar column names
                for existing_col in df.columns:
                    if col.lower() in existing_col.lower():
                        column_mapping[col] = existing_col
                        print(f"Using '{existing_col}' for '{col}'")
                        break
            
            # Rename columns if mappings found
            if column_mapping:
                df = df.rename(columns={v: k for k, v in column_mapping.items()})
        
        for _, row in df.iterrows():
            try:
                severity = int(row.get("S", 0))
            except (ValueError, TypeError):
                severity = 0
                
            try:
                occurrence = int(row.get("O", 0))
            except (ValueError, TypeError):
                occurrence = 0
                
            try:
                detection = int(row.get("D", 0))
            except (ValueError, TypeError):
                detection = 0
                
            try:
                rpn = int(row.get("RPN", 0))
            except (ValueError, TypeError):
                # Calculate RPN if not provided
                rpn = severity * occurrence * detection
            
            entry = {
                "function": str(row.get("Function", "")),
                "failure_mode": str(row.get("Failure Mode", "")),
                "effect": str(row.get("Effect of Failure", "")),
                "severity": severity,
                "cause": str(row.get("Cause", "")),
                "occurrence": occurrence,
                "current_controls": str(row.get("Current Controls", "")),
                "detection": detection,
                "rpn": rpn,
                "recommended_action": str(row.get("Recommended Action", "")),
                "risk_level": self._calculate_risk_level(rpn)
            }
            fmea_entries.append(entry)
        
        return {
            "agent_name": agent_name,
            "fmea_entries": fmea_entries,
            "metadata": {
                "version": "1.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
        }
    
    def convert_design_to_json(self, df, design_name):
        """Convert Design DataFrame to structured JSON."""
        design_entries = []
        
        # Check if DataFrame has expected columns
        expected_cols = ["Category", "Element", "Description"]
        missing_cols = [col for col in expected_cols if col not in df.columns]
        
        if missing_cols:
            print(f"Warning: Missing expected Design columns: {missing_cols}")
            # Try to find similar columns
            column_mapping = {}
            for col in missing_cols:
                # Look for similar column names
                for existing_col in df.columns:
                    if col.lower() in existing_col.lower():
                        column_mapping[col] = existing_col
                        print(f"Using '{existing_col}' for '{col}'")
                        break
            
            # Rename columns if mappings found
            if column_mapping:
                df = df.rename(columns={v: k for k, v in column_mapping.items()})
        
        for _, row in df.iterrows():
            entry = {
                "category": str(row.get("Category", "")),
                "element": str(row.get("Element", "")),
                "description": str(row.get("Description", ""))
            }
            design_entries.append(entry)
        
        return {
            "design_name": design_name,
            "design_entries": design_entries,
            "metadata": {
                "version": "1.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
        }
    
    def _calculate_risk_level(self, rpn):
        """Calculate risk level based on RPN."""
        if rpn >= 1000:
            return "critical"
        elif rpn >= 500:
            return "high"
        elif rpn >= 200:
            return "medium"
        return "low"
    
    def save_json(self, data, filename, output_dir):
        """Save JSON data to file."""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Saved JSON data to {output_path}")
        return output_path
    
    def is_fmea_sheet(self, df):
        """Check if a DataFrame looks like an FMEA sheet."""
        fmea_indicators = ["Function", "Failure Mode", "Effect", "S", "O", "D", "RPN"]
        matching_cols = sum(1 for col in fmea_indicators if any(col.lower() in c.lower() for c in df.columns))
        return matching_cols >= 4  # If at least 4 FMEA indicators are present
    
    def is_design_sheet(self, df):
        """Check if a DataFrame looks like a Design sheet."""
        design_indicators = ["Category", "Element", "Description", "Input", "Output", "Processing"]
        matching_cols = sum(1 for col in design_indicators if any(col.lower() in c.lower() for c in df.columns))
        return matching_cols >= 2  # If at least 2 design indicators are present
    
    def clean_filename(self, name):
        """Convert a sheet name to a valid filename."""
        # Replace spaces and special characters
        name = name.replace(' ', '_').lower()
        # Remove any characters that aren't alphanumeric, underscore, or hyphen
        name = ''.join(c for c in name if c.isalnum() or c in '_-')
        return name
    
    def process_all_sheets(self):
        """Process all sheets in the Excel file."""
        sheets = self.list_sheets()
        processed_count = 0
        
        for sheet in sheets:
            sheet_name = sheet['title']
            try:
                df = self.get_sheet_data(sheet_name)
                
                if len(df) == 0:
                    print(f"Skipping empty sheet: {sheet_name}")
                    continue
                
                # Check if sheet name starts with standard prefixes
                if sheet_name.lower().startswith(('dfmea_', 'pfmea_')):
                    agent_name = sheet_name.replace('dfmea_', '').replace('pfmea_', '').replace('_', ' ').title()
                    json_data = self.convert_fmea_to_json(df, agent_name)
                    self.save_json(json_data, f"{sheet_name}.json", "docs/fmea")
                    print(f"Processed FMEA sheet: {sheet_name}")
                    processed_count += 1
                    
                elif sheet_name.lower().startswith('design_'):
                    design_name = sheet_name.replace('design_', '').replace('_', ' ').title()
                    json_data = self.convert_design_to_json(df, design_name)
                    self.save_json(json_data, f"{sheet_name}.json", "docs/design")
                    print(f"Processed Design sheet: {sheet_name}")
                    processed_count += 1
                    
                # If not standard naming, try to detect sheet type
                else:
                    # Try to determine if it's an FMEA sheet
                    if "FMEA" in sheet_name or "DFMEA" in sheet_name or self.is_fmea_sheet(df):
                        # Extract agent name from sheet name
                        if "Agent" in sheet_name:
                            parts = sheet_name.split("Agent")
                            agent_name = parts[0].strip()
                            if len(parts) > 1 and "DFMEA" in parts[1]:
                                agent_name = agent_name  # Keep as is
                        else:
                            agent_name = sheet_name.replace("DFMEA", "").replace("FMEA", "").strip()
                        
                        # Clean up agent name
                        agent_name = agent_name.strip()
                        if agent_name.endswith(" "):
                            agent_name = agent_name[:-1]
                        
                        filename = f"dfmea_{self.clean_filename(agent_name)}.json"
                        json_data = self.convert_fmea_to_json(df, agent_name)
                        self.save_json(json_data, filename, "docs/fmea")
                        print(f"Processed FMEA sheet: {sheet_name} as {agent_name}")
                        processed_count += 1
                        
                    # Try to determine if it's a Design sheet
                    elif "DIDO" in sheet_name or self.is_design_sheet(df):
                        design_name = sheet_name.replace("DIDO", "").strip()
                        if not design_name:
                            design_name = sheet_name
                            
                        filename = f"design_{self.clean_filename(design_name)}.json"
                        json_data = self.convert_design_to_json(df, design_name)
                        self.save_json(json_data, filename, "docs/design")
                        print(f"Processed Design sheet: {sheet_name} as {design_name}")
                        processed_count += 1
                    
                    else:
                        print(f"Skipping sheet that doesn't match known types: {sheet_name}")
                
            except Exception as e:
                print(f"Error processing sheet {sheet_name}: {str(e)}")
        
        if processed_count == 0:
            print("\nNo sheets were processed. Please check that your sheets follow the expected format.")
            print("FMEA sheets should have columns like: Function, Failure Mode, Effect of Failure, S, O, D, RPN")
            print("Design sheets should have columns like: Category, Element, Description")
            print("Or rename your sheets to start with 'dfmea_', 'pfmea_', or 'design_'")

def main():
    """Main function to run the Excel importer."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m utils.excel_importer <excel_file_path>")
        return
    
    excel_file_path = sys.argv[1]
    
    if not os.path.exists(excel_file_path):
        print(f"Error: Excel file not found: {excel_file_path}")
        return
    
    print(f"Starting Excel import for file: {excel_file_path}")
    
    # Initialize importer and process all sheets
    importer = ExcelImporter(excel_file_path)
    importer.process_all_sheets()
    
    print("Excel import completed successfully")

if __name__ == "__main__":
    main() 