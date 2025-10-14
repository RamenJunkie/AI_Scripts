import json

# Read the JSON file
input_file = 'books.json'  # Change this to your input file name
output_file = 'not_liberated_books.txt'

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter entries where BookStatus is "Not Liberated"
    not_liberated = []
    
    # Handle both list of objects and single object
    if isinstance(data, list):
        books = data
    else:
        books = [data]
    
    for book in books:
        if book.get('BookStatus') == 'NotLiberated' and book.get('ContentType') != 'Episode':
            print(f"{book.get('AuthorNames')} {book.get('Title')}")
            author = book.get('AuthorNames', 'Unknown Author')
            title = book.get('Title', 'Unknown Title')
            not_liberated.append(f"{author} - {title}")
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in not_liberated:
            f.write(entry + '\n')
    
    print(f"Found {len(not_liberated)} books with 'Not Liberated' status")
    print(f"Results written to {output_file}")

except FileNotFoundError:
    print(f"Error: Could not find file '{input_file}'")
except json.JSONDecodeError:
    print(f"Error: Invalid JSON format in '{input_file}'")
except Exception as e:
    print(f"Error: {e}")
