import os
import json
import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class SheetImporter:
    """Simple Google Sheets importer that converts sheets to JSON."""
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self, spreadsheet_id, credentials_path="config/google_credentials.json", debug_mode=False):
        """Initialize the importer with spreadsheet ID and credentials path."""
        self.spreadsheet_id = spreadsheet_id
        self.credentials_path = credentials_path
        self.token_path = "config/token.json"
        self.service = None
        self.debug_mode = debug_mode
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.credentials_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
    
    def authenticate(self):
        """Authenticate with Google Sheets API."""
        # In debug mode, don't actually authenticate
        if self.debug_mode:
            print("[DEBUG] Skipping authentication in debug mode")
            return
            
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('sheets', 'v4', credentials=creds)
        print("Successfully authenticated with Google Sheets API")
    
    def list_sheets(self):
        """List all sheets in the spreadsheet."""
        if self.debug_mode:
            print("[DEBUG] Using mock sheet list in debug mode")
            return [
                {'title': 'dfmea_policy_compliance_evaluator', 'id': '123'},
                {'title': 'design_io_agent', 'id': '456'}
            ]
            
        if not self.service:
            self.authenticate()
        
        sheets = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        sheet_list = [
            {
                'title': sheet['properties']['title'],
                'id': sheet['properties']['sheetId']
            }
            for sheet in sheets.get('sheets', [])
        ]
        
        print(f"Found {len(sheet_list)} sheets")
        return sheet_list
    
    def get_sheet_data(self, sheet_name):
        """Get data from a specific sheet."""
        if self.debug_mode:
            print(f"[DEBUG] Using mock data for sheet: {sheet_name}")
            if sheet_name.startswith('dfmea_'):
                return pd.DataFrame({
                    'Function': ['Test Function'],
                    'Failure Mode': ['Test Failure'],
                    'Effect of Failure': ['Test Effect'],
                    'S': ['5'],
                    'O': ['4'],
                    'D': ['3'],
                    'RPN': ['60'],
                    'Cause': ['Test Cause'],
                    'Current Controls': ['Test Controls'],
                    'Recommended Action': ['Test Action']
                })
            elif sheet_name.startswith('design_'):
                return pd.DataFrame({
                    'Category': ['Inputs'],
                    'Element': ['User-Submitted Insurance Documents'],
                    'Description': ['Policies, PDFs, forms, preferences uploaded via UI']
                })
            return pd.DataFrame()
            
        if not self.service:
            self.authenticate()
        
        range_name = f"{sheet_name}!A1:Z1000"
        print(f"Fetching data from sheet: {sheet_name}")
        
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if not values:
            print(f"No data found in sheet: {sheet_name}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(values[1:], columns=values[0])
        print(f"Retrieved {len(df)} rows from {sheet_name}")
        return df
    
    def convert_fmea_to_json(self, df, agent_name):
        """Convert FMEA DataFrame to structured JSON."""
        fmea_entries = []
        
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
                rpn = 0
            
            entry = {
                "function": row.get("Function", ""),
                "failure_mode": row.get("Failure Mode", ""),
                "effect": row.get("Effect of Failure", ""),
                "severity": severity,
                "cause": row.get("Cause", ""),
                "occurrence": occurrence,
                "current_controls": row.get("Current Controls", ""),
                "detection": detection,
                "rpn": rpn,
                "recommended_action": row.get("Recommended Action", ""),
                "risk_level": self._calculate_risk_level(rpn)
            }
            fmea_entries.append(entry)
        
        return {
            "agent_name": agent_name,
            "fmea_entries": fmea_entries,
            "metadata": {
                "version": "1.0",
                "last_updated": pd.Timestamp.now().strftime("%Y-%m-%d")
            }
        }
    
    def convert_design_to_json(self, df, design_name):
        """Convert Design DataFrame to structured JSON."""
        design_entries = []
        
        for _, row in df.iterrows():
            entry = {
                "category": row.get("Category", ""),
                "element": row.get("Element", ""),
                "description": row.get("Description", "")
            }
            design_entries.append(entry)
        
        return {
            "design_name": design_name,
            "design_entries": design_entries,
            "metadata": {
                "version": "1.0",
                "last_updated": pd.Timestamp.now().strftime("%Y-%m-%d")
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
    
    def process_all_sheets(self):
        """Process all sheets in the spreadsheet."""
        sheets = self.list_sheets()
        
        for sheet in sheets:
            sheet_name = sheet['title']
            
            # Process FMEA sheets
            if sheet_name.startswith('dfmea_') or sheet_name.startswith('pfmea_'):
                try:
                    df = self.get_sheet_data(sheet_name)
                    agent_name = sheet_name.replace('dfmea_', '').replace('pfmea_', '').replace('_', ' ').title()
                    json_data = self.convert_fmea_to_json(df, agent_name)
                    self.save_json(json_data, f"{sheet_name}.json", "docs/fmea")
                    print(f"Processed FMEA sheet: {sheet_name}")
                except Exception as e:
                    print(f"Error processing FMEA sheet {sheet_name}: {str(e)}")
            
            # Process Design sheets
            elif sheet_name.startswith('design_'):
                try:
                    df = self.get_sheet_data(sheet_name)
                    design_name = sheet_name.replace('design_', '').replace('_', ' ').title()
                    json_data = self.convert_design_to_json(df, design_name)
                    self.save_json(json_data, f"{sheet_name}.json", "docs/design")
                    print(f"Processed Design sheet: {sheet_name}")
                except Exception as e:
                    print(f"Error processing Design sheet {sheet_name}: {str(e)}")

def main():
    """Main function to run the sheet importer."""
    # Create necessary directories
    os.makedirs("docs/fmea", exist_ok=True)
    os.makedirs("docs/design", exist_ok=True)
    
    # Get spreadsheet ID from command line or use default
    import sys
    debug_mode = "--debug" in sys.argv
    if debug_mode:
        sys.argv.remove("--debug")
    
    spreadsheet_id = sys.argv[1] if len(sys.argv) > 1 else "1P88hOQf8WFvnPAbycy-jSmYAu_hhspuq9TiH4fZ3UWQ"
    
    print(f"Starting sheet import for spreadsheet: {spreadsheet_id}")
    
    # Initialize importer and process all sheets
    importer = SheetImporter(spreadsheet_id, debug_mode=debug_mode)
    importer.process_all_sheets()
    
    print("Sheet import completed successfully")

if __name__ == "__main__":
    main() 