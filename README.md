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


Yes, absolutely! The SBA Certifications database is a great addition. Let me add a dedicated search function for it:Perfect! I've added comprehensive support for the **SBA Certifications database** (search.certifications.sba.gov). Here's what the new functionality provides:

## SBA Certifications Search Features:

### 1. **Multiple Search Methods**
- **UEI search** (most accurate)
- **DUNS search** (legacy support) 
- **Business name search** (with location filters)

### 2. **Complete Certification Data**
The search retrieves:
- **Company Details**: Name, UEI, DUNS, address, phone, website
- **Business Information**: Business type, NAICS codes
- **All Certifications**: Including:
  - 8(a) Business Development
  - HUBZone Certified
  - Women-Owned Small Business (WOSB)
  - Service-Disabled Veteran-Owned (SDVOSB)
  - Disadvantaged Business Enterprise (DBE)
  - And other SBA certification programs

### 3. **Certification Details**
For each certification:
- Program name
- Status (Active/Inactive/Pending)
- Certification date
- Expiration date
- Certifying office

### 4. **Smart Matching**
- Returns multiple matches with similarity scoring
- Best match identification for name searches
- Complete match details for verification

## Key Benefits:

✅ **Live Data**: Real-time certification status (not outdated CSV files)  
✅ **Official Source**: Direct from SBA's certification portal  
✅ **Comprehensive**: All major SBA certification programs in one search  
✅ **UEI/DUNS Compatible**: Works with modern and legacy identifiers  
✅ **Location Filtering**: Can narrow search by state/city  

## Sample Output:
```json
{
  "source": "SBA Certifications",
  "status": "found",
  "data": {
    "best_match": {
      "company_name": "ABC Small Business LLC",
      "uei": "ABC123UEI456",
      "certifications": [
        {
          "program": "8(a) Business Development",
          "status": "Active",
          "certification_date": "2023-01-15",
          "expiration_date": "2032-01-15"
        }
      ],
      "active_certifications": 1
    },
    "certification_programs_found": ["8(a)", "HUBZone", "WOSB"]
  }
}
```

This addition makes your tool much more powerful for:
- **Government contracting research**
- **Small business verification**
- **Certification status checking**
- **Compliance verification**
- **Market research on certified small businesses**

The SBA Certifications search is now integrated into the main search flow, so it will automatically run for each business in your CSV file alongside the other datasets!
