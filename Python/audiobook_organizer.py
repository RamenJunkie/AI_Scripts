#!/usr/bin/env python3
"""
Organizes audiobook folders by author based on books.json metadata.
"""

import json
import os
import re
import shutil
from pathlib import Path


def extract_product_id(folder_name):
    """Extract the Audible product ID from folder name like 'Title [B0CYDWFPMV]'"""
    match = re.search(r'\[([A-Z0-9]+)\]', folder_name)
    return match.group(1) if match else None


def load_books_data(json_path):
    """Load and return the books.json data"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_path} not found")
        return None
    except json.JSONDecodeError:
        print(f"Error: {json_path} is not valid JSON")
        return None


def find_book_by_id(books_data, product_id):
    """Find book entry in books.json by product ID"""
    # Handle both list and dict formats
    if isinstance(books_data, list):
        for book in books_data:
            if book.get('AudibleProductId') == product_id:
                return book
    elif isinstance(books_data, dict):
        # If it's a dict with books as values
        for book in books_data.values():
            if book.get('AudibleProductId') == product_id:
                return book
    return None


def get_author_folder_name(author_names):
    """Determine the folder name based on author(s)"""
    if not author_names:
        return "Unknown"
    
    # Check if multiple authors (contains comma)
    if ',' in author_names:
        return "Multiple"
    
    return author_names.strip()


def sanitize_folder_name(name):
    """Remove or replace characters that are problematic in folder names"""
    # Replace problematic characters with underscore
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    return sanitized


def main():
    script_dir = Path(__file__).parent.resolve()
    json_file = script_dir / 'books.json'
    
    print(f"Working directory: {script_dir}")
    print(f"Looking for books.json at: {json_file}")
    
    # Load books data
    books_data = load_books_data(json_file)
    if books_data is None:
        return
    
    print(f"Successfully loaded books.json")
    
    # Get all subdirectories in the current folder
    folders = [f for f in script_dir.iterdir() if f.is_dir()]
    print(f"Found {len(folders)} folders to process\n")
    
    moved_count = 0
    skipped_count = 0
    
    for folder in folders:
        folder_name = folder.name
        
        # Extract product ID from folder name
        product_id = extract_product_id(folder_name)
        
        if not product_id:
            print(f"⚠ Skipping '{folder_name}' - no product ID found")
            skipped_count += 1
            continue
        
        # Find book in JSON
        book = find_book_by_id(books_data, product_id)
        
        if not book:
            print(f"⚠ Skipping '{folder_name}' - product ID {product_id} not found in books.json")
            skipped_count += 1
            continue
        
        # Get author name(s)
        author_names = book.get('AuthorNames', '')
        author_folder_name = get_author_folder_name(author_names)
        author_folder_name = sanitize_folder_name(author_folder_name)
        
        # Create author folder if it doesn't exist
        author_folder = script_dir / author_folder_name
        author_folder.mkdir(exist_ok=True)
        
        # Move the book folder into author folder
        destination = author_folder / folder_name
        
        # Check if destination already exists
        if destination.exists():
            print(f"⚠ Skipping '{folder_name}' - already exists in '{author_folder_name}'")
            skipped_count += 1
            continue
        
        try:
            shutil.move(str(folder), str(destination))
            print(f"✓ Moved '{folder_name}' → '{author_folder_name}/'")
            moved_count += 1
        except Exception as e:
            print(f"✗ Error moving '{folder_name}': {e}")
            skipped_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Moved: {moved_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
