#!/usr/bin/env python3
"""
Combine multiple markdown files from a folder into a single file.
"""

import os
import glob
from pathlib import Path

def combine_markdown_files(folder_path, output_file="combined.md", sort_files=True):
    """
    Combine all markdown files in a folder into a single file.
    
    Args:
        folder_path (str): Path to the folder containing markdown files
        output_file (str): Name of the output combined file
        sort_files (bool): Whether to sort files alphabetically before combining
    """
    
    # Convert to Path object for easier handling
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist.")
        return
    
    # Find all markdown files (both .md and .markdown extensions)
    md_files = list(folder.glob("*.md")) + list(folder.glob("*.markdown"))
    
    if not md_files:
        print(f"No markdown files found in '{folder_path}'.")
        return
    
    # Sort files alphabetically if requested
    if sort_files:
        md_files.sort()
    
    print(f"Found {len(md_files)} markdown files:")
    for file in md_files:
        print(f"  - {file.name}")
    
    # Combine files
    combined_content = []
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Add a header with the filename
            combined_content.append(f"# {md_file.stem}\n")
            combined_content.append(f"*Source: {md_file.name}*\n")
            combined_content.append(content)
            combined_content.append("\n---\n")  # Add separator between files
            
        except Exception as e:
            print(f"Error reading {md_file.name}: {e}")
            continue
    
    # Write combined content to output file
    output_path = folder / output_file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(combined_content))
        
        print(f"\nSuccessfully combined {len(md_files)} files into '{output_path}'")
        
    except Exception as e:
        print(f"Error writing to output file: {e}")

def main():
    # Get folder path from user
    folder_path = input("Enter the folder path containing markdown files: ").strip()
    
    # Remove quotes if user wrapped path in quotes
    if folder_path.startswith('"') and folder_path.endswith('"'):
        folder_path = folder_path[1:-1]
    
    # Get output filename (optional)
    output_file = input("Enter output filename (default: combined.md): ").strip()
    if not output_file:
        output_file = "combined.md"
    
    # Ask about sorting
    sort_choice = input("Sort files alphabetically? (y/n, default: y): ").strip().lower()
    sort_files = sort_choice != 'n'
    
    # Combine the files
    combine_markdown_files(folder_path, output_file, sort_files)

if __name__ == "__main__":
    main()
