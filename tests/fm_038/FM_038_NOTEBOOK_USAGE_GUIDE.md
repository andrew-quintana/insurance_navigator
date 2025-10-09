# FM-038 Debug Notebook Usage Guide

**Date:** 2025-10-09  
**Phase:** 2 - Interactive Debugging Notebook  
**Status:** ✅ **Complete**

---

## Overview

The `FM_038_Debug_Notebook.ipynb` is an interactive Jupyter notebook that provides step-by-step debugging capabilities for the complete chat flow investigation. It converts the working Phase 1 script into a cell-based format for detailed analysis.

## Prerequisites

### Software Requirements
- Python 3.11+
- Jupyter Notebook or JupyterLab
- Virtual environment with project dependencies

### Python Packages
```bash
pip install jupyter notebook pandas matplotlib seaborn aiohttp python-dotenv
```

### Environment Setup
- `.env.production` file with valid API credentials
- Access to production API endpoint
- Test user credentials (already configured in notebook)

## Starting the Notebook

### Option 1: Jupyter Notebook
```bash
cd tests/fm_038
jupyter notebook FM_038_Debug_Notebook.ipynb
```

### Option 2: JupyterLab
```bash
cd tests/fm_038
jupyter lab FM_038_Debug_Notebook.ipynb
```

### Option 3: VS Code
- Open the notebook file in VS Code
- Select Python kernel
- Run cells interactively

---

## Notebook Structure

### Cell 0: Overview (Markdown)
Introduction and prerequisites

### Cell 1: Setup and Environment Configuration (Markdown)
Documentation for setup cell

### Cell 2: Setup and Environment Configuration (Python)
- Import dependencies
- Load environment variables
- Configure logging
- Set test credentials
- Display configuration

**Expected Output:** Configuration table showing loaded settings

---

### Cell 3: Data Classes and Helper Functions (Markdown)
Documentation for data structures

### Cell 4: Data Classes and Helper Functions (Python)
- Define `FunctionCall` class
- Define `InvestigationMetrics` class
- Initialize global metrics

**Expected Output:** Confirmation message

---

### Cell 5: API Endpoint Discovery (Markdown)
Documentation for endpoint testing

### Cell 6: API Endpoint Discovery (Python)
- Test configured API endpoints
- Find working endpoint
- Display results table

**Expected Output:** Table showing endpoint test results and active endpoint

**Action Required:** Review which endpoint is working

---

### Cell 7: Authentication Flow Analysis (Markdown)
Documentation for authentication

### Cell 8: Authentication Flow Analysis (Python)
- Authenticate with test user
- Obtain JWT token
- Track authentication performance

**Expected Output:** 
- Success box with user details and token info
- OR Error box if authentication fails

**Action Required:** Verify authentication succeeded before proceeding

---

### Cell 9: Single Chat Request Analysis (Markdown)
Documentation for chat request

### Cell 10: Single Chat Request Analysis (Python)
- Send single test message
- Analyze request/response flow
- Track performance

**Expected Output:**
- Success box with response details and preview
- OR Error box if request fails

**Action Required:** Review response quality and timing

---

### Cell 11: Multiple Chat Requests (Markdown)
Documentation for multiple requests

### Cell 12: Multiple Chat Requests (Python)
- Send 2 additional test messages
- 5-second delay between requests
- Collect responses

**Expected Output:** Multiple success/error boxes for each message

**Action Required:** Review consistency across requests

---

### Cell 13: Function Call Timeline Visualization (Markdown)
Documentation for visualization

### Cell 14: Function Call Timeline Visualization (Python)
- Create function call DataFrame
- Display function call table
- Generate duration bar chart
- Generate success/error pie chart

**Expected Output:**
- HTML table of function calls
- 2-panel visualization (bar chart + pie chart)

**Analysis Points:**
- Which functions take longest?
- What's the success rate?
- Are there patterns in failures?

---

### Cell 15: Performance Metrics Analysis (Markdown)
Documentation for metrics

### Cell 16: Performance Metrics Analysis (Python)
- Display metrics summary table
- Generate performance timeline plot
- List key observations

**Expected Output:**
- Metrics table with all statistics
- Performance timeline graph
- Bulleted list of observations

**Analysis Points:**
- Are there performance bottlenecks?
- Is average duration acceptable?
- Are there failed requests?

---

### Cell 17: Production Log Analysis (Markdown)
Documentation for log analysis

### Cell 18: Production Log Analysis (Python)
- Display guidance for checking production logs
- List what to look for
- Key questions to answer

**Expected Output:** Formatted guidance box

**Action Required:** Check Render dashboard logs based on guidance

---

### Cell 19: Function Input/Output Deep Dive (Markdown)
Documentation for deep dive

### Cell 20: Function Input/Output Deep Dive (Python)
- Display each function call details
- Show inputs with values
- Show outputs or errors
- Format for readability

**Expected Output:** Detailed breakdown of each function call

**Analysis Points:**
- What inputs were provided?
- What outputs were generated?
- Are there any errors?
- Is data flowing correctly?

---

### Cell 21: Save Investigation Report (Markdown)
Documentation for saving report

### Cell 22: Save Investigation Report (Python)
- Generate timestamped filename
- Create JSON report
- Save to file

**Expected Output:** Success box with filename

**Action Required:** Review JSON file for detailed data

---

### Cell 23: Cleanup (Markdown)
Documentation for cleanup

### Cell 24: Cleanup (Python)
- Close HTTP session
- Display next steps

**Expected Output:** Cleanup confirmation and next steps guidance

---

### Cell 25: Summary (Markdown)
Final summary and troubleshooting guide

---

## Execution Strategies

### Strategy 1: Full Sequential Run
Execute all cells from top to bottom in order:
1. Setup → Endpoint Discovery → Authentication
2. Single Request → Multiple Requests
3. Visualizations → Analysis → Report → Cleanup

**Use Case:** First-time investigation or comprehensive analysis

### Strategy 2: Selective Execution
Run specific cells for focused debugging:
- Cells 2, 4, 6, 8 → Basic setup and auth
- Cell 10 → Test single request
- Cells 14, 16 → View analysis
- Cell 20 → Deep dive on specific issue

**Use Case:** Investigating specific issues or re-running tests

### Strategy 3: Iterative Testing
Run setup → Run multiple tests → Analyze:
1. Cells 2, 4, 6, 8 (setup)
2. Cells 10, 12 (testing) - modify messages as needed
3. Cells 14, 16, 20 (analysis)
4. Repeat step 2-3 with different messages

**Use Case:** Testing different scenarios or edge cases

---

## Customization Guide

### Adding Custom Test Messages
In Cell 12, modify the `test_messages` list:
```python
test_messages = [
    "Your custom message 1",
    "Your custom message 2",
    "Your custom message 3"
]
```

### Changing Wait Time Between Requests
In Cell 12, modify the sleep duration:
```python
await asyncio.sleep(10)  # Wait 10 seconds instead of 5
```

### Adding Custom Analysis
Add new code cells after Cell 20:
```python
# Example: Analyze response lengths
response_lengths = [len(r.get('text', '')) for r in responses if r]
print(f"Average response length: {sum(response_lengths) / len(response_lengths):.2f} chars")
```

### Modifying Visualizations
In Cells 14 or 16, customize the plots:
```python
# Change figure size
plt.rcParams['figure.figsize'] = (16, 8)

# Change color scheme
sns.set_palette("husl")

# Add more plot types
fig, axes = plt.subplots(2, 2, figsize=(15, 12))
# ... add custom plots
```

---

## Troubleshooting

### Issue: Notebook Won't Start
**Symptoms:** Jupyter won't load the notebook
**Solutions:**
1. Check Python version: `python --version` (should be 3.11+)
2. Verify Jupyter installation: `jupyter --version`
3. Try: `pip install --upgrade jupyter notebook`
4. Check file permissions

### Issue: ImportError on Dependencies
**Symptoms:** Cell 2 fails with import errors
**Solutions:**
1. Activate virtual environment
2. Install missing packages: `pip install -r requirements.txt`
3. Check specific package: `pip install aiohttp pandas matplotlib seaborn`

### Issue: Authentication Fails
**Symptoms:** Cell 8 shows authentication error
**Solutions:**
1. Check `.env.production` file exists
2. Verify credentials are correct
3. Check API endpoint is accessible (Cell 6)
4. Verify user account is active

### Issue: No Endpoints Found
**Symptoms:** Cell 6 reports no working endpoints
**Solutions:**
1. Check network connectivity
2. Verify `PRODUCTION_API_URL` in `.env.production`
3. Try hardcoding endpoint in Cell 2: 
   ```python
   API_BASE_URLS = ["https://your-api.com"]
   ```
4. Check if API service is running

### Issue: Chat Requests Fail
**Symptoms:** Cell 10 or 12 show chat errors
**Solutions:**
1. Verify authentication succeeded (Cell 8)
2. Check token is valid
3. Review error message in output
4. Check production logs for backend issues
5. Verify user has permissions

### Issue: Visualizations Don't Display
**Symptoms:** Cells 14 or 16 show no plots
**Solutions:**
1. Check `matplotlib` backend: `matplotlib.get_backend()`
2. Try: `%matplotlib inline` at top of notebook
3. Restart kernel and run all cells
4. Check if `metrics.function_calls` has data

### Issue: Notebook Kernel Dies
**Symptoms:** Kernel stops responding during execution
**Solutions:**
1. Check memory usage
2. Reduce number of test messages
3. Restart kernel: Kernel → Restart
4. Clear outputs: Cell → All Output → Clear
5. Check logs for Python errors

---

## Best Practices

### 1. Save Frequently
- Use Ctrl+S / Cmd+S to save
- Notebook auto-saves, but manual saves are safer

### 2. Clear Outputs Before Sharing
- Cell → All Output → Clear
- Reduces file size
- Removes sensitive data from outputs

### 3. Restart Kernel Between Runs
- Kernel → Restart & Clear Output
- Ensures clean state
- Prevents variable conflicts

### 4. Document Your Changes
- Add markdown cells to document findings
- Use comments in code cells
- Save modified notebook with descriptive name

### 5. Keep Original Notebook
- Make a copy before experimenting
- `cp FM_038_Debug_Notebook.ipynb FM_038_Debug_Notebook_CUSTOM.ipynb`

### 6. Export Reports
- Cell 22 saves JSON report
- Keep reports for comparison
- Name format: `chat_flow_investigation_report_YYYYMMDD_HHMMSS.json`

---

## Output Files

### Generated Files
- `chat_flow_investigation_report_<timestamp>.json` - Complete investigation data
- Notebook auto-saves to `.ipynb_checkpoints/` directory

### Report Structure
```json
{
  "timestamp": "ISO-8601 timestamp",
  "test_user": "email address",
  "test_user_id": "UUID",
  "api_base_url": "active endpoint",
  "metrics": {
    "total_duration_seconds": 0.0,
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "function_calls": 0,
    "average_function_duration_ms": 0.0
  },
  "function_calls": [
    {
      "name": "function_name",
      "duration_ms": 0.0,
      "inputs": {},
      "outputs": "...",
      "error": null
    }
  ]
}
```

---

## Next Steps

After running the notebook:

1. **Review JSON Report**
   - Analyze function call timing
   - Identify bottlenecks
   - Check for errors

2. **Check Production Logs**
   - Follow guidance from Cell 18
   - Look for RAG operation logs
   - Verify CHECKPOINT entries

3. **Document Findings**
   - Create findings document
   - List identified issues
   - Propose solutions

4. **Proceed to Phase 3**
   - Analysis & Documentation
   - Root cause analysis
   - Corrective action plan

---

## Support

### Documentation References
- **Phase 1:** `tests/fm_038/chat_flow_investigation.py` - Original script
- **Agent Handoff:** `tests/fm_038/FM_038_AGENT_HANDOFF.md` - Task details
- **TODO:** `docs/initiatives/debug/fm_038_chat_rag_failures/TODO.md` - Phase tracking

### Getting Help
1. Review troubleshooting section above
2. Check Phase 1 script for comparison
3. Review investigation documentation
4. Ask specific questions with error messages

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-09  
**Status:** ✅ Complete and Ready for Use

