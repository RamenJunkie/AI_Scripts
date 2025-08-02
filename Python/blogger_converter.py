#!/usr/bin/env python3
"""
Blogger XML to Markdown Converter

This script converts Blogger export XML files to individual markdown files.
It extracts blog entries and converts HTML content to markdown format.
"""

import xml.etree.ElementTree as ET
import re
import html
import os
from datetime import datetime
from urllib.parse import urlparse
import argparse


def clean_filename(title):
    """Convert title to a safe filename."""
    # Remove HTML tags if any
    title = re.sub(r'<[^>]+>', '', title)
    # Replace spaces and special characters
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[-\s]+', '-', title)
    return title.strip('-').lower()


def html_to_markdown(html_content):
    """Convert HTML content to markdown format."""
    if not html_content:
        return ""
    
    # Decode HTML entities
    content = html.unescape(html_content)
    
    # Convert images to markdown format
    img_pattern = r'<img[^>]+src="([^"]+)"[^>]*(?:alt="([^"]*)")?[^>]*>'
    content = re.sub(img_pattern, lambda m: f'![{m.group(2) or ""}]({m.group(1)})', content)
    
    # Convert links to markdown format
    link_pattern = r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>'
    content = re.sub(link_pattern, r'[\2](\1)', content, flags=re.DOTALL)
    
    # Convert headings
    content = re.sub(r'<h([1-6])[^>]*>(.*?)</h[1-6]>', lambda m: '#' * int(m.group(1)) + ' ' + m.group(2), content, flags=re.DOTALL)
    
    # Convert paragraphs
    content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.DOTALL)
    
    # Convert line breaks
    content = re.sub(r'<br\s*/?>', '\n', content)
    
    # Convert bold and italic
    content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.DOTALL)
    content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.DOTALL)
    content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.DOTALL)
    content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.DOTALL)
    
    # Convert lists
    content = re.sub(r'<ul[^>]*>(.*?)</ul>', lambda m: convert_list(m.group(1), 'ul'), content, flags=re.DOTALL)
    content = re.sub(r'<ol[^>]*>(.*?)</ol>', lambda m: convert_list(m.group(1), 'ol'), content, flags=re.DOTALL)
    
    # Convert blockquotes
    content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', lambda m: '> ' + m.group(1).strip().replace('\n', '\n> '), content, flags=re.DOTALL)
    
    # Convert code blocks
    content = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'```\n\1\n```', content, flags=re.DOTALL)
    content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', content, flags=re.DOTALL)
    
    # Remove remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Clean up extra whitespace
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    content = re.sub(r'&nbsp;', ' ', content)
    
    return content.strip()


def convert_list(list_content, list_type):
    """Convert HTML list to markdown format."""
    items = re.findall(r'<li[^>]*>(.*?)</li>', list_content, flags=re.DOTALL)
    markdown_items = []
    
    for i, item in enumerate(items):
        item = re.sub(r'<[^>]+>', '', item).strip()
        if list_type == 'ul':
            markdown_items.append(f'- {item}')
        else:  # ol
            markdown_items.append(f'{i+1}. {item}')
    
    return '\n' + '\n'.join(markdown_items) + '\n'


def format_date(date_string):
    """Format the published date."""
    try:
        # Parse the date (format: 2024-12-18T19:26:00.000-08:00)
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except:
        return date_string


def extract_blog_entries(xml_file, output_dir='blog_posts'):
    """Extract blog entries from Blogger XML and convert to markdown files."""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse the XML file
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        return
    
    # Define namespaces
    namespaces = {
        'atom': 'http://www.w3.org/2005/Atom',
        'app': 'http://purl.org/atom/app#'
    }
    
    entries_processed = 0
    
    # Find all entry elements
    for entry in root.findall('.//atom:entry', namespaces):
        # Skip settings entries
        category = entry.find('atom:category[@scheme="http://schemas.google.com/g/2005#kind"]', namespaces)
        if category is not None and 'settings' in category.get('term', ''):
            continue
        
        # Check if it's a draft (but don't skip - just note it)
        is_draft = False
        control = entry.find('app:control', namespaces)
        if control is not None:
            draft = control.find('app:draft', namespaces)
            if draft is not None and draft.text == 'yes':
                is_draft = True
        
        # Extract title
        title_elem = entry.find('atom:title[@type="text"]', namespaces)
        title = title_elem.text if title_elem is not None else 'Untitled'
        
        # Extract published date
        published_elem = entry.find('atom:published', namespaces)
        if published_elem is None:
            continue
        
        published_date = format_date(published_elem.text)
        
        # Extract content
        content_elem = entry.find('atom:content[@type="html"]', namespaces)
        if content_elem is None:
            continue
        
        html_content = content_elem.text or ''
        markdown_content = html_to_markdown(html_content)
        
        # Create filename
        safe_title = clean_filename(title)
        draft_prefix = "draft-" if is_draft else ""
        filename = f"{draft_prefix}{published_date}-{safe_title}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Write markdown file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"**Date:** {published_date}\n")
            if is_draft:
                f.write(f"**Status:** Draft\n")
            f.write(f"\n{markdown_content}\n")
        
        print(f"Created: {filename}")
        entries_processed += 1
    
    print(f"\nProcessed {entries_processed} blog entries.")


def main():
    """Main function to run the converter."""
    parser = argparse.ArgumentParser(description='Convert Blogger XML export to Markdown files')
    parser.add_argument('xml_file', help='Path to the Blogger XML export file')
    parser.add_argument('-o', '--output', default='blog_posts', help='Output directory for markdown files')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.xml_file):
        print(f"Error: File '{args.xml_file}' not found.")
        return
    
    print(f"Converting '{args.xml_file}' to markdown files...")
    print(f"Output directory: {args.output}")
    
    extract_blog_entries(args.xml_file, args.output)


if __name__ == '__main__':
    main()
