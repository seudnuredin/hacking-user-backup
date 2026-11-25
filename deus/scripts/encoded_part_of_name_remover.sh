#!/bin/bash

# Function to remove URL-encoded sequences
remove_url_encoded() {
    local filename="$1"
    # Remove URL-encoded sequences like %20, %2F, etc.
    echo "$filename" | sed 's/%[0-9A-Fa-f][0-9A-Fa-f]//g'
}

# Get the current directory
directory=$(pwd)

# Iterate over all files in the directory
for file in "$directory"/*; do
    # Check if the current item is a file (to avoid directories)
    if [ -f "$file" ]; then
        # Extract the base filename
        filename=$(basename "$file")
        # Remove URL-encoded sequences from the filename
        cleaned_filename=$(remove_url_encoded "$filename")
        # Check if the filename was modified (contains URL-encoded text)
        if [ "$filename" != "$cleaned_filename" ]; then
            # Rename the file
            mv "$file" "$directory/$cleaned_filename"
            echo "Renamed: '$filename' to '$cleaned_filename'"
        fi
    fi
done

