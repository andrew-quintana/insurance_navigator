#!/usr/bin/env python3
"""
Simple test for sheet importer.
"""

import os
import sys
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.sheet_importer import SheetImporter

class TestSheetImporter(unittest.TestCase):
    """Test the SheetImporter class."""
    
    def setUp(self):
        """Set up test environment."""
        self.spreadsheet_id = "test_spreadsheet_id"
        self.importer = SheetImporter(self.spreadsheet_id)
    
    @patch('utils.sheet_importer.build')
    def test_list_sheets(self, mock_build):
        """Test listing sheets."""
        # Setup mocks
        mock_service = MagicMock()
        mock_sheets = MagicMock()
        mock_get = MagicMock()
        
        mock_build.return_value = mock_service
        mock_service.spreadsheets.return_value = mock_sheets
        mock_sheets.get.return_value = mock_get
        
        # Mock the execute method to return test data
        mock_get.execute.return_value = {
            'sheets': [
                {'properties': {'title': 'dfmea_test', 'sheetId': '123'}},
                {'properties': {'title': 'design_test', 'sheetId': '456'}}
            ]
        }
        
        # Set mocked service
        self.importer.service = mock_service
        
        # List sheets
        sheets = self.importer.list_sheets()
        
        # Assertions
        self.assertEqual(len(sheets), 2)
        self.assertEqual(sheets[0]['title'], 'dfmea_test')
        self.assertEqual(sheets[1]['title'], 'design_test')
    
    @patch('utils.sheet_importer.build')
    def test_get_sheet_data(self, mock_build):
        """Test getting sheet data."""
        # Setup mocks
        mock_service = MagicMock()
        mock_sheets = MagicMock()
        mock_values = MagicMock()
        mock_get = MagicMock()
        
        mock_build.return_value = mock_service
        mock_service.spreadsheets.return_value = mock_sheets
        mock_sheets.values.return_value = mock_values
        mock_values.get.return_value = mock_get
        
        # Mock the execute method to return test data
        mock_get.execute.return_value = {
            'values': [
                ['Function', 'Failure Mode', 'S', 'O', 'D', 'RPN'],
                ['Test Function', 'Test Failure', '5', '4', '3', '60']
            ]
        }
        
        # Set mocked service
        self.importer.service = mock_service
        
        # Get sheet data
        df = self.importer.get_sheet_data('test_sheet')
        
        # Assertions
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['Function'], 'Test Function')
        self.assertEqual(df.iloc[0]['RPN'], '60')
    
    def test_convert_fmea_to_json(self):
        """Test converting FMEA data to JSON."""
        # Create test DataFrame
        data = {
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
        }
        df = pd.DataFrame(data)
        
        # Convert to JSON
        result = self.importer.convert_fmea_to_json(df, 'Test Agent')
        
        # Assertions
        self.assertEqual(result['agent_name'], 'Test Agent')
        self.assertEqual(len(result['fmea_entries']), 1)
        self.assertEqual(result['fmea_entries'][0]['function'], 'Test Function')
        self.assertEqual(result['fmea_entries'][0]['rpn'], 60)
        self.assertEqual(result['fmea_entries'][0]['risk_level'], 'low')
    
    def test_convert_design_to_json(self):
        """Test converting Design data to JSON."""
        # Create test DataFrame
        data = {
            'Category': ['Inputs'],
            'Element': ['User-Submitted Insurance Documents'],
            'Description': ['Policies, PDFs, forms, preferences uploaded via UI']
        }
        df = pd.DataFrame(data)
        
        # Convert to JSON
        result = self.importer.convert_design_to_json(df, 'Test Design')
        
        # Assertions
        self.assertEqual(result['design_name'], 'Test Design')
        self.assertEqual(len(result['design_entries']), 1)
        self.assertEqual(result['design_entries'][0]['category'], 'Inputs')
        self.assertEqual(result['design_entries'][0]['element'], 'User-Submitted Insurance Documents')

if __name__ == '__main__':
    unittest.main() 