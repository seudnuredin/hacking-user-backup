import multiprocessing
try:
    multiprocessing.set_start_method('fork', force=True)
    print("forked")
except RuntimeError:
    print("unable to fork!")
    exit()
import copy
from http_parser.parser import HttpParser
import json
import subprocess
from urllib.parse import urlparse, parse_qs, parse_qsl, quote, unquote, urlencode, urlunparse
import os
from collections import defaultdict
import urllib.parse
import hashlib
import glob
import re
import psutil
import argparse
import time
from io import BytesIO
import mimetypes
import threading
import requests
from botasaurus.request import request, Request
from botasaurus.browser import browser, Driver
import base64


def custom_parse_qsl(query):
    pairs = query.split('&')
    result = {}
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
        else:
            key, value = pair, ''
        # Use unquote (not unquote_plus) to avoid converting '+' to space
        key = unquote(key)
        value = (value)
        result[key] = value
    return result


def safe_urlencode(data):
    def encode_key_chars_only(s):
        # Only encode '+' and '=' characters
        return ''.join(quote(c) if c in ':?#@& ;=+%' else c for c in s)
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

def add_query_params(url, new_params):
    # Parse the URL
    parsed_url = urlparse(url)

    # Parse existing query parameters
    existing_params = custom_parse_qsl(parsed_url.query)

    # Update with new parameters
    existing_params.update(new_params)

    # Encode parameters back into a query string
    new_query = safe_urlencode(existing_params)

    # Rebuild the URL
    new_url = urlunparse(parsed_url._replace(query=new_query))
    
    return new_url


def extract_query_parameters(url):
    # Parse the URL
    parsed_url = urlparse(url)
    query_string = parsed_url.query
    
    # Parse query string without decoding the values
    query_params = custom_parse_qsl(query_string)
    
    # Re-encode each query parameter value to preserve the original encoding
    # flat_query_params = {key: value for key, value in query_params}

    return query_params


def extract_path(url):

    parsed_url = urlparse(url)
    parsed_path = parsed_url.path

    return parsed_path


def parse_multipart_form_data(content_type, body):
    """Parses a multipart/form-data body into a Python dictionary."""
    form_data = {}

    # Extract boundary from content_type (no need to encode it to bytes)

    boundary = content_type[1]

    boundary = boundary.encode('utf-8')

    # If body is a string, convert it to bytes
    if isinstance(body, str):
        body = body.encode('utf-8')

    # Split the body by boundary (now using string-based splitting)
    parts = body.split(boundary)

    for part in parts:
        if not part or part == b'--\r\n' or part == b'--':
            continue

        if b'\n\n' in part:
            headers, content = part.split(b'\n\n')

            # Process content-disposition headers
            content_disposition = re.search(
                r'Content-Disposition: form-data; name="([^"]+)"(?:; filename="([^"]+)")?', headers)

            if content_disposition:
                name = content_disposition.group(1)
                filename = content_disposition.group(2)

                if filename:
                    # It's a file
                    file_content = content.rstrip(b'\n\n')
                    form_data[name] = {
                        'filename': filename, 'content': file_content}
                else:
                    # It's a regular form field
                    form_data[name] = content.strip()

    return form_data


def parse_http(http_text):
    parser = HttpParser()
    http_text = http_text.encode('utf-8')
    parser.execute(http_text, len(http_text))

    try:
        method = parser.get_method() if parser.get_method() else 'RESPONSE'
        url = parser.get_url()
        path = extract_path(url)
        queries = extract_query_parameters(url)

        headers = dict(parser.get_headers())
        headers_keys = list(headers.keys())
        for header in headers_keys:
            if "etag" == header.lower():
                del headers[header]
            if "if-none-match" == header.lower():
                del headers[header]
            if "last-modified" == header.lower():
                del headers[header]
            if "if-modified-since" == header.lower():
                del headers[header]
            if "if-range" == header.lower():
                del headers[header]
            if "if-unmodified-since" == header.lower():
                del headers[header]
            if "if-match" == header.lower():
                del headers[header]
            if "content-length" == header.lower():
                del headers[header]
        if args.header != None:
            headers[args.header[0]] = args.header[1]

        # Parse the headers' parameters
        for header, value in headers.items():

            if "authorization" == header.lower():
                headers[header] = {'value': value, 'params': {}}
                continue
            
            parts = [v.strip() for v in value.split(';')]
            non_param_value = ""
            params = {}

            for param in parts:
                if re.search(r'=[^=\s]', param):
                    key, val = param.split('=', 1)
                    params[key.strip()] = val.strip()
                else:
                    if len(parts) != parts.index(param) + 1:
                        non_param_value += param + ";"
                    else:
                        non_param_value += param

            headers[header] = {'value': non_param_value, 'params': params}

        # Parse the body based on Content-Type
        body = parser.recv_body()
        parsed_body = None
        if "Content-Type" in headers.keys():
            content_type = str(headers["Content-Type"])

            if body.strip():
                if "json" in content_type.lower():
                    parsed_body = json.loads(body.decode('utf-8'))
                elif "x-www-form-urlencoded" in content_type.lower():
                    parsed_body = {k: v if len(v) == 1 else v for k, v in custom_parse_qsl(body.decode('utf-8')).items()}
                elif "multipart/form-data" in content_type.lower():
                    parsed_body = parse_multipart_form_data(content_type, body)
                else:
                    parsed_body = ""
            else:
                parsed_body = ""

        http_data = {
            'method': method,
            'path': path,
            'queries': queries,
            'headers': headers,
            'body': parsed_body
        }

        return http_data
    except Exception as e:
        # Print the exception
        # print("An exception occurred:", e)
        pass


def permutate_and_send_request(req):
    global payloads
    global args
    global used_proxies_across_processes
    global proxies
    global req_lock
    global signatures_and_their_data_lock
    global reflected_detection_output_lock
    global proxy_setting_lock
    global common_http_headers
    global counter
    global requests_len
    global reqs
    global reqs_and_resps
    global payload
    global expected_to_be_reflected_payload

    # log_file = open("logfile.log", "a")
    # log_file.write(str(reqs.index(req)) + " start 1 \n")
    # log_file.close()

    # if args.rate_limit == None:
    with proxy_setting_lock:
        while True:
            try:
                # proxy = ""
                if args.rate_limit == None:
                    proxy = list(set(proxies) -
                                 set(used_proxies_across_processes))[0]
                else:
                    for l_proxy in proxies:
                        l_proxy_count = used_proxies_across_processes.count(
                            l_proxy)

                        # log_file = open("logfile.log", "a")
                        # log_file.write(f" {l_proxy} {l_proxy_count} \n")
                        # log_file.close()
                        if l_proxy_count < args.rate_limit:
                            # log_file = open("logfile.log", "a")
                            # log_file.write(f" assigned proxy \n")
                            # log_file.close()
                            proxy = l_proxy

                if proxy:
                    used_proxies_across_processes.append(proxy)
                else:
                    raise ValueError("proxy is empty")
                break
            except ValueError as e:
                log_file = open("logfile.log", "a")
                log_file.write(f" Error: {e} from {','.join(proxies)}\n")
                log_file.close()
                time.sleep(2)

    # log_file = open("logfile.log", "a")
    # log_file.write(str(reqs.index(req)) + " end 1\n")
    # log_file.close()

    def search_string_in_file(file_path, search_string):
        """Search for the string in a specific file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if search_string in line:
                        return True
        except (IOError, UnicodeDecodeError):
            # Skip files that can't be opened or read
            return False
        return False

    def search_string_in_directory(directory, search_string):
        """Recursively search for the string in all files within a directory and its subdirectories."""
        for root, dirs, files in os.walk(directory):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if search_string_in_file(file_path, search_string):
                    return True

    def modify_to_unexisting_id(input_str):
        input_str = str(input_str)

        def modify_char(c):
            if c.isdigit():
                if c == '9':
                    return '8'
                else:
                    return '9'
            elif c.isalpha():
                if c.lower() == 'f':
                    return 'e' if c.islower() else 'E'
                else:
                    return 'f' if c.islower() else 'F'
            return c

        modified_input_str = ''.join(modify_char(c) for c in input_str)

        return modified_input_str

    def generate_payload_variations(dict_or_list):
        dict_or_list = copy.deepcopy(dict_or_list)
        """
        Generate variations of the dict_or_listuest by replacing values in 'body' with payloads and calling run_feroxbuster.

        :param dict_or_list: Dictionary containing the dict_or_listuest structure.
        :param payloads: List of payloads to replace the values.
        """
        variations = list()
        if type(dict_or_list) is dict:
            for key, value in dict_or_list.items():
                if type(value) is dict or type(value) is list:
                    # Replace with payload directly
                    for variation in generate_payload_variations(value):
                        permd_dict_or_list = copy.deepcopy(dict_or_list)
                        permd_dict_or_list[key] = variation

                        variations.append(permd_dict_or_list)

                # Replace with payload directly
                permd_dict_or_list = copy.deepcopy(dict_or_list)
                permd_dict_or_list[key] = payload

                variations.append(permd_dict_or_list)

        elif type(dict_or_list) is list:
            if len(dict_or_list) == 0:
                dict_or_list.append(999999999999999999999999999999999999999)

            for key in range(0, len(dict_or_list)):
                value = dict_or_list[key]
                if type(value) is dict or type(value) is list:
                    # Replace with payload directly
                    for variation in generate_payload_variations(value):
                        permd_dict_or_list = copy.deepcopy(dict_or_list)
                        permd_dict_or_list[key] = variation

                        variations.append(permd_dict_or_list)

                # Replace with payload directly
                permd_dict_or_list = copy.deepcopy(dict_or_list)
                permd_dict_or_list[key] = payload

                variations.append(permd_dict_or_list)

        return variations

    def list_different_values(obj1, obj2, parent_key=""):
        differing_keys = []

        # If both are dictionaries
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            common_keys = obj1.keys() & obj2.keys()  # Get the common keys

            for key in common_keys:
                full_key = f"{parent_key}{key}" if not parent_key else f"{parent_key}.{key}"

                if isinstance(obj1[key], dict) and isinstance(obj2[key], dict):
                    # Recursive call for nested dictionaries
                    differing_keys += list_different_values(
                        obj1[key], obj2[key], full_key)
                elif isinstance(obj1[key], list) and isinstance(obj2[key], list):
                    # Handle lists
                    differing_keys += list_different_in_lists(
                        obj1[key], obj2[key], full_key)
                else:
                    if obj1[key] != obj2[key]:  # Compare values
                        differing_keys.append(full_key)

        # If both are lists (at root level)
        elif isinstance(obj1, list) and isinstance(obj2, list):
            differing_keys += list_different_in_lists(obj1, obj2, parent_key)

        return differing_keys

    def list_different_in_lists(list1, list2, parent_key):
        differing_keys = []
        min_len = min(len(list1), len(list2))

        # Compare common indices
        for i in range(min_len):
            full_key = f"{parent_key}.{i}" if parent_key else f"{i}"
            if isinstance(list1[i], dict) and isinstance(list2[i], dict):
                # Recursive call for dictionaries inside lists
                differing_keys += list_different_values(
                    list1[i], list2[i], full_key)
            elif list1[i] != list2[i]:
                differing_keys.append(full_key)

        # Check if one list is longer
        if len(list1) > min_len:
            for i in range(min_len, len(list1)):
                differing_keys.append(
                    f"{parent_key}.{i}" if parent_key else f"{i}")
        elif len(list2) > min_len:
            for i in range(min_len, len(list2)):
                differing_keys.append(
                    f"{parent_key}.{i}" if parent_key else f"{i}")

        return differing_keys

    def generate_md5(content):
        # Create an MD5 hash object
        md5_hash = hashlib.md5()

        # Update the hash object with the bytes-like object (encoded string)
        md5_hash.update(content.encode('utf-8'))

        # Get the hexadecimal representation of the hash
        return md5_hash.hexdigest()

    def clean_filename(filename):
        # Define the valid characters for a Linux filename
        valid_chars = re.compile(r'[^a-zA-Z0-9._-]')

        # Remove any character that is not valid
        cleaned_filename = re.sub(valid_chars, '', filename)

        return cleaned_filename

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
        # Parse the query string to get a dictionary of key-value pairs
        query_params = custom_parse_qsl(query_string)
        # Flatten the dictionary (parse_qs returns a list for each key)
        flat_query_params = {key: value for key, value in query_params.items()}
        return flat_query_params

    def extract_headers(file_path):
        headers = {}
        with open(file_path, 'r') as file:
            req_lines = file.readlines()
            for subdomain in req_lines[1:]:
                if ': ' in subdomain:
                    key, value = subdomain.split(': ', 1)
                    if key.lower() != 'host':
                        headers[key] = value.strip()

        for header, value in headers.items():

            if "authorization" == header.lower():
                headers[header] = {'value': value, 'params': {}}
                continue
            
            parts = [v.strip() for v in value.split(';')]
            non_param_value = ""
            params = {}
            for param in parts:
                if re.search(r'=[^=\s]', param):
                    key, val = param.split('=', 1)
                    params[key.strip()] = val.strip()
                else:
                    if len(parts) != parts.index(param) + 1:
                        non_param_value += param + ";"
                    else:
                        non_param_value += param

            headers[header] = {'value': non_param_value, 'params': params}

        return headers

    def update_dict_with_matches(target_dict, update_dict):
        """
        Updates the target_dict with the values from update_dict if their keys or subkeys match.

        :param target_dict: The original dictionary to be updated.
        :param update_dict: The dictionary with updates.
        :return: None, the target_dict is updated in place.
        """
        for key, value in update_dict.items():
            if key in target_dict:
                if isinstance(value, dict) and isinstance(target_dict[key], dict):
                    update_dict_with_matches(target_dict[key], value)
                else:
                    target_dict[key] = value

    def run_feroxbuster(perm_req, idx_of_request=0, injection_point='not_injected'):

        url = f"https://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"

        if args.delay != None and idx_of_request % args.payloads_number == 0:
            time.sleep(args.delay)

        with req_lock:
            if args.request_file != None:
                if args.payloads_number != None and args.token_expiration == None and args.token_script != None and idx_of_request % args.payloads_number == 0:
                    subprocess.run(f"python3 {args.token_script}", shell=True)

                headers = extract_headers(args.request_file)
                queries = extract_query_parameters(args.request_file)

                update_dict_with_matches(perm_req["queries"], queries)
                update_dict_with_matches(perm_req["headers"], headers)

        if args.delay != None and args.token_script != None and idx_of_request % args.payloads_number == 0 and args.token_expiration == None:
            time.sleep(args.delay)

        # Add queries
        queries = None
        if perm_req["queries"]:
            queries = dict()
            for key, value in perm_req.get('queries', {}).items():
                queries[key] = value.strip()
        
            url = add_query_params(url, queries)

        def sanitize_headers(headers):
            sanitized = {}
            for header_name, header_value in headers.items():
                try:
                    # Ensure header values are latin-1 compatible or URL-encode if needed
                    header_value.encode('latin-1')
                    sanitized[header_name] = header_value
                except UnicodeEncodeError:
                    # Fallback to URL-encoding for non-latin-1 characters
                    sanitized[header_name] = quote(header_value)
            return sanitized

        # Add headers
        headers = None
        if perm_req["headers"]:
            headers = dict()
            for header_name, header_info in perm_req.get('headers', {}).items():
                if header_name.lower() == "host":
                    continue

                header_value = ""
                if header_info['value'] != "":
                    header_value = " " + header_info['value']

                key_count = 0
                for key, value in header_info['params'].items():
                    key_count += 1
                    if key_count != len(header_info['params'].keys()):
                        header_value += f"{key}={value};"
                    else:
                        header_value += f"{key}={value}"

                headers[header_name] = header_value.strip()

            headers = sanitize_headers(headers)

        # Add body if present
        body = None
        if perm_req.get('body'):
            content_type = str(perm_req["headers"]["Content-Type"])
            if "json" in content_type.lower():

                body = json.dumps(perm_req['body'])

            elif "x-www-form-urlencoded" in content_type.lower():

                body = safe_urlencode(perm_req['body'])

            elif "multipart/form-data" in content_type.lower():
                body = build_multipart_form_data(
                    perm_req['body'], content_type)

        def build_multipart_form_data(form_data, content_type):
            """Builds a multipart/form-data body from a Python dictionary."""

            boundary = content_type.split("boundary=")[1]

            body = BytesIO()

            for name, value in form_data.items():
                if isinstance(value, dict) and 'filename' in value:
                    # This is a file
                    filename = value['filename']
                    content = value['content']
                    content_type = mimetypes.guess_type(
                        filename)[0] or 'application/octet-stream'

                    body.write(f'{boundary}\r\n'.encode())
                    body.write(
                        f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode())
                    body.write(
                        f'Content-Type: {content_type}\r\n\r\n'.encode())
                    body.write(content.encode())
                    body.write(b'\r\n')
                else:
                    # This is a regular form field
                    body.write(f'{boundary}\r\n'.encode())
                    body.write(
                        f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
                    body.write(f'{value}\r\n'.encode())

            # End boundary
            body.write(f'{boundary}--\r\n'.encode())

            return body.getvalue()
        

        @browser
        def GET_make_a_request_and_check_if_reflected_payload_is_there(driver: Driver, url):
            response = driver.requests.get(
                url=url,
                headers=headers,
                # params=queries,  # Add query parameters to the URL
                data=body,  # For form or raw body
                timeout=30,  # Set a reasonable timeout
                allow_redirects=True  # Follow redirects if needed
            )

            def get_reqs_signatures():

                req_path_for_signature = ""
                req_unidentified_subpath = 0
                for subpath in req["path"].split("/"):
                    if search_string_in_directory("/usr/share/seclists/Discovery/Web-Content/raft-large", subpath):
                        req_path_for_signature += "/" + subpath
                    else:
                        req_unidentified_subpath += 1

                req_unhashed_signature = f'{req["headers"]["Host"]["value"]}_{req["method"]}_{req_path_for_signature}_{req_unidentified_subpath}_{"_".join(get_all_keys(req))}'
                req_signature = generate_md5(req_unhashed_signature)

                reqs_unhashed_and_hashed_signatures = list()
                reqs_unhashed_and_hashed_signatures.append(
                    req_unhashed_signature)
                reqs_unhashed_and_hashed_signatures.append(req_signature)

                perm_req_path_for_signature = ""
                perm_req_unidentified_subpath = 0
                for subpath in perm_req["path"].split("/"):
                    if search_string_in_directory("/usr/share/seclists/Discovery/Web-Content/raft-large", subpath):
                        perm_req_path_for_signature += "/" + subpath
                    else:
                        perm_req_unidentified_subpath += 1

                perm_req_unhashed_signature = f'{perm_req["headers"]["Host"]["value"]}_{perm_req["method"]}_{perm_req_path_for_signature}_{perm_req_unidentified_subpath}_{"_".join(get_all_keys(perm_req))}'
                perm_req_signature = generate_md5(perm_req_unhashed_signature)

                perm_reqs_unhashed_and_hashed_signatures = list()
                perm_reqs_unhashed_and_hashed_signatures.append(
                    perm_req_unhashed_signature)
                perm_reqs_unhashed_and_hashed_signatures.append(
                    perm_req_signature)

                perm_and_req_signatures = list()
                perm_and_req_signatures.append(
                    reqs_unhashed_and_hashed_signatures)
                perm_and_req_signatures.append(
                    perm_reqs_unhashed_and_hashed_signatures)

                return perm_and_req_signatures

            def make_unique_lines(file_path):
                # Read all lines from the file
                with open(file_path, 'r') as file:
                    lines = file.readlines()

                # Remove duplicates while preserving the order
                unique_lines = list(dict.fromkeys(lines))

                # Write the unique lines back to the file
                with open(file_path, 'w') as file:
                    file.writelines(unique_lines)

            def reflection_detected():
                perm_and_req_signatures = get_reqs_signatures()

                with signatures_and_their_data_lock:
                    with open(f"./signatures_and_their_data.txt", "a") as signatures_and_their_data:
                        signatures_and_their_data.write(f'{perm_and_req_signatures[0][1]} is {perm_and_req_signatures[0][0]}' + "\n")
                        signatures_and_their_data.write(f'{perm_and_req_signatures[1][1]} is {perm_and_req_signatures[1][0]}' + "\n")
                    make_unique_lines(f"./signatures_and_their_data.txt")

                with reflected_detection_output_lock:
                    with open(f"./reflected_detection_output_lock.txt", "a") as signatures_and_their_data:
                        signatures_and_their_data.write(
                            f'{perm_and_req_signatures[0][1]}\'s {injection_point} value {payload} is reflected in {perm_and_req_signatures[1][1]} response as {expected_to_be_reflected_payload}. response content type is {response.headers.get("Content-Type", "Unknown")}' + "\n")
                    make_unique_lines(f"./reflected_detection_output_lock.txt")

            try:
                if "Content-Type" in response.headers.keys():
                    if "json" in response.headers["Content-Type"]:
                        if expected_to_be_reflected_payload in get_all_values(json.loads(response.text)):

                            reflection_detected()
                    else:
                        time.sleep(4)
                        if re.search(re.escape(expected_to_be_reflected_payload.encode("utf-8")), response.content):
                            reflection_detected()
                else:
                    time.sleep(4)
                    if re.search(re.escape(expected_to_be_reflected_payload.encode("utf-8")), response.content):
                        reflection_detected()
                
                if re.search(re.escape(expected_to_be_reflected_payload), str(response.headers)):
                    reflection_detected()
                
            except:
                pass

        # Set proxy
        proxies = {
            'http': f'http://{proxy}',
            'https': f'https://{proxy}'
        } if proxy != "self" else None

        @request(max_retry=1)
        def make_a_request_and_check_if_reflected_payload_is_there(request: Request, url, proxies=proxies):
            if "get" == perm_req['method'].lower():
                response = request.get(
                    url=url,
                    headers=headers,
                    params=queries,  # Add query parameters to the URL
                    data=body,  # For form or raw body
                    timeout=30,  # Set a reasonable timeout
                    allow_redirects=True  # Follow redirects if needed
                )
            elif "post" == perm_req['method'].lower():
                response = request.post(
                    url=url,
                    headers=headers,
                    params=queries,  # Add query parameters to the URL
                    data=body,  # For form or raw body
                    timeout=30,  # Set a reasonable timeout
                    allow_redirects=True  # Follow redirects if needed
                )
            elif "patch" == perm_req['method'].lower():
                response = request.patch(
                    url=url,
                    headers=headers,
                    params=queries,  # Add query parameters to the URL
                    data=body,  # For form or raw body
                    timeout=30,  # Set a reasonable timeout
                    allow_redirects=True  # Follow redirects if needed
                )
            elif "delete" == perm_req['method'].lower():
                response = request.delete(
                    url=url,
                    headers=headers,
                    params=queries,  # Add query parameters to the URL
                    data=body,  # For form or raw body
                    timeout=30,  # Set a reasonable timeout
                    allow_redirects=True  # Follow redirects if needed
                )
            elif "head" == perm_req['method'].lower():
                response = request.head(
                    url=url,
                    headers=headers,
                    params=queries,  # Add query parameters to the URL
                    data=body,  # For form or raw body
                    timeout=30,  # Set a reasonable timeout
                    allow_redirects=True  # Follow redirects if needed
                )
            elif "options" == perm_req['method'].lower():
                response = request.options(
                    url=url,
                    headers=headers,
                    params=queries,  # Add query parameters to the URL
                    data=body,  # For form or raw body
                    timeout=30,  # Set a reasonable timeout
                    allow_redirects=True  # Follow redirects if needed
                )

            def get_reqs_signatures():

                req_path_for_signature = ""
                req_unidentified_subpath = 0
                for subpath in req["path"].split("/"):
                    if search_string_in_directory("/usr/share/seclists/Discovery/Web-Content/raft-large", subpath):
                        req_path_for_signature += "/" + subpath
                    else:
                        req_unidentified_subpath += 1

                req_unhashed_signature = f'{req["headers"]["Host"]["value"]}_{req["method"]}_{req_path_for_signature}_{req_unidentified_subpath}_{"_".join(get_all_keys(req))}'
                req_signature = generate_md5(req_unhashed_signature)

                reqs_unhashed_and_hashed_signatures = list()
                reqs_unhashed_and_hashed_signatures.append(
                    req_unhashed_signature)
                reqs_unhashed_and_hashed_signatures.append(req_signature)

                perm_req_path_for_signature = ""
                perm_req_unidentified_subpath = 0
                for subpath in perm_req["path"].split("/"):
                    if search_string_in_directory("/usr/share/seclists/Discovery/Web-Content/raft-large", subpath):
                        perm_req_path_for_signature += "/" + subpath
                    else:
                        perm_req_unidentified_subpath += 1

                perm_req_unhashed_signature = f'{perm_req["headers"]["Host"]["value"]}_{perm_req["method"]}_{perm_req_path_for_signature}_{perm_req_unidentified_subpath}_{"_".join(get_all_keys(perm_req))}'
                perm_req_signature = generate_md5(perm_req_unhashed_signature)

                perm_reqs_unhashed_and_hashed_signatures = list()
                perm_reqs_unhashed_and_hashed_signatures.append(
                    perm_req_unhashed_signature)
                perm_reqs_unhashed_and_hashed_signatures.append(
                    perm_req_signature)

                perm_and_req_signatures = list()
                perm_and_req_signatures.append(
                    reqs_unhashed_and_hashed_signatures)
                perm_and_req_signatures.append(
                    perm_reqs_unhashed_and_hashed_signatures)

                return perm_and_req_signatures

            def make_unique_lines(file_path):
                # Read all lines from the file
                with open(file_path, 'r') as file:
                    lines = file.readlines()

                # Remove duplicates while preserving the order
                unique_lines = list(dict.fromkeys(lines))

                # Write the unique lines back to the file
                with open(file_path, 'w') as file:
                    file.writelines(unique_lines)

            def reflection_detected():
                perm_and_req_signatures = get_reqs_signatures()

                with signatures_and_their_data_lock:
                    with open(f"./signatures_and_their_data.txt", "a") as signatures_and_their_data:
                        signatures_and_their_data.write(f'{perm_and_req_signatures[0][1]} is {perm_and_req_signatures[0][0]}' + "\n")
                        signatures_and_their_data.write(f'{perm_and_req_signatures[1][1]} is {perm_and_req_signatures[1][0]}' + "\n")
                    make_unique_lines(f"./signatures_and_their_data.txt")

                with reflected_detection_output_lock:
                    with open(f"./reflected_detection_output_lock.txt", "a") as signatures_and_their_data:
                        signatures_and_their_data.write(
                            f'{perm_and_req_signatures[0][1]}\'s {injection_point} value {payload} is reflected in {perm_and_req_signatures[1][1]} response as {expected_to_be_reflected_payload}. response content type is {response.headers.get("Content-Type", "Unknown")}' + "\n")
                    make_unique_lines(f"./reflected_detection_output_lock.txt")

            try:
                if "Content-Type" in response.headers.keys():
                    if "json" in response.headers["Content-Type"]:
                        if expected_to_be_reflected_payload in get_all_values(json.loads(response.text)):

                            reflection_detected()
                    else:
                        time.sleep(4)
                        if re.search(re.escape(expected_to_be_reflected_payload.encode("utf-8")), response.content):
                            reflection_detected()
                else:
                    time.sleep(4)
                    if re.search(re.escape(expected_to_be_reflected_payload.encode("utf-8")), response.content):
                        reflection_detected()
                
                if re.search(re.escape(expected_to_be_reflected_payload), str(response.headers)):
                    reflection_detected()
                
            except:
                pass

        requests_count = 0
        successful_request = False
        while True:
            try:
                # response = requests.request(
                #     method=perm_req['method'],
                #     url=url,
                #     headers=headers,
                #     params=queries,  # Add query parameters to the URL
                #     data=body,  # For form or raw body
                #     timeout=30,  # Set a reasonable timeout
                #     proxies=proxies,  # Proxy configuration
                #     # verify=False,  # Disable SSL verification like `-k` in feroxbuster
                #     allow_redirects=True  # Follow redirects if needed
                # )

                if "get" != perm_req['method'].lower():
                    make_a_request_and_check_if_reflected_payload_is_there(url)
                else:
                    if proxy != "self"
                        GET_make_a_request_and_check_if_reflected_payload_is_there(url=url,proxy=f'http://{proxy}')
                    else:
                        GET_make_a_request_and_check_if_reflected_payload_is_there(url=url)

                    
                successful_request = True
                break
            except Exception as e:
                log_file = open("reflection_and_encodings_identifier.log", "a")
                log_file.write(f"Error: {e} \n")
                log_file.close()

                if requests_count % 2 == 0:
                    url = f"http://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"
                else:
                    url = f"https://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"

            requests_count += 1
            if requests_count == 3:
                break

        if successful_request:
            pass
            # save_response_details(response, output_path + ".json")
            # save_response_content(response, output_path + ".body")

    def get_all_keys(d):
        keys = []
        if isinstance(d, dict):
            for k, v in d.items():
                keys.append(k)
                if isinstance(v, dict) or isinstance(v, list):
                    keys.extend(get_all_keys(v))
                else:
                    json_obj, escaped_or_unescaped = process_and_load_json(v)
                    if isinstance(json_obj, dict) or isinstance(json_obj, list):
                        keys.extend(get_all_keys(json_obj))
        elif isinstance(d, list):
            # keys.append(str(len(d)))
            for v in d:
                if isinstance(v, dict) or isinstance(v, list):
                    keys.extend(get_all_keys(v))
                else:
                    json_obj, escaped_or_unescaped = process_and_load_json(v)
                    if isinstance(json_obj, dict) or isinstance(json_obj, list):
                        keys.extend(get_all_keys(json_obj))
        return keys

    def get_all_values(d):
        values = []
        if isinstance(d, dict):
            for k, v in d.items():
                if not isinstance(v, dict) and not isinstance(v, list):
                    values.append(v)
                if isinstance(v, dict) or isinstance(v, list):
                    values.extend(get_all_values(v))
                else:
                    json_obj, escaped_or_unescaped = process_and_load_json(v)
                    if isinstance(json_obj, dict) or isinstance(json_obj, list):
                        values.extend(get_all_values(json_obj))
        elif isinstance(d, list):
            for v in d:
                if isinstance(v, dict) or isinstance(v, list):
                    values.extend(get_all_values(v))
                else:
                    json_obj, escaped_or_unescaped = process_and_load_json(v)
                    if isinstance(json_obj, dict) or isinstance(json_obj, list):
                        values.extend(get_all_values(json_obj))

        values = [x for x in values if x is not None]
        return values

    def escape_json(json_obj):
        # Convert the JSON object to a string
        json_string = json.dumps(json_obj)

        # Escape the double quotes
        escaped_string = json_string.replace('"', r'\"')

        return escaped_string

    def unescape_json(json_string):
        unescaped_string = json_string.replace(r'\"', '"')

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

    # req_affected_reqs_and_resps = list()
    # for val in get_all_values(req["queries"]):
    #     for req_and_res in reqs_and_resps:
    #         if len(val) > 3 and val in get_all_values(req_and_res[1]):
    #             if req_and_res not in req_affected_reqs_and_resps:
    #                 req_affected_reqs_and_resps.append(req_and_res[0])
    # for val in get_all_values(req["body"]):
    #     for req_and_res in reqs_and_resps:
    #         content_type = ""
    #         try:
    #             content_type = str(req_and_res[1]["headers"]["Content-Type"])
    #         except:
    #             pass
    #         if "json" in str(content_type).lower():
    #             if len(val) > 3 and val in get_all_values(req_and_res[1]):
    #                 if req_and_res not in req_affected_reqs_and_resps:
    #                     req_affected_reqs_and_resps.append(req_and_res[0])
    #         else:
    #             try:
    #                 if len(val) > 3 and re.search(re.escape(val.encode("utf-8")), str(req_and_res[1]).encode("utf-8")):
    #                     if req_and_res not in req_affected_reqs_and_resps:
    #                         req_affected_reqs_and_resps.append(req_and_res[0])
    #             except:
    #                 pass
    


    req_affected_reqs_and_resps = list()
    req_unhashed_signatures = list()
    
    for val in get_all_values(req["queries"]):
        for req_and_res in reqs_and_resps:
            if len(str(val)) > 3 and val in get_all_values(req_and_res[1]):
                req_path_for_signature = ""
                req_unidentified_subpath = 0
                for subpath in req["path"].split("/"):
                    if search_string_in_directory("/usr/share/seclists/Discovery/Web-Content/raft-large", subpath) and not subpath.isdigit():
                        req_path_for_signature += "/" + subpath
                    else:
                        req_unidentified_subpath += 1
                req_unhashed_signature = f'{req_and_res[0]["headers"]["Host"]["value"]}_{req["method"]}_{req_path_for_signature}_{req_unidentified_subpath}_{"_".join(get_all_keys(req_and_res[0]["body"]))}'
                if req_unhashed_signature not in req_unhashed_signatures:
                    req_affected_reqs_and_resps.append(req_and_res[0])
                    req_unhashed_signatures.append(req_unhashed_signature)

    for val in get_all_values(req["body"]):
        for req_and_res in reqs_and_resps:
            content_type = ""
            try:
                content_type = str(req_and_res[1]["headers"]["Content-Type"])
            except:
                pass
            if "json" in str(content_type).lower():
                if len(str(val)) > 3 and val in get_all_values(req_and_res[1]):
                    req_path_for_signature = ""
                    req_unidentified_subpath = 0
                    for subpath in req["path"].split("/"):
                        if search_string_in_directory("/usr/share/seclists/Discovery/Web-Content/raft-large", subpath) and not subpath.isdigit():
                            req_path_for_signature += "/" + subpath
                        else:
                            req_unidentified_subpath += 1
                    req_unhashed_signature = f'{req_and_res[0]["headers"]["Host"]["value"]}_{req["method"]}_{req_path_for_signature}_{req_unidentified_subpath}_{"_".join(get_all_keys(req_and_res[0]))}'
                    if req_unhashed_signature not in req_unhashed_signatures:
                        req_affected_reqs_and_resps.append(req_and_res[0])
                        req_unhashed_signatures.append(req_unhashed_signature)
            else:
                try:
                    if len(str(val)) > 3 and re.search(re.escape(val.encode("utf-8")), str(req_and_res[1]).encode("utf-8")):
                        req_path_for_signature = ""
                        req_unidentified_subpath = 0
                        for subpath in req["path"].split("/"):
                            if search_string_in_directory("/usr/share/seclists/Discovery/Web-Content/raft-large", subpath) and not subpath.isdigit():
                                req_path_for_signature += "/" + subpath
                            else:
                                req_unidentified_subpath += 1
                        req_unhashed_signature = f'{req_and_res[0]["headers"]["Host"]["value"]}_{req["method"]}_{req_path_for_signature}_{req_unidentified_subpath}_{"_".join(get_all_keys(req_and_res[0]))}'
                        if req_unhashed_signature not in req_unhashed_signatures:
                            req_affected_reqs_and_resps.append(req_and_res[0])
                            req_unhashed_signatures.append(req_unhashed_signature)
                except:
                    pass
    
    # fuzzing path
    subpaths = req["path"].split("/")
    for subpath in subpaths:
        if not search_string_in_directory("/usr/share/seclists/Discovery/Web-Content/raft-large", subpath) or subpath.isdigit():

            permd_req = copy.deepcopy(req)
            permd_req["path"] = permd_req["path"].replace(subpath, payload)
            for i in range(0, len(req_affected_reqs_and_resps)):
                run_feroxbuster(permd_req)
                permd_req_affected_reqs_and_resps = copy.deepcopy(req_affected_reqs_and_resps[i])
                run_feroxbuster(permd_req_affected_reqs_and_resps,i, f"{subpaths.index(subpath)}_subpath")
    # fuzzing queries
    if req["queries"]:
        for key, value in req["queries"].items():

            permd_req = copy.deepcopy(req)
            permd_req["queries"][key] = payload
            for i in range(0, len(req_affected_reqs_and_resps)):
                run_feroxbuster(permd_req)
                permd_req_affected_reqs_and_resps = copy.deepcopy(
                    req_affected_reqs_and_resps[i])
                run_feroxbuster(permd_req_affected_reqs_and_resps, i, key)

            json_obj, escaped_or_unescaped = process_and_load_json(value)
            if json_obj != None:
                variations = generate_payload_variations(json_obj)
                for variation in variations:
                    key_for_output = "_".join(
                        list_different_values(json_obj, variation))
                    if escaped_or_unescaped == 0:
                        json_string = json.dumps(variation)
                    elif escaped_or_unescaped == 1:
                        json_string = escape_json(variation)
                    elif escaped_or_unescaped == 2:
                        json_string = encode_json_with_url_encoding(variation)
                    elif escaped_or_unescaped == 3:
                        json_string = encode_base64(variation)

                    permd_req = copy.deepcopy(req)
                    permd_req["queries"][key] = json_string
                    for i in range(0, len(req_affected_reqs_and_resps)):
                        run_feroxbuster(permd_req)

                        permd_req_affected_reqs_and_resps = copy.deepcopy(
                            req_affected_reqs_and_resps[i])
                        run_feroxbuster(
                            permd_req_affected_reqs_and_resps, i, key_for_output)

    if req["headers"]:
        for key, value in req["headers"].items():

            if key in common_http_headers:
                continue

            permd_req = copy.deepcopy(req)
            permd_req["headers"][key]["value"] = payload
            for i in range(0, len(req_affected_reqs_and_resps)):
                run_feroxbuster(permd_req)
                permd_req_affected_reqs_and_resps = copy.deepcopy(
                    req_affected_reqs_and_resps[i])
                run_feroxbuster(permd_req_affected_reqs_and_resps, i, key)

            json_obj, escaped_or_unescaped = process_and_load_json(
                permd_req["headers"][key]["value"])
            if json_obj != None:
                variations = generate_payload_variations(json_obj)
                for variation in variations:
                    key_for_output = "_".join(
                        list_different_values(json_obj, variation))
                    if escaped_or_unescaped == 0:
                        json_string = json.dumps(variation)
                    elif escaped_or_unescaped == 1:
                        json_string = escape_json(variation)
                    elif escaped_or_unescaped == 2:
                        json_string = encode_json_with_url_encoding(variation)
                    elif escaped_or_unescaped == 3:
                        json_string = encode_base64(variation)

                    permd_req = copy.deepcopy(req)
                    permd_req["headers"][key]["value"] = json_string
                    for i in range(0, len(req_affected_reqs_and_resps)):
                        run_feroxbuster(permd_req)

                        permd_req_affected_reqs_and_resps = copy.deepcopy(
                            req_affected_reqs_and_resps[i])
                        run_feroxbuster(
                            permd_req_affected_reqs_and_resps, i, key_for_output)

            for p_key, p_value in req["headers"][key]["params"].items():

                permd_req = copy.deepcopy(req)
                permd_req["headers"][key]["params"][p_key] = payload
                for i in range(0, len(req_affected_reqs_and_resps)):
                    run_feroxbuster(permd_req)
                    permd_req_affected_reqs_and_resps = copy.deepcopy(
                        req_affected_reqs_and_resps[i])
                    run_feroxbuster(
                        permd_req_affected_reqs_and_resps, i, f"{key}_{p_key}")

                json_obj, escaped_or_unescaped = process_and_load_json(p_value)
                if json_obj != None:
                    variations = generate_payload_variations(json_obj)
                    for variation in variations:
                        key_for_output = "_".join(
                            list_different_values(json_obj, variation))
                        if escaped_or_unescaped == 0:
                            json_string = json.dumps(variation)
                        elif escaped_or_unescaped == 1:
                            json_string = escape_json(variation)
                        elif escaped_or_unescaped == 2:
                            json_string = encode_json_with_url_encoding(variation)
                        elif escaped_or_unescaped == 3:
                            json_string = encode_base64(variation)

                        permd_req = copy.deepcopy(req)
                        permd_req["headers"][key]["params"][p_key] = json_string
                        for i in range(0, len(req_affected_reqs_and_resps)):
                            run_feroxbuster(permd_req)

                            permd_req_affected_reqs_and_resps = copy.deepcopy(
                                req_affected_reqs_and_resps[i])
                            run_feroxbuster(
                                permd_req_affected_reqs_and_resps, i, key_for_output)

    # fuzzing body
    if req["body"]:
        variations = generate_payload_variations(req["body"])
        for variation in variations:
            permd_req = copy.deepcopy(req)
            permd_req["body"] = variation

            key = "_".join(list_different_values(
                req["body"], permd_req["body"]))
            for i in range(0, len(req_affected_reqs_and_resps)):
                run_feroxbuster(permd_req)
                permd_req_affected_reqs_and_resps = copy.deepcopy(
                    req_affected_reqs_and_resps[i])
                run_feroxbuster(permd_req_affected_reqs_and_resps, i, key)

        for key, value in req["body"].items():
            json_obj, escaped_or_unescaped = process_and_load_json(value)
            if json_obj != None:
                variations = generate_payload_variations(json_obj)
                for variation in variations:
                    key_for_output = "_".join(
                        list_different_values(json_obj, variation))

                    if escaped_or_unescaped == 0:
                        json_string = json.dumps(variation)
                    elif escaped_or_unescaped == 1:
                        json_string = escape_json(variation)
                    elif escaped_or_unescaped == 2:
                        json_string = encode_json_with_url_encoding(variation)
                    elif escaped_or_unescaped == 3:
                        json_string = encode_base64(variation)

                    permd_req = copy.deepcopy(req)
                    permd_req["body"][key] = json_string
                    for i in range(0, len(req_affected_reqs_and_resps)):
                        run_feroxbuster(permd_req)
                        permd_req_affected_reqs_and_resps = copy.deepcopy(
                            req_affected_reqs_and_resps[i])
                        run_feroxbuster(
                            permd_req_affected_reqs_and_resps, i, key_for_output)

    used_proxies_across_processes.remove(proxy)

    log_file = open("reflection_and_encodings_identifier.log", "a")
    log_file.write("Finished " + str(counter.value) +
                   "/" + str(requests_len) + "\n")
    log_file.close()

    with counter.get_lock():
        counter.value += 1


stop_event = threading.Event()


def token_loop():
    while not stop_event.is_set():
        with req_lock:
            if args.delay is not None:
                time.sleep(args.delay)
            subprocess.run(f"python3 {args.token_script}", shell=True)

        # Wait for expiration but break early if stopped
        for _ in range(int(args.token_expiration)):
            if stop_event.is_set():
                break
            time.sleep(1)

# def token_loop():

#     if stop_event.is_set():
#         return
#     with req_lock:
#         if args.delay != None:
#             time.sleep(args.delay)
#         subprocess.run(f"python3 {args.token_script}", shell=True)

#     threading.Timer(args.token_expiration, token_loop).start()

parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument("-r", "--request-file", required=True, help="Path to the request file containing headers.")
parser.add_argument("-X", "--filter-regex", required=False, help="Filter out messages via regular expression matching on the response's body (ex: -X '^ignore me$')")
parser.add_argument("-a", "--avoid-path", required=False, help="Filter this path or a path that has the input path (deny list) (ex: -a /logout,/deleteuser )")
parser.add_argument('-rl', '--rate-limit', type=int, help='Limit number of requests per second (per directory) (default: 1, i.e. 1 r/s)')
parser.add_argument('-np', '--no-proxy', action='store_true', help='don\'t use proxies and instead use the server ip')
parser.add_argument('-pn', '--payloads-number', type=int, required=False, help='number of payloads supplied per updating req.txt for like new authorization keys')
parser.add_argument('-ts', '--token-script', required=False, help='a python script to execute to generate new authorization keys')
parser.add_argument('-H', '--header', required=False, help='a header to add all requests like -H "X-Hackerone: seudxs"')
parser.add_argument('-p', '--payload', required=False, help='payload to send and payload to look for in output separated by , like <h1>hey</h1>,<h1>hey</h1>')
parser.add_argument('-d', '--delay', type=int, required=False, help='delay in seconds between --payloads-number requests')
parser.add_argument("-nd", "--normal-directory", required=False, help="other account's normal output directory to check against the main output directory for shared injection point value")
parser.add_argument('-te', '--token-expiration', type=int, required=False, help='executes token script everytime token expiration time in minutes is reached')
parser.add_argument("-uf", "--urls-file", required=False, help="urls file to add in the search")

args = parser.parse_args()

proxies = []
if args.no_proxy:
    proxies.append("self")
else:
    with open('/home/deus/documents/proxies.txt') as proxy_file:
        for proxy in proxy_file:
            proxy = proxy.replace("\n", "")
            if proxy != "":
                proxy = proxy.split(':')
                proxies.append(f"isp.smartproxy.com:{proxy[1]}")

manager = multiprocessing.Manager()
used_proxies_across_processes = manager.list()
req_lock = multiprocessing.Lock()
signatures_and_their_data_lock = multiprocessing.Lock()
reflected_detection_output_lock = multiprocessing.Lock()
proxy_setting_lock = multiprocessing.Lock()
counter = multiprocessing.Value('i', 1)

payloads = list()

common_http_headers = [
    # Request Headers
    "A-IM",
    "X-Requested-With",
    "Accept",
    "Accept-Charset",
    "Accept-Datetime",
    "Accept-Encoding",
    "Accept-Language",
    "Access-Control-Request-Method",
    "Access-Control-Request-Headers",
    "Cache-Control",
    "Connection",
    "Content-Length",
    "Content-MD5",
    "Content-Type",
    "Host",
    "Date",
    "Expect",
    "Forwarded",
    "From",
    "If-Match",
    "If-Modified-Since",
    "If-None-Match",
    "If-Range",
    "If-Unmodified-Since",
    "Max-Forwards",
    "Origin",
    "Pragma",
    "Proxy-Authorization",
    "Range",
    "Referer",
    "TE",
    "Trailer",
    "Transfer-Encoding",
    "Upgrade",
    "User-Agent",
    "Via",
    "Warning",
    "Priority",

    # Response Headers
    "Accept-Patch",
    "Accept-Post",
    "Accept-Ranges",
    "Age",
    "Allow",
    "Alt-Svc",
    "Cache-Control",
    "Clear-Site-Data",
    "Connection",
    "Content-Disposition",
    "Content-Encoding",
    "Content-Language",
    "Content-Length",
    "Content-Location",
    "Content-MD5",
    "Content-Range",
    "Content-Security-Policy",
    "Content-Security-Policy-Report-Only",
    "Content-Type",
    "Date",
    "ETag",
    "Expect-CT",
    "Expires",
    "Feature-Policy",
    "Last-Modified",
    "Link",
    "Location",
    "P3P",
    "Pragma",
    "Proxy-Authenticate",
    "Public-Key-Pins",
    "Public-Key-Pins-Report-Only",
    "Retry-After",
    "Server",
    "Set-Cookie",
    "SourceMap",
    "Strict-Transport-Security",
    "Timing-Allow-Origin",
    "Trailer",
    "Transfer-Encoding",
    "Upgrade",
    "Vary",
    "Via",
    "WWW-Authenticate",
    "Warning",
    "X-Content-Type-Options",
    "X-DNS-Prefetch-Control",
    "X-Frame-Options",
    "X-Permitted-Cross-Domain-Policies",
    "X-Powered-By",
    "X-Robots-Tag",
    "X-UA-Compatible",
    "X-XSS-Protection",

    # CORS Headers
    "Access-Control-Allow-Origin",
    "Access-Control-Allow-Credentials",
    "Access-Control-Allow-Headers",
    "Access-Control-Allow-Methods",
    "Access-Control-Expose-Headers",
    "Access-Control-Max-Age",

    # Fetch Metadata Headers
    "Sec-Fetch-Dest",
    "Sec-Fetch-Mode",
    "Sec-Fetch-Site",
    "Sec-Fetch-User",

    # Client Hints Headers
    "Sec-Ch-Ua",
    "Sec-Ch-Ua-Arch",
    "Sec-Ch-Ua-Bitness",
    "Sec-Ch-Ua-Full-Version",
    "Sec-Ch-Ua-Full-Version-List",
    "Sec-Ch-Ua-Mobile",
    "Sec-Ch-Ua-Model",
    "Sec-Ch-Ua-Platform",
    "Sec-Ch-Ua-Platform-Version",
    "Sec-Ch-Prefers-Color-Scheme",
    "Sec-Ch-Viewport-Width",
    "Sec-Ch-Device-Memory",
    "Sec-Ch-Dpr",
    "Sec-Ch-Downgrade",
    "Sec-Ch-Width",

    # Deprecated Headers
    "DNT",  # Do Not Track
    "Keep-Alive",
    "P3P",  # Platform for Privacy Preferences Project
    "TE",   # Transfer Encodings
    "Upgrade-Insecure-Requests",

    # Proxy Headers (X-Forwarded-*)
    "X-Forwarded-For",      # Originating IP address of a client
    "X-Forwarded-Host",     # The original host requested by the client
    "X-Forwarded-Proto",    # The original protocol (HTTP/HTTPS)
    "X-Real-IP",            # Passes the client's IP address
    "X-Forwarded-Port",     # The original port requested by the client
    "X-Client-IP",          # Another header to forward client IP addresses
    "X-Forwarded-Server",   # Proxy server name/address
    "X-Request-ID",         # Tracks requests through a distributed system
    "X-Correlation-ID",     # Tracing requests

    # WebSockets
    "Sec-WebSocket-Key",
    "Sec-WebSocket-Version",
    "Sec-WebSocket-Accept",
    "Sec-WebSocket-Extensions",
    "Sec-WebSocket-Protocol"
]

if (args.payloads_number == None and args.token_expiration == None) and args.token_script != None:
    print("payloads number argument not supplied")
    exit()

if args.payloads_number == None and args.delay != None:
    print("payloads number argument not supplied")
    exit()

if args.payloads_number != None and ((args.token_script == None and args.token_expiration == None) and args.delay == None):
    print("token script or delay argument not supplied")
    exit()

if args.token_expiration != None and args.token_script == None:
    print("token script argument not supplied")
    exit()

if args.avoid_path != None:
    args.avoid_path = args.avoid_path.lower().split(",")

if args.header != None:
    args.header = args.header.split(":")

if args.token_expiration != None:
    args.token_expiration = args.token_expiration * 60
    # token_loop()
    threading.Thread(target=token_loop, daemon=True).start()

if args.rate_limit != None and args.rate_limit < 1:
    print("lmao enter rate limit properly")
    exit()

traffic_unpack_burp_output = list()
for burp_file in os.listdir('./traffic'):
    if os.path.exists("/home/deus/downloads"):
        subprocess.run(
            f"php /home/deus/downloads/unpack-burp/unpack-burp.php ./traffic/{burp_file} all > traffic_unpack_burp_output.txt", shell=True)
    else:
        subprocess.run(
            f"php /home/kali/Downloads/unpack-burp/unpack-burp.php ./traffic/{burp_file} all > traffic_unpack_burp_output.txt", shell=True)

    with open('traffic_unpack_burp_output.txt', 'r') as file:
        traffic_unpack_burp_output.extend(file.read().split("\n\n"))

reqs_unpack_burp_output = list()
for burp_file in os.listdir('./input'):
    if os.path.exists("/home/deus/downloads"):
        subprocess.run(
            f"php /home/deus/downloads/unpack-burp/unpack-burp.php ./input/{burp_file} jsonreq > reqs_unpack_burp_output.txt", shell=True)
    else:
        subprocess.run(
            f"php /home/kali/Downloads/unpack-burp/unpack-burp.php ./input/{burp_file} jsonreq > reqs_unpack_burp_output.txt", shell=True)

    with open('reqs_unpack_burp_output.txt', 'r') as file:
        reqs_unpack_burp_output.extend(file.read().split("\n\n"))

reqs = list()

for req in reqs_unpack_burp_output:
    if req == '':
        continue

    req = json.loads(req)

    if args.avoid_path != None and any(avoid_path in req["reqp"].lower() for avoid_path in args.avoid_path):
        continue

    req_text = req["reqp"].replace(
        "HTTP/2", "HTTP/1.1") + "\r\n" + req["reqh"] + "\r\n\r\n" + req["reqb"] + "\r\n"

    parsed_request = parse_http(req_text)
    if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
        reqs.append(parsed_request)
    else:
        print(req_text)

reqs_and_resps = list()
for req_and_resp in traffic_unpack_burp_output:
    if req_and_resp == '':
        continue

    req_and_resp = json.loads(req_and_resp)

    if args.avoid_path != None and any(avoid_path in req["reqp"].lower() for avoid_path in args.avoid_path):
        continue

    req_text = req_and_resp["reqp"].replace(
        "HTTP/2", "HTTP/1.1") + "\r\n" + req_and_resp["reqh"] + "\r\n\r\n" + req_and_resp["reqb"]
    res_text = req_and_resp["resc"].replace(
        "HTTP/2", "HTTP/1.1") + "\r\n" + req_and_resp["resh"] + "\r\n\r\n" + req_and_resp["resb"]

    parsed_request = parse_http(req_text)
    parsed_response = parse_http(res_text)
    parsed_req_and_resp = list()

    if parsed_request:
        parsed_req_and_resp.append(parsed_request)
    else:
        print(req_text)

    if parsed_response:
        parsed_req_and_resp.append(parsed_response)
    else:
        # print(res_text)
        pass

    reqs_and_resps.append(parsed_req_and_resp)


if args.urls_file:
    with open(args.urls_file, 'r', encoding='utf-8') as urls:
        for url in urls:
            path = extract_path(url)
            queries = extract_query_parameters(url)

            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            headers = dict()
            headers["Host"] = dict()
            headers["Host"] = {'value': hostname}
            headers['User-Agent'] = {'value': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'}
            
            http_data = {
                'method': "GET",
                'path': path,
                'queries': queries,
                'headers': headers,
                'body': ""
            }

            reqs.append(http_data)

if args.header != None:
    args.header = args.header.split(":")

requests_len = len(reqs)


if args.payload != None:
    args.payload = args.payload.split(",")

if args.rate_limit == None:
    pool = multiprocessing.Pool(len(proxies))
else:
    pool = multiprocessing.Pool(len(proxies) * args.rate_limit)

if args.payload == None:
    payload = "xn--c1yn36f"
    expected_to_be_reflected_payload = "點看"
    pool.map(permutate_and_send_request, reqs, chunksize=1)
    
    payload = "bG1hb2xtYW8="
    expected_to_be_reflected_payload = "lmaolmao"
    pool.map(permutate_and_send_request, reqs, chunksize=1)
    
    payload = "6c6d616f6c6d616f"
    expected_to_be_reflected_payload = "lmaolmao"
    pool.map(permutate_and_send_request, reqs, chunksize=1)
    
    payload = "%E9%BB%9E%E7%9C%8B"
    expected_to_be_reflected_payload = "點看"
    pool.map(permutate_and_send_request, reqs, chunksize=1)
    
    # payload = "%25E9%25BB%259E%25E7%259C%258B"
    # expected_to_be_reflected_payload = "點看"
    
    # payload = "%25E9%25BB%259E%25E7%259C%258B%E9%BB%9E%E7%9C%8B"
    # expected_to_be_reflected_payload = "點看點看"
    
    payload = "=E9=BB=9E=E7=9C=8B"
    expected_to_be_reflected_payload = "點看"
    pool.map(permutate_and_send_request, reqs, chunksize=1)
    
    payload = "Ci*U!Ci*U!"
    expected_to_be_reflected_payload = "lmaolmao"
    pool.map(permutate_and_send_request, reqs, chunksize=1)
    
    payload = "&#60;lmao&#62;"
    expected_to_be_reflected_payload = "<lmao>"
    pool.map(permutate_and_send_request, reqs, chunksize=1)
    
    payload = "NRWWC3Y="
    expected_to_be_reflected_payload = "lmao"
    pool.map(permutate_and_send_request, reqs, chunksize=1)
    
    payload = "ᴬlmaoᴬ"
    expected_to_be_reflected_payload = "AlmaoA"
    pool.map(permutate_and_send_request, reqs, chunksize=1)
    
else:
    payload = args.payload[0]
    expected_to_be_reflected_payload = args.payload[1]
    pool.map(permutate_and_send_request, reqs, chunksize=1)


stop_event.set()
