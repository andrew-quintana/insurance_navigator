import os
import json
import tempfile
import unittest
import pandas as pd
from utils.excel_importer import ExcelImporter

class TestExcelImporter(unittest.TestCase):
    """Test the Excel importer functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary Excel file with test data
        self.temp_dir = tempfile.TemporaryDirectory()
        self.excel_path = os.path.join(self.temp_dir.name, "test_data.xlsx")
        
        # Create test data
        with pd.ExcelWriter(self.excel_path) as writer:
            # FMEA sheet
            fmea_df = pd.DataFrame({
                'Function': ['Test Function'],
                'Failure Mode': ['Test Failure'],
                'Effect of Failure': ['Test Effect'],
                'S': [5],
                'O': [4],
                'D': [3],
                'RPN': [60],
                'Cause': ['Test Cause'],
                'Current Controls': ['Test Controls'],
                'Recommended Action': ['Test Action']
            })
            fmea_df.to_excel(writer, sheet_name='dfmea_test_agent', index=False)
            
            # Design sheet
            design_df = pd.DataFrame({
                'Category': ['Inputs'],
                'Element': ['User-Submitted Insurance Documents'],
                'Description': ['Policies, PDFs, forms, preferences uploaded via UI']
            })
            design_df.to_excel(writer, sheet_name='design_test_component', index=False)
        
        # Create output directories
        os.makedirs(os.path.join(self.temp_dir.name, "docs/fmea"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir.name, "docs/design"), exist_ok=True)
        
        # Initialize importer
        self.importer = ExcelImporter(self.excel_path)
    
    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()
    
    def test_list_sheets(self):
        """Test listing sheets from Excel file."""
        sheets = self.importer.list_sheets()
        self.assertEqual(len(sheets), 2)
        sheet_names = [sheet['title'] for sheet in sheets]
        self.assertIn('dfmea_test_agent', sheet_names)
        self.assertIn('design_test_component', sheet_names)
    
    def test_get_sheet_data(self):
        """Test getting data from a sheet."""
        df = self.importer.get_sheet_data('dfmea_test_agent')
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['Function'], 'Test Function')
    
    def test_convert_fmea_to_json(self):
        """Test converting FMEA data to JSON."""
        df = self.importer.get_sheet_data('dfmea_test_agent')
        json_data = self.importer.convert_fmea_to_json(df, 'Test Agent')
        
        self.assertEqual(json_data['agent_name'], 'Test Agent')
        self.assertEqual(len(json_data['fmea_entries']), 1)
        self.assertEqual(json_data['fmea_entries'][0]['function'], 'Test Function')
        self.assertEqual(json_data['fmea_entries'][0]['severity'], 5)
        self.assertEqual(json_data['fmea_entries'][0]['risk_level'], 'low')
    
    def test_convert_design_to_json(self):
        """Test converting Design data to JSON."""
        df = self.importer.get_sheet_data('design_test_component')
        json_data = self.importer.convert_design_to_json(df, 'Test Component')
        
        self.assertEqual(json_data['design_name'], 'Test Component')
        self.assertEqual(len(json_data['design_entries']), 1)
        self.assertEqual(json_data['design_entries'][0]['category'], 'Inputs')
    
    def test_process_all_sheets(self):
        """Test processing all sheets."""
        # Override save_json to save to temp directory
        original_save_json = self.importer.save_json
        
        def mock_save_json(data, filename, output_dir):
            temp_output_dir = os.path.join(self.temp_dir.name, output_dir)
            os.makedirs(temp_output_dir, exist_ok=True)
            output_path = os.path.join(temp_output_dir, filename)
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return output_path
        
        self.importer.save_json = mock_save_json
        
        # Process all sheets
        self.importer.process_all_sheets()
        
        # Check if files were created
        fmea_path = os.path.join(self.temp_dir.name, "docs/fmea/dfmea_test_agent.json")
        design_path = os.path.join(self.temp_dir.name, "docs/design/design_test_component.json")
        
        self.assertTrue(os.path.exists(fmea_path))
        self.assertTrue(os.path.exists(design_path))
        
        # Verify content
        with open(fmea_path, 'r') as f:
            fmea_data = json.load(f)
            self.assertEqual(fmea_data['agent_name'], 'Test Agent')
        
        with open(design_path, 'r') as f:
            design_data = json.load(f)
            self.assertEqual(design_data['design_name'], 'Test Component')
        
        # Restore original method
        self.importer.save_json = original_save_json

if __name__ == '__main__':
    unittest.main() 