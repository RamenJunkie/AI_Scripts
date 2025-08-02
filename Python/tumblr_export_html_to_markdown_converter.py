#!/usr/bin/env python3
"""
HTML to Markdown Converter
Converts HTML files to Markdown format with custom image paths and date-based filenames.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import html2text

def extract_date_from_html(html_content):
    """
    Extract date from HTML content in format 'January 15th, 2025 7:37am'
    Returns formatted date as YYYY.MM.DD or None if not found
    """
    # Pattern to match dates like "January 15th, 2025 7:37am"
    date_pattern = r'(\w+)\s+(\d+)(?:st|nd|rd|th),?\s+(\d{4})\s+(\d+):(\d+)(?:am|pm)'
    
    match = re.search(date_pattern, html_content, re.IGNORECASE)
    if match:
        month_name, day, year, hour, minute = match.groups()
        
        # Convert month name to number
        month_names = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        month_num = month_names.get(month_name.lower())
        if month_num:
            return f"{year}.{month_num:02d}.{int(day):02d}"
    
    return None

def convert_image_paths(markdown_content):
    """
    Convert image paths to point to tumblrmedia/[ImageFileName]
    Handles both markdown image syntax and HTML img tags
    """
    # Pattern to match markdown image syntax: ![alt](path)
    def replace_markdown_image_path(match):
        alt_text = match.group(1)
        original_path = match.group(2)
        
        # Extract just the filename from the path
        filename = os.path.basename(original_path)
        new_path = f"tumblrmedia/{filename}"
        
        return f"![{alt_text}]({new_path})"
    
    # Pattern to match markdown link syntax that should be images: [text](image_path)
    def replace_image_links(match):
        link_text = match.group(1)
        original_path = match.group(2)
        
        # Check if this looks like an image file
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        if any(original_path.lower().endswith(ext) for ext in image_extensions):
            filename = os.path.basename(original_path)
            new_path = f"tumblrmedia/{filename}"
            # Convert link to embedded image
            return f"![{link_text}]({new_path})"
        else:
            # Keep as regular link
            return f"[{link_text}]({original_path})"
    
    # Replace existing markdown image paths
    markdown_content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_markdown_image_path, markdown_content)
    
    # Convert image links to embedded images
    markdown_content = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', replace_image_links, markdown_content)
    
    return markdown_content

def html_to_markdown(html_content):
    """
    Convert HTML content to Markdown using html2text
    """
    # Configure html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap lines
    h.unicode_snob = True
    h.ignore_tables = False
    
    # Convert to markdown
    markdown = h.handle(html_content)
    
    return markdown

def process_html_folder(input_folder, output_folder=None):
    """
    Process all HTML files in the input folder and convert to Markdown
    """
    input_path = Path(input_folder)
    
    if not input_path.exists():
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return
    
    # Set output folder to current directory if not specified
    if output_folder is None:
        output_path = Path(".")
    else:
        output_path = Path(output_folder)
        output_path.mkdir(exist_ok=True)
    
    # Process each HTML file
    html_files = list(input_path.glob("*.html"))
    
    if not html_files:
        print(f"No HTML files found in '{input_folder}'")
        return
    
    print(f"Found {len(html_files)} HTML files to process...")
    
    for html_file in html_files:
        try:
            # Read HTML content
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract date from HTML
            date_str = extract_date_from_html(html_content)
            
            if not date_str:
                print(f"Warning: Could not extract date from {html_file.name}, skipping...")
                continue
            
            # Convert HTML to Markdown
            markdown_content = html_to_markdown(html_content)
            
            # Convert image paths
            markdown_content = convert_image_paths(markdown_content)
            
            # Create output filename
            base_name = html_file.stem  # filename without extension
            output_filename = f"{date_str} - {base_name}.md"
            output_file_path = output_path / output_filename
            
            # Write markdown file
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"Converted: {html_file.name} -> {output_filename}")
            
        except Exception as e:
            print(f"Error processing {html_file.name}: {str(e)}")
    
    print("Conversion complete!")

def main():
    """
    Main function to run the converter
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert HTML files to Markdown with custom formatting')
    parser.add_argument('input_folder', help='Path to folder containing HTML files')
    parser.add_argument('-o', '--output', help='Output folder (default: current directory)', default=None)
    
    args = parser.parse_args()
    
    # Check if html2text is available
    try:
        import html2text
    except ImportError:
        print("Error: html2text library is required. Install it with: pip install html2text")
        return
    
    # Check if BeautifulSoup is available
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Error: beautifulsoup4 library is required. Install it with: pip install beautifulsoup4")
        return
    
    process_html_folder(args.input_folder, args.output)

if __name__ == "__main__":
    # If running directly, you can modify these paths:
    input_folder = "html"  # Change this to your HTML folder path
    output_folder = None   # None means current directory, or specify a path
    
    # Uncomment the line below to run with command line arguments instead
    # main()
    
    # Run the conversion
    process_html_folder(input_folder, output_folder)
