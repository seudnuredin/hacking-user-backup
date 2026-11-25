import argparse
from urllib.parse import urlparse, parse_qs, parse_qsl, quote, unquote, urlencode
import json
import copy
import os
import re

parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument("-r", "--request-file", required=True, help="Path to the request file containing required params.")
parser.add_argument("-map", "--method-and-path-file", required=True, help="a file containing method and path separated by space")
parser.add_argument("-m", "--use-methods", required=False, help="comma-separated methods to use for all paths regardless of their method found in the given file")
args = parser.parse_args()

def escape_json(json_obj):
    # Convert the JSON object to a string
    json_string = json.dumps(json_obj)
    # Escape the double quotes
    escaped_string = json_string.replace('"', r'\"')
    return escaped_string

def unescape_json(json_string):
    unescaped_string = json_string.replace(r'\"','"')
    return unescaped_string

def decode_url_encoded_json(json_string):
    decoded_json_string = unquote(json_string)
    return decoded_json_string

def encode_json_with_url_encoding(json_obj):
    json_string = json.dumps(json_obj)
    encoded_json_string = quote(json_string)
    return encoded_json_string

def encode_base64(data):
    if isinstance(data, dict):  
        data = json.dumps(data)  # Convert dict to JSON string
    if isinstance(data, str):  
        data = data.encode("utf-8")  # Convert string to bytes
    return base64.b64encode(data).decode("utf-8")  # Encode & return as string

def decode_base64(encoded_data):
    byte_data = encoded_data.encode("utf-8")  # Convert string to bytes for decoding
    decoded = base64.b64decode(byte_data)
    return decoded.decode("utf-8")  

def process_and_load_json(string):
    for i in range(4):
        try:
            if i == 1:
                unescaped_json = unescape_json(string)
                json_object = json.loads(unescaped_json)
            elif i == 2:
                decoded_json = decode_url_encoded_json(string)
                json_object = json.loads(decoded_json)
            elif i == 3:
                decoded_json = decode_base64(string)
                json_object = json.loads(decoded_json)
            else:
                json_object = json.loads(string)
            return json_object, i
        except:
            if i == 3:
                return None, i

def get_the_new_or_updated_key_and_its_value(d, value_as_access):
    if isinstance(d, dict):
        for k, v in d.items():
            if "PAYLOADDDD" in k:
                new_d = copy.deepcopy(d)
                new_d.pop(k, None)
                new_d[k.replace("PAYLOADDDD","")] = value_as_access
                
                return new_d
            if isinstance(v, dict) or isinstance(v, list):
                payload = get_the_new_or_updated_key_and_its_value(v, value_as_access)
                if payload:
                    return payload
            else:
                json_obj, escaped_or_unescaped = process_and_load_json(v)
                if isinstance(json_obj, dict) or isinstance(json_obj, list):
                    payload = get_the_new_or_updated_key_and_its_value(json_obj, value_as_access)
                    if payload:
                        return payload
    elif isinstance(d, list):
        for v in d:
            if isinstance(v, dict) or isinstance(v, list):
                payload = get_the_new_or_updated_key_and_its_value(v, value_as_access)
                if payload:
                    return payload
            else:
                json_obj, escaped_or_unescaped = process_and_load_json(v)
                if isinstance(json_obj, dict) or isinstance(json_obj, list):
                    payload = get_the_new_or_updated_key_and_its_value(json_obj, value_as_access)
                    if payload:
                        return payload

def extract_query_parameters(file_path):
    http_request = ""
    with open(file_path, 'r') as file:
        http_request = file.readlines()
    # Extract the first line of the HTTP request (the request line)
    request_line = http_request[0]
    # Split the request line to get the URL part
    method, url, protocol = request_line.split()
    # Parse the URL to extract the query string
    parsed_url = urlparse(url)
    query_string = parsed_url.query
    # # Parse the query string to get a dictionary of key-value pairs
    # query_params = parse_qs(query_string)
    # # Flatten the dictionary (parse_qs returns a list for each key)
    # flat_query_params = {key: value[0] for key, value in query_params.items()}
    return query_string

def extract_headers_without_host(file_path):
    headers = {}
    with open(file_path, 'r') as file:
        req_lines = file.readlines()
        for subdomain in req_lines[1:]:
            if ': ' in subdomain:
                key, value = subdomain.split(': ', 1)
                if key.lower() != 'host':
                    headers[key] = value.strip()
    return headers

def extract_headers_with_host(file_path):
    headers = {}
    with open(file_path, 'r') as file:
        req_lines = file.readlines()
        for subdomain in req_lines[1:]:
            if ': ' in subdomain:
                key, value = subdomain.split(': ', 1)
                # if key.lower() != 'host':
                headers[key] = value.strip()
    return headers


def encode_key_chars_only(s):
    # Only encode '+' and '=' characters
    return ''.join(quote(c) if c in ':?#@& ;=+%' else c for c in s)

def safe_urlencode(data):
    def ensure_not_encoded(value):
        # from urllib.parse import unquote
        # Decode repeatedly until the value is no longer changed by unquoting
        while True:
            decoded = unquote(value)
            if decoded == value:
                return decoded
            value = decoded

    # Apply the decoding to each string value to ensure no double encoding
    safe_data = {
        key: ensure_not_encoded(value) if isinstance(value, str) else value 
        for key, value in data.items()
    }
    
    # Manually build the query string using our custom encoding
    encoded_pairs = []
    for key, value in safe_data.items():
        # Encode the key (if it's a string) using our custom encoder

        if not key.strip():
            continue
        
        if isinstance(key, str):
            encoded_key = encode_key_chars_only(key)
        else:
            encoded_key = key
        
        # For values that are strings, encode them using our custom encoder
        if isinstance(value, str):
            encoded_value = encode_key_chars_only(value)
        else:
            encoded_value = value

        encoded_pairs.append(f"{encoded_key}={encoded_value}")

    return "&".join(encoded_pairs)

def extract_path(file_path):
    with open(file_path, "r") as file:
        for line in file:
            match = re.match(r"^(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (/[^ ]*)", line)
            if match:
                return match.group(2).split("?")[0]  # Extracted path

    return None  # No valid HTTP request line found

query_string = extract_query_parameters(args.request_file)
path = extract_path(args.request_file)

list_of_reqs = list()

with open(args.method_and_path_file, 'r') as method_and_path_file:
    for method_and_path in method_and_path_file:
        method_and_path = method_and_path.strip()
        if not method_and_path:
            continue
        

        method_and_path_list = method_and_path.split(" ")

        is_url = method_and_path_list[1].startswith("http://") or method_and_path_list[1].startswith("https://")

        req_query_string = query_string
        if is_url:
            headers = extract_headers_without_host(args.request_file)
            parsed_url = urlparse(method_and_path_list[1])
            host_header = f"Host: {parsed_url.netloc}\n"
            path = parsed_url.path
            if parsed_url.query:
                if query_string:
                    req_query_string += f"&{parsed_url.query}"
                else:
                    req_query_string += f"{parsed_url.query}"
        else:
            headers = extract_headers_with_host(args.request_file)
            # print(dict(parse_qsl(req_query_string)))
            req_query_string = safe_urlencode(get_the_new_or_updated_key_and_its_value(dict(parse_qsl(req_query_string)), method_and_path_list[1]))

        
        headers_block = "".join(f"{key}: {value}\n" for key, value in headers.items())

        method = method_and_path_list[0]
        if not args.use_methods:
            methods = list()
            methods.append(method)
        else:
            methods = args.use_methods.split(",")

        for method in methods:

            # Build the request line
            request_line = f"{method.upper()} {path}"
            if req_query_string:
                request_line += f"?{req_query_string}"
            request_line += f" HTTP/1.1\n"
            
            headers_without_content_type = copy.deepcopy(headers)

            headers_without_content_type.pop("Content-Length", None)
            if method == "GET" or method == "DELETE":
                headers_without_content_type.pop("Content-Type", None)
            else:
                headers_without_content_type["Content-Type"] = method_and_path_list[2]

            
            headers_block = "".join(f"{key}: {value}\n" for key, value in headers_without_content_type.items())
            # Combine all parts
            if is_url:
                http_request = f"{request_line}{host_header}{headers_block}\n"
            else:
                http_request = f"{request_line}{headers_block}\n"

            if http_request not in list_of_reqs:
                list_of_reqs.append(http_request)
        
output_count = 0
for f_or_d in os.listdir('./'):
    if f"constructed_http_reqs" in f_or_d:
        output_count += 1

with open(f'constructed_http_reqs_{output_count}.json', 'w') as constructed_http_reqs:
    constructed_http_reqs.write(json.dumps(list_of_reqs))

