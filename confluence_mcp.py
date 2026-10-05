#!/usr/bin/env python3
"""
Confluence REST API Client
Provides tools to fetch and interact with Confluence pages via REST API
"""

import base64
import json
import requests
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def fetch_confluence_page(
    page_id: str = None,
    confluence_url: str = None,
    email: str = None,
    api_token: str = None,
    expand: Optional[str] = "body.storage"
) -> dict:
    """
    Fetch a Confluence page's content using the REST API.
    
    Args:
        page_id: The ID of the Confluence page to fetch
        confluence_url: The base URL of your Confluence instance (e.g., https://your-domain.atlassian.net/wiki)
        email: Email address for Confluence API authentication
        api_token: API token for Confluence API authentication
        expand: Comma-separated list of properties to expand (default: body.storage)
    
    Returns:
        dict: Page content including title, body, metadata, and links
    
    Raises:
        ValueError: If required parameters are missing
        requests.exceptions.RequestException: If API request fails
    """
    
    # Use environment variables if parameters not provided
    page_id = page_id or os.getenv("CONFLUENCE_PAGE_ID")
    confluence_url = confluence_url or os.getenv("CONFLUENCE_URL")
    email = email or os.getenv("CONFLUENCE_EMAIL")
    api_token = api_token or os.getenv("CONFLUENCE_TOKEN")
    
    if not all([page_id, confluence_url, email, api_token]):
        raise ValueError("All parameters (page_id, confluence_url, email, api_token) are required. "
                       "Provide as arguments or set environment variables.")
    
    # Create Basic Auth header
    auth_string = f"{email}:{api_token}"
    auth_bytes = auth_string.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
    
    # Construct API endpoint
    api_endpoint = f"{confluence_url}/rest/api/content/{page_id}"
    
    # Set headers with Basic Auth
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Add expand parameter to get body content
    params = {
        "expand": expand
    }
    
    try:
        # Make the API request
        response = requests.get(
            api_endpoint,
            headers=headers,
            params=params,
            timeout=10
        )
        
        # Raise exception for bad status codes
        response.raise_for_status()
        
        # Parse response
        page_data = response.json()
        
        # Extract and return relevant content
        result = {
            "success": True,
            "page_id": page_id,
            "title": page_data.get("title", ""),
            "type": page_data.get("type", ""),
            "status": page_data.get("status", ""),
            "body": page_data.get("body", {}),
            "metadata": {
                "created": page_data.get("metadata", {}).get("createDate", ""),
                "modified": page_data.get("metadata", {}).get("updateDate", ""),
                "created_by": page_data.get("version", {}).get("createdBy", {}),
                "last_modified_by": page_data.get("version", {}).get("by", {})
            },
            "links": page_data.get("links", {}),
            "space": page_data.get("space", {}).get("key", "")
        }
        
        return result
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            error_msg = "Unauthorized: Invalid email or API token"
        elif response.status_code == 404:
            error_msg = f"Page not found: {page_id}"
        elif response.status_code == 403:
            error_msg = "Forbidden: Access denied to this page"
        else:
            error_msg = f"HTTP Error {response.status_code}: {e}"
        
        return {
            "success": False,
            "error": error_msg,
            "status_code": response.status_code
        }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout: Confluence API did not respond within 10 seconds"
        }
    
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "error": f"Connection error: Could not connect to Confluence at {confluence_url}"
        }
    
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid response from Confluence API: Not valid JSON"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def search_confluence_pages(
    query: str = None,
    confluence_url: str = None,
    email: str = None,
    api_token: str = None,
    max_results: Optional[int] = 10
) -> dict:
    """
    Search for Confluence pages using CQL (Confluence Query Language).
    
    Args:
        query: CQL query string (e.g., "type=page AND title ~ 'customer'")
        confluence_url: The base URL of your Confluence instance
        email: Email address for Confluence API authentication
        api_token: API token for Confluence API authentication
        max_results: Maximum number of results to return (default: 10)
    
    Returns:
        dict: Search results with matching pages
    """
    
    # Use environment variables if parameters not provided
    query = query or os.getenv("CONFLUENCE_QUERY")
    confluence_url = confluence_url or os.getenv("CONFLUENCE_URL")
    email = email or os.getenv("CONFLUENCE_EMAIL")
    api_token = api_token or os.getenv("CONFLUENCE_TOKEN")
    
    if not all([query, confluence_url, email, api_token]):
        raise ValueError("Query, confluence_url, email, and api_token are required. "
                       "Provide as arguments or set environment variables.")
    
    # Create Basic Auth header
    auth_string = f"{email}:{api_token}"
    auth_bytes = auth_string.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
    
    # Construct API endpoint
    api_endpoint = f"{confluence_url}/rest/api/content/search"
    
    # Set headers
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Set search parameters
    params = {
        "cql": query,
        "limit": max_results,
        "expand": "body.preview"
    }
    
    try:
        response = requests.get(
            api_endpoint,
            headers=headers,
            params=params,
            timeout=10
        )
        
        response.raise_for_status()
        search_results = response.json()
        
        results = []
        for result in search_results.get("results", []):
            results.append({
                "page_id": result.get("id", ""),
                "title": result.get("title", ""),
                "type": result.get("type", ""),
                "space": result.get("space", {}).get("key", ""),
                "url": result.get("links", {}).get("webui", ""),
                "preview": result.get("body", {}).get("preview", {}).get("value", "")
            })
        
        return {
            "success": True,
            "total": search_results.get("size", 0),
            "results": results
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }


if __name__ == "__main__":
    import sys
    
    # Example usage
    print("=" * 60)
    print("Confluence API Client - Standalone Module")
    print("=" * 60)
    
    # Check if .env is configured
    print("\n.ENV Configuration Status:")
    env_vars = {
        'CONFLUENCE_PAGE_ID': os.getenv("CONFLUENCE_PAGE_ID"),
        'CONFLUENCE_URL': os.getenv("CONFLUENCE_URL"),
        'CONFLUENCE_EMAIL': os.getenv("CONFLUENCE_EMAIL"),
        'CONFLUENCE_TOKEN': '***' if os.getenv("CONFLUENCE_TOKEN") else 'NOT SET'
    }
    
    for key, value in env_vars.items():
        status = "✓" if value and key != 'CONFLUENCE_TOKEN' else "✗"
        print(f"  {status} {key}: {value if key != 'CONFLUENCE_TOKEN' else value}")
    
    # Example 1: Fetch a page (requires credentials)
    print("\n1. To fetch a Confluence page:")
    print("   from confluence_mcp import fetch_confluence_page")
    print("   result = fetch_confluence_page(")
    print("       page_id='9399541499729',")
    print("       confluence_url='https://tpgtelecom.atlassian.net/wiki',")
    print("       email='your-email@company.com',")
    print("       api_token='your-api-token'")
    print("   )")
    
    # Example 2: Using environment variables
    print("\n2. Or use environment variables (.env file):")
    print("   CONFLUENCE_PAGE_ID=9399541499729")
    print("   CONFLUENCE_URL=https://tpgtelecom.atlassian.net/wiki")
    print("   CONFLUENCE_EMAIL=your-email@company.com")
    print("   CONFLUENCE_TOKEN=your-api-token")
    print("   ---")
    print("   from confluence_mcp import fetch_confluence_page")
    print("   result = fetch_confluence_page()  # Uses .env variables")
    
    # Example 3: Search
    print("\n3. To search for pages:")
    print("   from confluence_mcp import search_confluence_pages")
    print("   results = search_confluence_pages(")
    print("       query=\"type=page AND title ~ 'TMF'\",")
    print("       confluence_url='https://tpgtelecom.atlassian.net/wiki',")
    print("       email='your-email@company.com',")
    print("       api_token='your-api-token',")
    print("       max_results=20")
    print("   )")
    
    # Example 4: Convert to Word document
    print("\n4. To convert page to Word document:")
    print("   from confluence_to_word import create_word_doc_from_confluence")
    print("   create_word_doc_from_confluence()")
    print("   # Output: <Page Title>.docx")
    
    print("\n" + "=" * 60)
    print("✓ Module ready to use in Python code or imported into MCP")
    print("=" * 60)

