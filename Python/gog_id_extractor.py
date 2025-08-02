#!/usr/bin/env python3
"""
Script to extract _id_mirror values from a JSON-style file containing GOG game data.
Usage: python extract_gog_ids.py <input_filename>
Output: Creates gog_ids.txt with one ID per line
"""

import json
import sys
import ast

def extract_gog_ids(input_filename):
    """
    Extract _id_mirror values from the input file and save to gog_ids.txt
    
    Args:
        input_filename (str): Path to the input JSON-style file
    """
    try:
        with open(input_filename, 'r', encoding='utf-8') as file:
            content = file.read().strip()
        
        # Try to parse as JSON first
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to evaluate as Python literal
            # This handles cases where the file might be Python dict/list format
            try:
                data = ast.literal_eval(content)
            except (ValueError, SyntaxError) as e:
                print(f"Error: Could not parse the file as JSON or Python literal: {e}")
                return False
        
        # Extract _id_mirror values
        id_mirrors = []
        
        if isinstance(data, list):
            # Data is a list of dictionaries
            for item in data:
                if isinstance(item, dict) and '_id_mirror' in item:
                    id_mirrors.append(str(item['_id_mirror']))
        elif isinstance(data, dict) and '_id_mirror' in data:
            # Data is a single dictionary
            id_mirrors.append(str(data['_id_mirror']))
        else:
            print("Error: Input data format not recognized. Expected list of dicts or single dict with '_id_mirror' key.")
            return False
        
        # Write to output file
        with open('gog_ids.txt', 'w', encoding='utf-8') as output_file:
            for id_mirror in id_mirrors:
                output_file.write(f"{id_mirror}\n")
        
        print(f"Successfully extracted {len(id_mirrors)} IDs to gog_ids.txt")
        return True
        
    except FileNotFoundError:
        print(f"Error: File '{input_filename}' not found.")
        return False
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) != 2:
        print("Usage: python extract_gog_ids.py <input_filename>")
        print("Example: python extract_gog_ids.py paste.txt")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    success = extract_gog_ids(input_filename)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()