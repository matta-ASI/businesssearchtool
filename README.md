This a Python script that reads a CSV with business names and searches against these public datasets to generate a comprehensive report. This will be a substantial piece of code that handles multiple APIs and data sources.I've created a comprehensive Python script that searches for businesses across multiple public datasets and generates detailed reports. Here's what the code does:

## Key Features:

1. **Reads CSV Input**: Expects a CSV with at minimum a `business_name` column, plus optional `city`, `state`, and `zip` columns

2. **Searches Multiple Datasets**:
   - **SAM.gov**: Business registrations, UEI, CAGE codes, NAICS codes
   - **USAspending.gov**: Federal contracts and grants
   - **SEC EDGAR**: Public company filings
   - **SBA Data**: Small business certifications (framework for CSV processing)

3. **Generates Comprehensive Reports**:
   - HTML report with summary statistics and detailed findings
   - JSON export for programmatic use
   - Color-coded results (green for found, yellow for not found, red for errors)

## Setup Requirements:

```bash
pip install pandas requests
```

## Environment Variables:
- `SAM_API_KEY`: Required for SAM.gov searches (get from sam.gov)

## Usage:

1. **Prepare your CSV file** with business names:
```csv
business_name,city,state,zip
Microsoft Corporation,Redmond,WA,98052
Apple Inc,Cupertino,CA,95014
Your Business LLC,Chicago,IL,60601
```

2. **Run the script**:
```python
python business_search_tool.py
```

## Key Capabilities:

- **Rate Limiting**: Built-in delays to respect API limits
- **Error Handling**: Continues processing even if individual searches fail
- **Flexible Input**: Works with minimal business name or full address info
- **Comprehensive Logging**: Tracks progress and issues
- **Multiple Output Formats**: HTML report for viewing, JSON for data processing

## Notes on Dataset Access:

- **SAM.gov**: Requires free API key registration
- **USAspending.gov**: Free public API
- **SEC EDGAR**: Free but requires proper User-Agent header
- **SBA Data**: Most require downloading CSV files for local processing

The script provides a solid foundation that you can extend by adding more datasets or refining search algorithms.
UEI/DUNS Coverage:
1. Direct UEI/DUNS Search Support

Search by UEI (Unique Entity Identifier) - the current standard
Search by DUNS (Data Universal Numbering System) - legacy but still supported
Search by business name as fallback

2. Enhanced CSV Input Format
Your CSV can now include any combination of these columns:
csvbusiness_name,city,state,zip,uei,duns
Microsoft Corporation,Redmond,WA,98052,EXAMPLE123UEI45,796666225
Apple Inc,Cupertino,CA,95014,,073133228
Small Business LLC,Chicago,IL,60601,,,
3. Comprehensive SAM.gov Data Retrieval
When found, the code now extracts:

UEI SAM (current identifier)
UEI DUNS (DUNS converted to UEI format)
Original DUNS number (if still available)
CAGE code
Registration status and dates
Exclusion status
Complete address information
NAICS codes

4. Smart Search Priority
The code intelligently prioritizes:

UEI search (most accurate, if available)
DUNS search (legacy but still works)
Business name search (fallback method)

Key Benefits for UEI/DUNS:

Higher Accuracy: UEI/DUNS searches are more precise than name searches
Faster Results: Direct identifier lookups are quicker
Complete Records: Gets full SAM.gov registration details
Legacy Support: Handles both old DUNS and new UEI systems
Data Validation: Cleans and formats UEI/DUNS numbers automatically

Important Notes:

UEI is the new standard (replaced DUNS in 2022)
SAM.gov API key required for UEI/DUNS searches
DUNS still works but may be phased out eventually
Cross-dataset linking: UEI/DUNS from SAM.gov can help identify the same entity in other datasets

This makes the tool much more powerful for government contracting research, compliance checking, and business verification using the official federal identifiers!
