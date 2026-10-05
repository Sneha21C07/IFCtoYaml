#!/usr/bin/env python3
"""
Confluence IFC Page Extraction Tool
Extracts IFC specifications from Confluence and creates a formatted Word document
Uses credentials from .env file
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from confluence_to_word import create_word_doc_from_confluence

def main():
    """Main entry point for the extraction tool"""
    
    # Load environment variables
    load_dotenv()
    
    print("\n" + "=" * 70)
    print("CONFLUENCE IFC PAGE EXTRACTION TOOL")
    print("=" * 70)
    
    # Verify .env configuration
    required_vars = [
        'CONFLUENCE_PAGE_ID',
        'CONFLUENCE_URL',
        'CONFLUENCE_EMAIL',
        'CONFLUENCE_TOKEN'
    ]
    
    print("\nVerifying .env configuration...")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"  ✗ {var}: NOT SET")
        else:
            if var == 'CONFLUENCE_TOKEN':
                print(f"  ✓ {var}: {'*' * 8} (configured)")
            else:
                print(f"  ✓ {var}: {value}")
    
    if missing_vars:
        print(f"\n✗ ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease update your .env file with:")
        print("""
CONFLUENCE_PAGE_ID=<page-id>
CONFLUENCE_URL=https://tpgtelecom.atlassian.net/wiki
CONFLUENCE_EMAIL=<your-email>
CONFLUENCE_TOKEN=<your-api-token>
        """)
        return False
    
    # Optional: allow command-line output filename
    output_filename = None
    if len(sys.argv) > 1:
        output_filename = sys.argv[1]
        print(f"\nOutput filename: {output_filename}")
    
    print("\n" + "-" * 70)
    
    # Run the extraction
    try:
        success = create_word_doc_from_confluence(output_filename=output_filename)
        if success:
            print("\n✓ Extraction completed successfully!")
            return True
        else:
            print("\n✗ Extraction failed")
            return False
    except Exception as e:
        print(f"\n✗ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
