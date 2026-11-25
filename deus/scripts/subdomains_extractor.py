import os
import re
import sys

def extract_surrounding_text(file_path, search_string, context_size=20):
    """Extracts 20 characters before and after the search string in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            pattern = re.compile(rf'.{{0,{context_size}}}{re.escape(search_string)}.{{0,{context_size}}}', re.DOTALL)
            matches = pattern.findall(content)
            return matches
    except (IOError, UnicodeDecodeError) as e:
        #print(f"Error reading {file_path}: {e}")
        return []

def search_directory(directory, search_string):
    """Searches through all files in a directory and its subdirectories."""
    results = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            matches = extract_surrounding_text(file_path, search_string)
            if matches:
                results.append((file_path, matches))
    return results

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <directory> <search_string>")
        sys.exit(1)

    directory = sys.argv[1]
    search_string = sys.argv[2]

    if not os.path.isdir(directory):
        print(f"The directory {directory} does not exist.")
        sys.exit(1)

    results = search_directory(directory, search_string)

    if results:
        for file_path, matches in results:
            #print(f"\nIn file: {file_path}")
            for match in matches:
                print(match)
    else:
        print("No matches found.")

if __name__ == "__main__":
    main()

