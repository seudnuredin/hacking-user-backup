import os
import re
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def extract_json_object(text):
    # This pattern looks for:
    # - an opening curly brace '{'
    # - followed by any characters non-greedily until it finds a closing curly brace '}'
    # - optionally a trailing double quote (") which we want to include,
    # - and asserts that it is immediately followed by ".js"
    pattern = r'(\{[^{}]*\})(?=\)\[e\]\+"\.js")'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None

def quote_keys(s: str) -> str:
    """
    Walks through the JSON-like string `s` and wraps unquoted keys
    (numeric or otherwise) in double quotes, without using regex.
    """
    result = []
    i, n = 0, len(s)
    expecting_key = False

    while i < n:
        c = s[i]

        # Start of object or new key list
        if c == '{':
            expecting_key = True
            result.append(c)
            i += 1

        # Between key/value pairs
        elif c == ',':
            expecting_key = True
            result.append(c)
            i += 1

        # When we expect a key, handle quoting
        elif expecting_key:
            # Copy over any whitespace
            while i < n and s[i].isspace():
                result.append(s[i])
                i += 1

            # If already a quoted key, copy verbatim
            if i < n and s[i] == '"':
                result.append(s[i])
                i += 1
                while i < n:
                    result.append(s[i])
                    # Handle escape sequences
                    if s[i] == '\\':
                        i += 1
                        if i < n:
                            result.append(s[i])
                    elif s[i] == '"':
                        i += 1
                        break
                    i += 1

            # Otherwise, capture the unquoted key and wrap it
            else:
                start = i
                # Read until colon
                while i < n and s[i] != ':':
                    i += 1
                key = s[start:i].strip()
                result.append(f'"{key}"')

            # Skip whitespace before colon, then append colon
            while i < n and s[i].isspace():
                i += 1
            if i < n and s[i] == ':':
                result.append(':')
                i += 1

            expecting_key = False

        # Default: copy other characters
        else:
            result.append(c)
            i += 1

    return ''.join(result)

def safe_filename(url):
    """
    Convert a URL into a safe file name.
    This extracts the netloc and path, replaces non-alphanumeric characters with underscores,
    and appends .html extension.
    """
    parsed = urlparse(url)
    # Use netloc and path; if path is empty, use "index"
    filename = parsed.netloc + (parsed.path if parsed.path else "/index")
    filename = filename.rstrip("/")
    # Replace any character that isn't alphanumeric or a hyphen with underscore
    filename = re.sub(r'[^A-Za-z0-9\-]+', '_', filename)
    return filename

def write_response_to_file(url, response_text, directory="nextjs_js_outputs"):
    """
    Writes the response_text to a file in the given directory.
    It ensures that an existing file is never overwritten or appended to.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = safe_filename(url)
    file_path = os.path.join(directory, filename)
    counter = 1
    base_name, ext = os.path.splitext(filename)

    # Loop until we find a filename that does not exist.
    while os.path.exists(file_path):
        file_path = os.path.join(directory, f"{base_name}_{counter}{ext}")
        counter += 1

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(response_text)
    print(f"Saved response to {file_path}")

def extract_webpack_hrefs(url):
    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []
    
    write_response_to_file(url, response.text)

    soup = BeautifulSoup(response.text, "html.parser")
    webpack_values = set()
    
    # all_tags_with_href = soup.find_all(href=True)
    for tag in soup.find_all():
        for attr, value in tag.attrs.items():
            if isinstance(value, list):  # Some attributes can be lists
                value = " ".join(value)
            if "webpack" in str(value):
                webpack_values.add(value)

    # webpack_hrefs = [tag['href'] for tag in webpack_values if "webpack" in tag['href']]
    return webpack_values

def download_nextjs_js(url):
    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

    try:
        js_chunks = json.loads(quote_keys(extract_json_object(response.text)))
        # print(f"extract_json_object: {extract_json_object(response.text)}")
        # print(f"quote_keys: {quote_keys(extract_json_object(response.text))}")
    except Exception as e:
        print("An error occurred:", e)
        print(f"extract_json_object: {extract_json_object(response.text)}")
        print(f"quote_keys: {quote_keys(extract_json_object(response.text))}")
        # exit()
    # if js_chunks == None:
        return
    
    hostname = urlparse(url).hostname
    
    for js_chunk_key, js_chunk_value in js_chunks.items():

        # Replace the Webpack path
        new_path = re.sub(r"webpack-[\w\d]+\.js", f"{js_chunk_key}.{js_chunk_value}.js", urlparse(url).path)

        # print(new_path)


        # Rebuild the URL
        parsed = urlparse(url)
        js_chunk_url = urlunparse((parsed.scheme, parsed.netloc, new_path, parsed.params, parsed.query, parsed.fragment))
        # print(js_chunk_url)

        try:
            response = requests.get(js_chunk_url, timeout=10, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching {js_chunk_url}: {e}")
            # return []
        

        write_response_to_file(js_chunk_url, response.text)
        
        
        


def main():
    parser = argparse.ArgumentParser(description="Extract href attributes containing 'webpack' from a URL or list of URLs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u','--url', help="A single URL to process.")
    group.add_argument('-uf','--url-file', help="A file containing URLs (one per line).")
    args = parser.parse_args()
    webpack_urls = []

    if args.url:
        url = args.url

        for webpack_url in extract_webpack_hrefs(url):
            if url[-1] == "/" and webpack_url[0] == "/":
                webpack_url = webpack_url[1:]
            webpack_urls.append(url + webpack_url)

        # print(extract_webpack_hrefs(args.url))
    elif args.url_file:
        try:
            with open(args.url_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            for url in urls:
                for webpack_url in extract_webpack_hrefs(url):
                    if url[-1] == "/" and webpack_url[0] == "/":
                        webpack_url = webpack_url[1:]

                    webpack_urls.append(url + webpack_url)
        except Exception as e:
            print(f"Error reading file: {e}")
    
    for webpack_url in webpack_urls:
        download_nextjs_js(webpack_url)
    

if __name__ == "__main__":
    main()
