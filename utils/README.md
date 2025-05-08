# Google Sheets Importer

A simple utility to import data from Google Sheets and convert it to structured JSON files.

## Setup

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Set up Google Sheets API credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Sheets API
   - Create OAuth 2.0 credentials:
     - Go to "APIs & Services" > "Credentials"
     - Click "Create Credentials" > "OAuth client ID"
     - Choose "Desktop app" as the application type
     - Download the credentials JSON file
   - Save the downloaded file as `config/google_credentials.json`

## Usage

Run the script with:

```bash
python utils/sheet_importer.py [SPREADSHEET_ID]
```

If no spreadsheet ID is provided, it will use the default ID from the code.

### Sheet Naming Conventions

The importer looks for sheets with specific prefixes:

- `dfmea_*` or `pfmea_*`: Processed as FMEA documents
- `design_*`: Processed as design documents

### Output

- FMEA JSON files are saved to `docs/fmea/`
- Design JSON files are saved to `docs/design/`

## Example

For a spreadsheet with sheets named:
- `dfmea_policy_compliance_evaluator`
- `design_io_agent`

The script will create:
- `docs/fmea/dfmea_policy_compliance_evaluator.json`
- `docs/design/design_io_agent.json`

## Expected Sheet Format

### FMEA Sheets
Should contain columns:
- Function
- Failure Mode
- Effect of Failure
- S (Severity)
- O (Occurrence)
- D (Detection)
- RPN
- Cause
- Current Controls
- Recommended Action

### Design Sheets
Should contain columns:
- Category
- Element
- Description

## Testing

Run the tests with:

```bash
python tests/test_sheet_importer_simple.py
```

The tests verify:
1. Listing sheets from a Google Spreadsheet
2. Getting data from a specific sheet
3. Converting FMEA data to JSON
4. Converting Design data to JSON

No actual Google Sheets API calls are made during testing - all API interactions are mocked. 