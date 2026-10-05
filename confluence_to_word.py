#!/usr/bin/env python3
"""
Confluence to Word Document Converter
Fetches content from Confluence and creates a properly formatted Word document
with full content preservation including tables, lists, and formatting
"""

from confluence_mcp import fetch_confluence_page
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re
from datetime import datetime
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
Confluence to Word Document Converter
Fetches content from Confluence and creates a properly formatted Word document
with full content preservation including tables, lists, and formatting
"""

from confluence_mcp import fetch_confluence_page
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re
from datetime import datetime
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def decode_html_entities(text):
    """Decode HTML entities to proper characters"""
    entities = {
        '&nbsp;': ' ',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&#39;': "'",
        '&quot;': '"',
        '&apos;': "'",
        '&copy;': '©',
        '&reg;': '®',
        '&euro;': '€',
        '&pound;': '£',
        '&yen;': '¥',
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)
    # Handle numeric entities
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    return text

def get_cell_background_color(soup_cell):
    """Extract background color from table cell"""
    style = soup_cell.get('style', '')
    bgcolor = soup_cell.get('data-highlight-colour', '')
    if bgcolor:
        return bgcolor
    if 'background' in style:
        match = re.search(r'background[^:]*:\s*([^;]+)', style)
        if match:
            return match.group(1).strip()
    return None

def set_cell_background(cell, color):
    """Set cell background color in Word"""
    if not color:
        return
    # Remove # if present
    color = color.lstrip('#').upper()
    # Handle color names
    color_map = {
        'F4F5F7': 'D3D3D3',  # Light gray
        'FFFFFF': 'FFFFFF',  # White
        'F0F1F2': 'E6E6E6',  # Slightly darker gray
    }
    color = color_map.get(color, color)
    
    try:
        tcPr = cell._element.tcPr
        if tcPr is None:
            tcPr = OxmlElement('w:tcPr')
            cell._element.insert(0, tcPr)
        shd = OxmlElement('w:shd')
        shd.set(qn('w:fill'), color)
        tcPr.append(shd)
    except Exception as e:
        logger.warning(f"Could not set cell background: {e}")

def parse_and_add_table(doc, soup_table):
    """Parse HTML table and add as Word table"""
    try:
        rows = soup_table.find_all('tr')
        if not rows:
            return
        
        # Count columns
        cols = 0
        for row in rows:
            cells = row.find_all(['td', 'th'])
            cols = max(cols, len(cells))
        
        # Create Word table
        table = doc.add_table(rows=len(rows), cols=cols)
        table.style = 'Light Grid Accent 1'
        
        # Fill table
        for row_idx, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            for col_idx, cell in enumerate(cells):
                word_cell = table.rows[row_idx].cells[min(col_idx, cols - 1)]
                
                # Get background color
                bg_color = get_cell_background_color(cell)
                set_cell_background(word_cell, bg_color)
                
                # Add content
                cell_text = cell.get_text(strip=True)
                cell_text = decode_html_entities(cell_text)
                
                # Clear existing paragraph
                word_cell.text = ''
                
                # Add formatted content
                if cell_text:
                    p = word_cell.paragraphs[0]
                    is_header = cell.name == 'th'
                    
                    run = p.add_run(cell_text)
                    if is_header:
                        run.bold = True
                        run.font.color.rgb = RGBColor(0, 0, 0)
        
        doc.add_paragraph()  # Add spacing after table
        
    except Exception as e:
        logger.warning(f"Error parsing table: {e}")

def parse_and_add_html_content(doc, html_content):
    """Parse HTML content and add to Word document with formatting"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
        
        # Process all elements
        for element in soup.children:
            if isinstance(element, str):
                text = element.strip()
                if text and text != '\n':
                    decoded_text = decode_html_entities(text)
                    if decoded_text.strip():
                        doc.add_paragraph(decoded_text)
            else:
                tag_name = element.name if element.name else ''
                
                # Handle headings
                if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    level = int(tag_name[1])
                    text = element.get_text(strip=True)
                    text = decode_html_entities(text)
                    if text:
                        doc.add_heading(text, level=level)
                
                # Handle paragraphs
                elif tag_name == 'p':
                    text = element.get_text(strip=True)
                    text = decode_html_entities(text)
                    if text:
                        p = doc.add_paragraph(text)
                        # Check for bold/italic
                        if element.find('strong') or element.find('b'):
                            for run in p.runs:
                                run.bold = True
                        if element.find('em') or element.find('i'):
                            for run in p.runs:
                                run.italic = True
                
                # Handle tables
                elif tag_name == 'table':
                    parse_and_add_table(doc, element)
                
                # Handle unordered lists
                elif tag_name == 'ul':
                    for li in element.find_all('li', recursive=False):
                        text = li.get_text(strip=True)
                        text = decode_html_entities(text)
                        if text:
                            doc.add_paragraph(text, style='List Bullet')
                
                # Handle ordered lists
                elif tag_name == 'ol':
                    for li in element.find_all('li', recursive=False):
                        text = li.get_text(strip=True)
                        text = decode_html_entities(text)
                        if text:
                            doc.add_paragraph(text, style='List Number')
                
                # Handle divs with table-wrap
                elif tag_name == 'div' and 'table-wrap' in element.get('class', []):
                    table = element.find('table')
                    if table:
                        parse_and_add_table(doc, table)
                
                # Handle other divs recursively
                elif tag_name == 'div':
                    parse_and_add_html_content(doc, str(element))
        
    except Exception as e:
        logger.error(f"Error parsing HTML content: {e}")
        # Fallback: add plain text
        text_only = BeautifulSoup(html_content, 'html.parser').get_text()
        doc.add_paragraph(text_only)

def create_word_doc_from_confluence(output_filename=None):
    """
    Fetch Confluence page and create properly formatted Word document
    
    Args:
        output_filename: Output Word file name (default: uses page title)
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    logger.info("=" * 70)
    logger.info("Confluence to Word Document Converter (Enhanced)")
    logger.info("=" * 70)
    
    # Fetch page from Confluence
    logger.info("\n1. Fetching page from Confluence...")
    result = fetch_confluence_page()
    
    if not result['success']:
        logger.error(f"✗ Error fetching page: {result['error']}")
        return False
    
    logger.info(f"✓ Page fetched: {result['title']}")
    
    # Extract content
    page_title = result['title']
    page_type = result['type']
    space = result['space']
    created = result['metadata']['created']
    modified = result['metadata']['modified']
    body_html = result['body'].get('storage', {}).get('value', '')
    
    # Create Word document
    logger.info("\n2. Creating Word document...")
    doc = Document()
    
    # Add title
    title = doc.add_heading(page_title, level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add metadata section
    metadata = doc.add_heading('Document Information', level=1)
    metadata_table = doc.add_table(rows=5, cols=2)
    metadata_table.style = 'Light Grid Accent 1'
    
    metadata_data = [
        ('Type', page_type),
        ('Space', space),
        ('Created', created),
        ('Modified', modified),
        ('Retrieved', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    ]
    
    for idx, (key, value) in enumerate(metadata_data):
        metadata_table.rows[idx].cells[0].text = key
        metadata_table.rows[idx].cells[1].text = value
    
    doc.add_paragraph()  # Spacing
    
    # Add content
    logger.info("3. Processing content...")
    
    try:
        parse_and_add_html_content(doc, body_html)
        logger.info("✓ Content processed successfully")
    except Exception as e:
        logger.error(f"Error processing content: {e}")
        # Fallback: add plain text
        soup = BeautifulSoup(body_html, 'html.parser')
        text_only = soup.get_text()
        doc.add_paragraph(text_only)
    
    # Generate filename
    if not output_filename:
        # Create filename from page title
        safe_title = re.sub(r'[<>:"/\\|?*]', '', page_title)
        output_filename = f"{safe_title}.docx"
    
    # Save document
    logger.info(f"\n4. Saving to {output_filename}...")
    doc.save(output_filename)
    
    logger.info("=" * 70)
    logger.info(f"✓ SUCCESS! Document created: {output_filename}")
    logger.info("=" * 70)
    logger.info(f"\nYou can now use this file with @IFC Swagger Converter agent:")
    logger.info(f"  @IFC Swagger Converter Convert {output_filename} to OpenAPI 3.0 YAML")
    
    return True

if __name__ == "__main__":
    import sys
    
    # Handle command line arguments
    output_filename = sys.argv[1] if len(sys.argv) > 1 else None
    
    logger.info("\n")
    create_word_doc_from_confluence(output_filename=output_filename)
