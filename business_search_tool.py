import pandas as pd
import requests
import time
import json
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from urllib.parse import quote, urlencode
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BusinessDatasetSearcher:
    """
    A comprehensive tool to search for businesses across multiple public datasets
    """
    
    def __init__(self):
        self.results = []
        self.api_delays = {
            'sam': 1,  # 1 second delay for SAM.gov
            'usaspending': 0.5,
            'census': 0.5,
            'edgar': 1,
            'sba': 0.5
        }
        
    def read_business_csv(self, filepath: str) -> List[Dict]:
        """
        Read CSV file containing business names
        Expected columns: 'business_name', optionally 'city', 'state', 'zip'
        """
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} businesses from {filepath}")
            
            # Ensure business_name column exists
            if 'business_name' not in df.columns:
                raise ValueError("CSV must contain 'business_name' column")
            
            # Convert to list of dictionaries
            businesses = df.to_dict('records')
            return businesses
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return []
    
    def search_sam_gov(self, business_name: str, location_info: Dict = None) -> Dict:
        """
        Search SAM.gov for business registration information
        """
        try:
            # SAM.gov API endpoint (public data)
            base_url = "https://api.sam.gov/entity-information/v3/entities"
            
            params = {
                'api_key': os.getenv('SAM_API_KEY', ''),  # Requires API key
                'legalBusinessName': business_name,
                'includeSections': 'entityRegistration,coreData'
            }
            
            if location_info and location_info.get('state'):
                params['stateOrProvinceCode'] = location_info['state']
            
            # Note: SAM.gov requires API key for most searches
            if not params['api_key']:
                logger.warning("SAM.gov API key not found in environment variables")
                return {'source': 'SAM.gov', 'status': 'API key required', 'data': None}
            
            response = requests.get(base_url, params=params, timeout=30)
            time.sleep(self.api_delays['sam'])
            
            if response.status_code == 200:
                data = response.json()
                entities = data.get('entityData', [])
                if entities:
                    entity = entities[0]
                    return {
                        'source': 'SAM.gov',
                        'status': 'found',
                        'data': {
                            'uei': entity.get('entityRegistration', {}).get('ueiSAM'),
                            'cage_code': entity.get('entityRegistration', {}).get('cageCode'),
                            'legal_name': entity.get('coreData', {}).get('legalBusinessName'),
                            'registration_status': entity.get('entityRegistration', {}).get('registrationStatus'),
                            'naics_codes': [naics.get('naicsCode') for naics in entity.get('naicsInformation', {}).get('primaryNaics', [])]
                        }
                    }
            
            return {'source': 'SAM.gov', 'status': 'not_found', 'data': None}
            
        except Exception as e:
            logger.error(f"Error searching SAM.gov for {business_name}: {e}")
            return {'source': 'SAM.gov', 'status': 'error', 'data': str(e)}
    
    def search_usaspending(self, business_name: str) -> Dict:
        """
        Search USAspending.gov for federal awards
        """
        try:
            base_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
            
            payload = {
                "filters": {
                    "recipient_search_text": [business_name],
                    "award_type_codes": ["A", "B", "C", "D"]  # Contracts and grants
                },
                "fields": ["Award ID", "Recipient Name", "Award Amount", "Award Type", "Period of Performance Start Date"],
                "sort": "Award Amount",
                "order": "desc",
                "limit": 10
            }
            
            response = requests.post(base_url, json=payload, timeout=30)
            time.sleep(self.api_delays['usaspending'])
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                if results:
                    awards = []
                    total_amount = 0
                    for award in results:
                        award_amount = award.get('Award Amount', 0)
                        total_amount += award_amount
                        awards.append({
                            'award_id': award.get('Award ID'),
                            'recipient_name': award.get('Recipient Name'),
                            'amount': award_amount,
                            'type': award.get('Award Type'),
                            'start_date': award.get('Period of Performance Start Date')
                        })
                    
                    return {
                        'source': 'USAspending.gov',
                        'status': 'found',
                        'data': {
                            'total_awards': len(awards),
                            'total_amount': total_amount,
                            'awards': awards[:5]  # Top 5 awards
                        }
                    }
            
            return {'source': 'USAspending.gov', 'status': 'not_found', 'data': None}
            
        except Exception as e:
            logger.error(f"Error searching USAspending.gov for {business_name}: {e}")
            return {'source': 'USAspending.gov', 'status': 'error', 'data': str(e)}
    
    def search_edgar_sec(self, business_name: str) -> Dict:
        """
        Search SEC EDGAR database for public company filings
        """
        try:
            # SEC Company Search API
            base_url = "https://www.sec.gov/files/company_tickers.json"
            
            headers = {
                'User-Agent': 'Business Search Tool contact@yourcompany.com'
            }
            
            response = requests.get(base_url, headers=headers, timeout=30)
            time.sleep(self.api_delays['edgar'])
            
            if response.status_code == 200:
                companies = response.json()
                
                # Search for business name in company data
                matches = []
                search_name = business_name.lower()
                
                for cik, company_data in companies.items():
                    if isinstance(company_data, dict):
                        company_name = company_data.get('title', '').lower()
                        ticker = company_data.get('ticker', '')
                        
                        if search_name in company_name or company_name in search_name:
                            matches.append({
                                'cik': company_data.get('cik_str'),
                                'ticker': ticker,
                                'company_name': company_data.get('title'),
                                'match_score': len(set(search_name.split()) & set(company_name.split()))
                            })
                
                if matches:
                    # Sort by match score
                    matches.sort(key=lambda x: x['match_score'], reverse=True)
                    return {
                        'source': 'SEC EDGAR',
                        'status': 'found',
                        'data': {
                            'matches_found': len(matches),
                            'best_match': matches[0],
                            'all_matches': matches[:3]  # Top 3 matches
                        }
                    }
            
            return {'source': 'SEC EDGAR', 'status': 'not_found', 'data': None}
            
        except Exception as e:
            logger.error(f"Error searching SEC EDGAR for {business_name}: {e}")
            return {'source': 'SEC EDGAR', 'status': 'error', 'data': str(e)}
    
    def search_sba_data(self, business_name: str, location_info: Dict = None) -> Dict:
        """
        Search SBA datasets for certifications and loan data
        Note: This is a simplified search - actual implementation would require
        downloading and processing SBA CSV datasets
        """
        try:
            # SBA DSBS (Dynamic Small Business Search) - hypothetical API call
            # In practice, you'd need to download and search CSV files
            
            return {
                'source': 'SBA Data',
                'status': 'requires_csv_processing',
                'data': {
                    'note': 'SBA data requires downloading CSV files and local processing',
                    'datasets_to_check': [
                        'PPP Loan Data',
                        '8(a) Business Development',
                        'HUBZone Certified Companies',
                        'Women-Owned Small Business',
                        'Service-Disabled Veteran-Owned'
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing SBA data for {business_name}: {e}")
            return {'source': 'SBA Data', 'status': 'error', 'data': str(e)}
    
    def search_business_across_datasets(self, business_info: Dict) -> Dict:
        """
        Search a single business across all available datasets
        """
        business_name = business_info.get('business_name', '')
        location_info = {
            'city': business_info.get('city'),
            'state': business_info.get('state'),
            'zip': business_info.get('zip')
        }
        
        logger.info(f"Searching for: {business_name}")
        
        # Initialize results for this business
        business_results = {
            'business_name': business_name,
            'location': location_info,
            'search_timestamp': datetime.now().isoformat(),
            'datasets_searched': []
        }
        
        # Search each dataset
        datasets_to_search = [
            ('sam_gov', lambda: self.search_sam_gov(business_name, location_info)),
            ('usaspending', lambda: self.search_usaspending(business_name)),
            ('edgar_sec', lambda: self.search_edgar_sec(business_name)),
            ('sba_data', lambda: self.search_sba_data(business_name, location_info))
        ]
        
        for dataset_name, search_func in datasets_to_search:
            try:
                result = search_func()
                business_results['datasets_searched'].append(result)
                logger.info(f"Completed search in {result['source']}: {result['status']}")
            except Exception as e:
                logger.error(f"Failed to search {dataset_name}: {e}")
                business_results['datasets_searched'].append({
                    'source': dataset_name,
                    'status': 'error',
                    'data': str(e)
                })
        
        return business_results
    
    def process_businesses(self, businesses: List[Dict]) -> List[Dict]:
        """
        Process all businesses and return comprehensive results
        """
        all_results = []
        total_businesses = len(businesses)
        
        for idx, business in enumerate(businesses, 1):
            logger.info(f"Processing business {idx}/{total_businesses}: {business.get('business_name', 'Unknown')}")
            
            try:
                result = self.search_business_across_datasets(business)
                all_results.append(result)
                
                # Small delay between businesses to be respectful to APIs
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing business {business.get('business_name')}: {e}")
                all_results.append({
                    'business_name': business.get('business_name'),
                    'error': str(e),
                    'search_timestamp': datetime.now().isoformat()
                })
        
        return all_results
    
    def generate_report(self, results: List[Dict], output_file: str = None) -> str:
        """
        Generate a comprehensive report from search results
        """
        if not output_file:
            output_file = f"business_search_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Generate HTML report
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Business Dataset Search Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .business { border: 1px solid #ddd; margin: 20px 0; padding: 15px; }
                .found { background-color: #e8f5e8; }
                .not-found { background-color: #fff3cd; }
                .error { background-color: #f8d7da; }
                .dataset-result { margin: 10px 0; padding: 10px; border-left: 3px solid #007bff; }
                .summary { background-color: #f8f9fa; padding: 15px; margin: 20px 0; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Business Dataset Search Report</h1>
            <p>Generated on: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        """
        
        # Summary statistics
        total_businesses = len(results)
        businesses_with_findings = 0
        dataset_stats = {}
        
        for result in results:
            has_findings = False
            for dataset_result in result.get('datasets_searched', []):
                dataset_name = dataset_result.get('source', 'Unknown')
                if dataset_name not in dataset_stats:
                    dataset_stats[dataset_name] = {'found': 0, 'not_found': 0, 'error': 0}
                
                status = dataset_result.get('status', 'error')
                if status == 'found':
                    dataset_stats[dataset_name]['found'] += 1
                    has_findings = True
                elif status == 'not_found':
                    dataset_stats[dataset_name]['not_found'] += 1
                else:
                    dataset_stats[dataset_name]['error'] += 1
            
            if has_findings:
                businesses_with_findings += 1
        
        # Add summary section
        html_content += f"""
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Total Businesses Searched:</strong> {total_businesses}</p>
            <p><strong>Businesses with Findings:</strong> {businesses_with_findings}</p>
            
            <h3>Dataset Search Statistics</h3>
            <table>
                <tr><th>Dataset</th><th>Found</th><th>Not Found</th><th>Errors</th></tr>
        """
        
        for dataset, stats in dataset_stats.items():
            html_content += f"""
                <tr>
                    <td>{dataset}</td>
                    <td>{stats['found']}</td>
                    <td>{stats['not_found']}</td>
                    <td>{stats['error']}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </div>
        
        <h2>Detailed Results</h2>
        """
        
        # Add detailed results for each business
        for result in results:
            business_name = result.get('business_name', 'Unknown Business')
            has_findings = any(ds.get('status') == 'found' for ds in result.get('datasets_searched', []))
            
            css_class = 'found' if has_findings else 'not-found'
            
            html_content += f"""
            <div class="business {css_class}">
                <h3>{business_name}</h3>
                <p><strong>Search Date:</strong> {result.get('search_timestamp', 'Unknown')}</p>
            """
            
            # Add location info if available
            location = result.get('location', {})
            if any(location.values()):
                location_str = ', '.join(filter(None, [location.get('city'), location.get('state'), location.get('zip')]))
                if location_str:
                    html_content += f"<p><strong>Location:</strong> {location_str}</p>"
            
            # Add dataset results
            for dataset_result in result.get('datasets_searched', []):
                source = dataset_result.get('source', 'Unknown')
                status = dataset_result.get('status', 'unknown')
                data = dataset_result.get('data')
                
                html_content += f"""
                <div class="dataset-result">
                    <h4>{source} - Status: {status.upper()}</h4>
                """
                
                if data and status == 'found':
                    html_content += f"<pre>{json.dumps(data, indent=2, default=str)}</pre>"
                elif status == 'error':
                    html_content += f"<p><em>Error: {data}</em></p>"
                elif status == 'not_found':
                    html_content += "<p><em>No records found</em></p>"
                
                html_content += "</div>"
            
            html_content += "</div>"
        
        html_content += """
        </body>
        </html>
        """
        
        # Write report to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Report generated: {output_file}")
        return output_file

def main():
    """
    Main function to demonstrate usage
    """
    # Initialize the searcher
    searcher = BusinessDatasetSearcher()
    
    # Example usage
    csv_file = "business_list.csv"  # Replace with your CSV file path
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        # Create a sample CSV for demonstration
        sample_data = [
            {"business_name": "Microsoft Corporation", "city": "Redmond", "state": "WA"},
            {"business_name": "Apple Inc", "city": "Cupertino", "state": "CA"},
            {"business_name": "Small Business Example LLC", "city": "Chicago", "state": "IL"}
        ]
        
        df = pd.DataFrame(sample_data)
        df.to_csv(csv_file, index=False)
        logger.info(f"Created sample CSV file: {csv_file}")
    
    # Read businesses from CSV
    businesses = searcher.read_business_csv(csv_file)
    
    if businesses:
        # Process all businesses
        logger.info(f"Starting search for {len(businesses)} businesses...")
        results = searcher.process_businesses(businesses)
        
        # Generate report
        report_file = searcher.generate_report(results)
        
        # Also save results as JSON
        json_file = f"business_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Search complete! Results saved to:")
        logger.info(f"  HTML Report: {report_file}")
        logger.info(f"  JSON Data: {json_file}")
    else:
        logger.error("No businesses found in CSV file")

if __name__ == "__main__":
    main()
