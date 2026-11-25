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
from urllib.parse import urlparse, parse_qs, parse_qsl, quote, unquote
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
# import faulthandler
# faulthandler.dump_traceback_later(5, repeat=True)


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
    
    # Split the body by boundary (now using string-based splitting)
    body = str(body)
    parts = body.split(boundary)

    for part in parts:
        if not part or part == '--\r\n' or part == '--':
            continue
        
        if '\n\n' in part:
            headers, content = part.split('\n\n')
        
            # Process content-disposition headers
            content_disposition = re.search(r'Content-Disposition: form-data; name="([^"]+)"(?:; filename="([^"]+)")?', headers)

            if content_disposition:
                name = content_disposition.group(1)
                filename = content_disposition.group(2)
                
                if filename:
                    # It's a file
                    file_content = content.rstrip('\n\n')
                    form_data[name] = {'filename': filename, 'content': file_content}
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
        print("An exception occurred:", e)



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
# def recursive_decode(s: str) -> str:
#     rec_count = 0
#     while '%' in s:
#         s = urllib.parse.unquote(s)
#         rec_count += 1
#         if rec_count == 5:
#             break
    
#     return s
def is_base64_encoded(data):
    try:
        # Attempt to decode and re-encode
        return base64.b64encode(base64.b64decode(data)).decode('utf-8') == data
    except Exception:
        return False
# Recursive decoder function
def recursive_decode(data):
    # While data can be decoded, continue decoding
    while True:
        # Check for Base64 encoding and decode if possible
        if is_base64_encoded(data):
            try:
                data = base64.b64decode(data).decode('utf-8')
                print("Decoded Base64:", data)
                continue
            except Exception:
                break
        # URL decoding with a try block
        try:
            decoded_url = urllib.parse.unquote(data)
            if decoded_url != data:  # Only update if decoding changes the string
                data = decoded_url
                print("Decoded URL:", data)
                continue
        except Exception as e:
            print(f"URL decoding error: {e}")
            break
        # Break if no further decoding possible
        break
    return data


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

def read_katana_json_output(path_to_output):
    reqs_and_resps_of_single_phase = list()
    with open(path_to_output, "r") as file_output:
        for line in file_output:
            try:
                reqs_and_resps_of_single_phase.append(json.loads(line.strip()))
            except:
                pass

    return reqs_and_resps_of_single_phase

def permutate_and_send_request(req):
    global payloads
    global args
    global signatures_and_their_data_lock
    global counter
    global requests_len
    global reqs

    # log_file = open("fuzz.log", "a")
    # log_file.write("\n")
    # log_file.write("\n")
    # log_file.write("Finished " + str(counter.value) + "/" + str(requests_len) + f" : {str(req)}\n")
    # log_file.write("\n")
    # log_file.write("\n")
    # log_file.close()
    
    # print(req)

    # log_file = open("logfile.log", "a")
    # log_file.write(str(counter.value) + " start 1 \n")
    # log_file.close()

    # if args.rate_limit == None:
    # with proxy_setting_lock:
    #     while True:
    #         try:
    #             # proxy = ""
    #             if args.rate_limit == None:
    #                 proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
    #             else:
    #                 for l_proxy in proxies:
    #                     l_proxy_count = used_proxies_across_processes.count(l_proxy)

    #                     # log_file = open("logfile.log", "a")
    #                     # log_file.write(f" {l_proxy} {l_proxy_count} \n")
    #                     # log_file.close()
    #                     if l_proxy_count < args.rate_limit:
    #                         # log_file = open("logfile.log", "a")
    #                         # log_file.write(f" assigned proxy \n")
    #                         # log_file.close()
    #                         proxy = l_proxy
                
    #             if proxy:
    #                 used_proxies_across_processes.append(proxy)
    #             else:
    #                  raise ValueError("proxy is empty")
    #             break
    #         except ValueError as e:
    #             log_file = open("fuzz.log", "a")
    #             log_file.write(f" Error: {e} from {','.join(proxies)}\n")
    #             log_file.close()
    #             time.sleep(2)
    
    # log_file = open("logfile.log", "a")
    # log_file.write(str(counter.value) + " end 1\n")
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
                        permd_dict_or_list = copy.copy(dict_or_list)
                        permd_dict_or_list[key] = variation
                        #run_feroxbuster(permd_dict_or_list, "body", key, payloads.index(payload))
                        # variations.append(permd_dict_or_list)
                        yield permd_dict_or_list
                
                for payload in payloads:
                    # Replace with payload directly
                    permd_dict_or_list = copy.copy(dict_or_list)
                    permd_dict_or_list[key] = str(permd_dict_or_list[key]).replace(str(value), payload)
                    #run_feroxbuster(permd_dict_or_list, "body", key, payloads.index(payload))
                    # variations.append(permd_dict_or_list)
                    yield permd_dict_or_list
    
                    # Replace with original value + payload
                    permd_dict_or_list = copy.copy(dict_or_list)
                    permd_dict_or_list[key] = str(permd_dict_or_list[key]).replace(str(value), str(value) + payload)
                    #run_feroxbuster(permd_dict_or_list, "body", key, payloads.index(payload))
                    # variations.append(permd_dict_or_list)
                    yield permd_dict_or_list
    
                # Replace with modified last three characters if value is integer or string
                permd_dict_or_list = copy.copy(dict_or_list)
                if type(permd_dict_or_list[key]) is int:
                    permd_dict_or_list[key] = int(str(permd_dict_or_list[key]).replace(str(value), modify_to_unexisting_id(str(value))))
                else:
                    permd_dict_or_list[key] = str(permd_dict_or_list[key]).replace(str(value), modify_to_unexisting_id(str(value)))
                #run_feroxbuster(permd_dict_or_list, "body", key, payloads.index(payload))
                # variations.append(permd_dict_or_list)
                yield permd_dict_or_list

        elif type(dict_or_list) is list:
            if len(dict_or_list) == 0:
                dict_or_list.append(999999999999999999999999999999999999999)
            
            for key in range(0, len(dict_or_list)):
                value = dict_or_list[key]
                if type(value) is dict or type(value) is list:
                    # Replace with payload directly
                    for variation in generate_payload_variations(value):
                        permd_dict_or_list = copy.copy(dict_or_list)
                        permd_dict_or_list[key] = variation
                        #run_feroxbuster(permd_dict_or_list, "body", key, payloads.index(payload))
                        # variations.append(permd_dict_or_list)
                        yield permd_dict_or_list
                
                for payload in payloads:
                    # Replace with payload directly
                    permd_dict_or_list = copy.copy(dict_or_list)
                    permd_dict_or_list[key] = str(permd_dict_or_list[key]).replace(str(value), payload)
                    #run_feroxbuster(permd_dict_or_list, "body", key, payloads.index(payload))
                    # variations.append(permd_dict_or_list)
                    yield permd_dict_or_list
    
                    # Replace with original value + payload
                    permd_dict_or_list = copy.copy(dict_or_list)
                    permd_dict_or_list[key] = str(permd_dict_or_list[key]).replace(str(value), str(value) + payload)
                    #run_feroxbuster(permd_dict_or_list, "body", key, payloads.index(payload))
                    # variations.append(permd_dict_or_list)
                    yield permd_dict_or_list
    
                # Replace with modified last three characters if value is integer or string
                permd_dict_or_list = copy.copy(dict_or_list)
                if type(permd_dict_or_list[key]) is int:
                    permd_dict_or_list[key] = int(str(permd_dict_or_list[key]).replace(str(value), modify_to_unexisting_id(str(value))))
                else:
                    permd_dict_or_list[key] = str(permd_dict_or_list[key]).replace(str(value), modify_to_unexisting_id(str(value)))
                #run_feroxbuster(permd_dict_or_list, "body", key, payloads.index(payload))
                # variations.append(permd_dict_or_list)
                yield permd_dict_or_list

        # return variations

    def list_different_values(obj1, obj2, parent_key=""):
        differing_keys = []

        # If both are dictionaries
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            common_keys = obj1.keys() & obj2.keys()  # Get the common keys

            for key in common_keys:
                full_key = f"{parent_key}{key}" if not parent_key else f"{parent_key}.{key}"

                if isinstance(obj1[key], dict) and isinstance(obj2[key], dict):
                    # Recursive call for nested dictionaries
                    differing_keys += list_different_values(obj1[key], obj2[key], full_key)
                elif isinstance(obj1[key], list) and isinstance(obj2[key], list):
                    # Handle lists
                    differing_keys += list_different_in_lists(obj1[key], obj2[key], full_key)
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
                differing_keys += list_different_values(list1[i], list2[i], full_key)
            elif list1[i] != list2[i]:
                differing_keys.append(full_key)
    
        # Check if one list is longer
        if len(list1) > min_len:
            for i in range(min_len, len(list1)):
                differing_keys.append(f"{parent_key}.{i}" if parent_key else f"{i}")
        elif len(list2) > min_len:
            for i in range(min_len, len(list2)):
                differing_keys.append(f"{parent_key}.{i}" if parent_key else f"{i}")
    
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

    # def recursive_decode(s: str) -> str:
    #     rec_count = 0
    #     while '%' in s:
    #         s = urllib.parse.unquote(s)
    #         rec_count += 1
    #         if rec_count == 5:
    #             break
        
    #     return s

    def is_base64_encoded(data):
        try:
            # Attempt to decode and re-encode
            return base64.b64encode(base64.b64decode(data)).decode('utf-8') == data
        except Exception:
            return False

    # Recursive decoder function
    def recursive_decode(data):
        # While data can be decoded, continue decoding
        while True:
            # Check for Base64 encoding and decode if possible
            if is_base64_encoded(data):
                try:
                    data = base64.b64decode(data).decode('utf-8')
                    print("Decoded Base64:", data)
                    continue
                except Exception:
                    break

            # URL decoding with a try block
            try:
                decoded_url = urllib.parse.unquote(data)
                if decoded_url != data:  # Only update if decoding changes the string
                    data = decoded_url
                    print("Decoded URL:", data)
                    continue
            except Exception as e:
                print(f"URL decoding error: {e}")
                break

            # Break if no further decoding possible
            break

        return data

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
    
    def found_match(found_in):
        with signatures_and_their_data_lock:
            with open(f"./chars_in_values_finder_output.txt", "a") as signatures_and_their_data:
                if "url" not in req.keys():
                    signatures_and_their_data.write(f'{req_signature} is {req["headers"]["Host"]["value"]}_{req["method"]}_{path_for_signature}_{clean_filename(req["path"])}_{"_".join(get_all_keys(req))}' + f" found in {found_in} "  + "\n"  + "\n"  + "\n")
                else:
                    signatures_and_their_data.write(req["url"] + "\n")
            

    path_for_signature = ""
    unidentified_subpath = 0
    for subpath in req["path"].split("/"):
        if search_string_in_directory("/usr/share/seclists/Discovery/Web-Content/raft-large", subpath) and not subpath.isdigit():
            path_for_signature += subpath + "/"
        else:
            unidentified_subpath += 1
    
    req_unhashed_signature = f'{req["headers"]["Host"]["value"]}_{req["method"]}_{path_for_signature}_{unidentified_subpath}_{"_".join(get_all_keys(req))}'
    req_signature = generate_md5(req_unhashed_signature)
    
    # subpaths = req["path"].split("/")
    # for subpath in subpaths:
    #     if not search_string_in_directory("/usr/share/seclists/Discovery/Web-Content/raft-large", subpath) or subpath.isdigit():
    #         for payload in payloads:
    #             preserved_payload = payload
    #             permd_req = copy.deepcopy(req)
    #             permd_req["path"] = permd_req["path"].replace(subpath, payload)
    #             run_feroxbuster(permd_req,"path",f"{subpaths.index(subpath) + 1}_subpath",payloads.index(preserved_payload))
    #             permd_req = copy.deepcopy(req)
    #             permd_req["path"] = permd_req["path"].replace(subpath, subpath + payload)
    #             run_feroxbuster(permd_req,"path",f"{subpaths.index(subpath) + 1}_subpath",payloads.index(preserved_payload))
    #         permd_req = copy.deepcopy(req)
    #         permd_req["path"] = permd_req["path"].replace(subpath, modify_to_unexisting_id(subpath))
    #         run_feroxbuster(permd_req,"path",f"{subpaths.index(subpath) + 1}_subpath", 0, True)
    if "path" not in args.exclude:
        path = recursive_decode(req["path"])
        already_found_match = False
        if args.in_value and any(payload in path for payload in args.in_value):
            found_match(path)
            already_found_match = True
        
        if args.match_value and any(payload == path for payload in args.match_value) and already_found_match == False:
            found_match(path)

    # fuzzing queries
    if "q_params" not in args.exclude:
        if req["queries"]:
            for key,value in req["queries"].items():
                value = recursive_decode(str(value))
                already_found_match = False
                if args.in_value and any(payload in value for payload in args.in_value):
                    found_match(value)
                    already_found_match = True
        
                if args.match_value and any(payload == value for payload in args.match_value) and already_found_match == False:
                    found_match(value)

            # for payload in payloads:
            #     preserved_payload = payload
            #     permd_req = copy.deepcopy(req)
            #     permd_req["queries"][key] = permd_req["queries"][key].replace(value, payload)
            #     run_feroxbuster(permd_req,"queries",key,payloads.index(preserved_payload))
            #     permd_req = copy.deepcopy(req)
            #     permd_req["queries"][key] = permd_req["queries"][key].replace(value, value + payload)
            #     run_feroxbuster(permd_req,"queries",key,payloads.index(preserved_payload))
            # permd_req = copy.deepcopy(req)
            # permd_req["queries"][key] = permd_req["queries"][key].replace(value, modify_to_unexisting_id(value))
            # run_feroxbuster(permd_req,"queries",key, 0, True)

            # json_obj, escaped_or_unescaped = process_and_load_json(value)
            # if json_obj != None:
            #     for index, variation in enumerate(generate_payload_variations(json_obj)):
                    # key_for_output = "_".join(list_different_values(json_obj, variation))
                    # if escaped_or_unescaped == 0:
                    #     json_string = json.dumps(variation)
                    # elif escaped_or_unescaped == 1:
                    #     json_string = escape_json(variation)
                    # elif escaped_or_unescaped == 2:
                    #     json_string = encode_json_with_url_encoding(variation)
                    # permd_req = copy.deepcopy(req)
                    # permd_req["queries"][key] = json_string
                    # idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
                    # if idx_of_payload != 0:
                    #     run_feroxbuster(permd_req,"queries",key_for_output,(idx_of_payload - 1) % len(payloads))
                    # else:
                    #     run_feroxbuster(permd_req,"queries",key_for_output, 0, True)
    
    # fuzzing headers
    if "headers" not in args.exclude:
        if req["headers"]:
            for key,value in req["headers"].items():
                value = recursive_decode(str(value))
                already_found_match = False
                if args.in_value and any(payload in value for payload in args.in_value):
                    found_match(value)
                    already_found_match = True

                if args.match_value and any(payload == value for payload in args.match_value) and already_found_match == False:
                    found_match(value)
            
            # if key in common_http_headers:
            #     continue
            # for payload in payloads:
            #     permd_req = copy.deepcopy(req)
            #     permd_req["headers"][key]["value"] = permd_req["headers"][key]["value"].replace(permd_req["headers"][key]["value"], payload)
            #     run_feroxbuster(permd_req,"headers",key,payloads.index(payload))
            #     permd_req = copy.deepcopy(req)
            #     permd_req["headers"][key]["value"] = permd_req["headers"][key]["value"].replace(permd_req["headers"][key]["value"], permd_req["headers"][key]["value"] + payload)
            #     run_feroxbuster(permd_req,"headers",key,payloads.index(payload))
            # permd_req = copy.deepcopy(req)
            # permd_req["headers"][key]["value"] = permd_req["headers"][key]["value"].replace(permd_req["headers"][key]["value"], modify_to_unexisting_id(permd_req["headers"][key]["value"]))
            # run_feroxbuster(permd_req,"headers",key, 0, True)
            # json_obj, escaped_or_unescaped = process_and_load_json(permd_req["headers"][key]["value"])
            # if json_obj != None:
                
            #     for index, variation in enumerate(generate_payload_variations(json_obj)):
            #         key_for_output = "_".join(list_different_values(json_obj, variation))
            #         if escaped_or_unescaped == 0:
            #             json_string = json.dumps(variation)
            #         elif escaped_or_unescaped == 1:
            #             json_string = escape_json(variation)
            #         elif escaped_or_unescaped == 2:
            #             json_string = encode_json_with_url_encoding(variation)
            #         permd_req = copy.deepcopy(req)
            #         permd_req["headers"][key]["value"] = json_string
            #         idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
            #         if idx_of_payload != 0:
            #             run_feroxbuster(permd_req,"headers",key_for_output,(idx_of_payload - 1) % len(payloads))
            #         else:
            #             run_feroxbuster(permd_req,"headers",key_for_output, 0, True)
            # for p_key,p_value in req["headers"][key]["params"].items():
            #     for payload in payloads:
            #         permd_req = copy.deepcopy(req)
            #         permd_req["headers"][key]["params"][p_key] = permd_req["headers"][key]["params"][p_key].replace(p_value, payload)
            #         run_feroxbuster(permd_req,"headers",f"{key}_{p_key}",payloads.index(payload))
            #         permd_req = copy.deepcopy(req)
            #         permd_req["headers"][key]["params"][p_key] = permd_req["headers"][key]["params"][p_key].replace(p_value, p_value + payload)
            #         run_feroxbuster(permd_req,"headers",f"{key}_{p_key}",payloads.index(payload))
            #     permd_req = copy.deepcopy(req)
            #     permd_req["headers"][key]["params"][p_key] = permd_req["headers"][key]["params"][p_key].replace(p_value, modify_to_unexisting_id(p_value))
            #     run_feroxbuster(permd_req,"headers",f"{key}_{p_key}", 0, True)
            #     json_obj, escaped_or_unescaped = process_and_load_json(p_value)
            #     if json_obj != None:
                    
            #         for index, variation in enumerate(generate_payload_variations(json_obj)):
            #             key_for_output = "_".join(list_different_values(json_obj, variation))
            #             if escaped_or_unescaped == 0:
            #                 json_string = json.dumps(variation)
            #             elif escaped_or_unescaped == 1:
            #                 json_string = escape_json(variation)
            #             elif escaped_or_unescaped == 2:
            #                 json_string = encode_json_with_url_encoding(variation)
            #             permd_req = copy.deepcopy(req)
            #             permd_req["headers"][key]["params"][p_key] = json_string
            #             idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
            #             if idx_of_payload != 0:
            #                 run_feroxbuster(permd_req,"headers",key_for_output,(idx_of_payload - 1) % len(payloads))
            #             else:
            #                 run_feroxbuster(permd_req,"headers",key_for_output, 0, True)
    # fuzzing body
    if "body" not in args.exclude:
        if req["body"]:
            value = recursive_decode(str(req["body"]))
            already_found_match = False
            if args.in_value and any(payload in value for payload in args.in_value):
                found_match(value)
                already_found_match = True
            
            if args.match_value and any(payload == value for payload in args.match_value) and already_found_match == False:
                found_match(value)
        
        # for index, variation in enumerate(generate_payload_variations(req["body"])):
        #     permd_req = copy.deepcopy(req)
        #     permd_req["body"] = variation
        #     key = "_".join(list_different_values(req["body"], permd_req["body"]))
        #     idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
        #     if idx_of_payload != 0:
        #         run_feroxbuster(permd_req,"body",key,(idx_of_payload - 1) % len(payloads))
        #     else:
        #         run_feroxbuster(permd_req,"body",key, 0, True)
        # for key,value in req["body"].items():
        #     json_obj, escaped_or_unescaped = process_and_load_json(value)
        #     if json_obj != None:
                
        #         for index, variation in enumerate(generate_payload_variations(json_obj)):
        #             key_for_output = "_".join(list_different_values(json_obj, variation))
        #             if escaped_or_unescaped == 0:
        #                json_string = json.dumps(variation)
        #             elif escaped_or_unescaped == 1:
        #                 json_string = escape_json(variation)
        #             elif escaped_or_unescaped == 2:
        #                 json_string = encode_json_with_url_encoding(variation)
        #             permd_req = copy.deepcopy(req)
        #             permd_req["body"][key] = json_string
                    
        #             idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
        #             if idx_of_payload != 0:
        #                 run_feroxbuster(permd_req,"body",key_for_output,(idx_of_payload - 1) % len(payloads))
        #             else:
        #                 run_feroxbuster(permd_req,"body",key_for_output, 0, True)
    
    log_file = open("chars_in_values_finder.log", "a")
    log_file.write("Finished " + str(counter.value) + "/" + str(requests_len) + "\n")
    log_file.close()
    
    with counter.get_lock():
        counter.value += 1


parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument("-iv", "--in-value", required=False, help="the string(s) to look for in values of requests. when supplying strings, separate them by ','")
parser.add_argument("-mv", "--match-value", required=False, help="the string(s) to look for in values of requests. when supplying strings, separate them by ','")
parser.add_argument("-e", "--exclude", required=False, help="where to not look for the string, you can choose multipile ones separated by ','. available exclusions: path, q_params, headers, body")
parser.add_argument("-uf", "--urls-file", required=False, help="urls file to add in the search")
parser.add_argument("-kd", "--katana-directory", required=False, help="a directory that has the outputs of katana to parse as requests")
parser.add_argument("-kmhv", "--katana-match-host-value", required=False, help="test requests that are parsed from katana's output with matching host to this value")
parser.add_argument("-kihv", "--katana-in-host-value", required=False, help="test requests that are parsed from katana's output with host that contain this value")
args = parser.parse_args()


manager = multiprocessing.Manager()
counter = multiprocessing.Value('i',1)
signatures_and_their_data_lock = multiprocessing.Lock()

if args.match_value == None and args.in_value == None:
    print("both --match-value and --in-value can't be empty")
    exit(1)

if args.in_value:
    args.in_value = args.in_value.split(",")
if args.match_value:
    args.match_value = args.match_value.split(",")

unpack_burp_output = list()
if os.path.isdir('./input'):
    for burp_file in os.listdir('./input'):
        if os.path.exists("/home/deus/downloads"):
            subprocess.run(f"php /home/deus/downloads/unpack-burp/unpack-burp.php ./input/{burp_file} jsonreq > unpack_burp_output.txt", shell=True)
        else:
            subprocess.run(f"php /home/kali/Downloads/unpack-burp/unpack-burp.php ./input/{burp_file} jsonreq > unpack_burp_output.txt", shell=True)


        with open('unpack_burp_output.txt', 'r') as file:
            unpack_burp_output.extend(file.read().split("\n\n"))

reqs = list()
all_queries_keys = list()
unique_reqs_check = dict()

if args.urls_file:
    with open(args.urls_file, 'r', encoding='utf-8') as urls:
        for url in urls:
            url = url.strip()
            queries = extract_query_parameters(url)

            queries_keys = get_all_keys(queries)
            queries_keys.sort()

            hostname = urlparse(url).hostname
            if hostname not in unique_reqs_check.keys():
                unique_reqs_check[hostname] = list()
            
            if len(queries_keys) == 0 or f"GET_{'_'.join(queries_keys)}" in unique_reqs_check[hostname]:
                continue
            
            unique_reqs_check[hostname].append(f"GET_{'_'.join(queries_keys)}")

            path = extract_path(url)
            
            headers = dict()
            headers["Host"] = {'value': hostname, 'params': {}}
            headers['User-Agent'] = {'value': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'params': {}}
            # if args.header != None and args.header[0] not in list(headers.keys()):
            #     headers[args.header[0]] = {'value': args.header[1], 'params': {}}
            
            http_data = {
                'method': "GET",
                'path': path,
                'queries': queries,
                'headers': headers,
                'body': ""
            }

            reqs.append(http_data)

if args.katana_directory:
    paths_of_outputs = os.listdir(args.katana_directory)
    for path in paths_of_outputs:
        if os.path.isfile(args.katana_directory + '/' +path) == False:
            continue
        
        reqs_and_resps_of_single_phase = read_katana_json_output(args.katana_directory + '/' +path)
        for req_and_resp in reqs_and_resps_of_single_phase:


            if "request" in req_and_resp.keys() and "raw" in req_and_resp["request"].keys():
                unparsed_req = req_and_resp["request"]["raw"]
                parsed_request = parse_http(unparsed_req)

                if args.katana_match_host_value and args.katana_match_host_value != parsed_request["headers"]["Host"]["value"].strip():
                    continue

                if args.katana_in_host_value and args.katana_in_host_value not in parsed_request["headers"]["Host"]["value"].strip():
                    continue

                if parsed_request["headers"]["Host"]["value"] not in unique_reqs_check.keys():
                    unique_reqs_check[parsed_request["headers"]["Host"]["value"]] = list()

                if (len(list(parsed_request["queries"].keys())) > 0 and f"{parsed_request['method']}_{'_'.join(get_all_keys(parsed_request['queries']))}" not in unique_reqs_check[parsed_request["headers"]["Host"]["value"]]) or (type(parsed_request["body"]) is dict and len(list(parsed_request["body"].keys())) > 0 and f"{parsed_request['method']}_{'_'.join(get_all_keys(parsed_request['body']))}" not in unique_reqs_check[parsed_request["headers"]["Host"]["value"]]):
                    reqs.append(parsed_request)
                    if len(list(parsed_request["queries"].keys())) > 0:
                        unique_reqs_check[parsed_request["headers"]["Host"]["value"]].append(f"{parsed_request['method']}_{'_'.join(get_all_keys(parsed_request['queries']))}")

                    if type(parsed_request["body"]) is dict and len(list(parsed_request["body"].keys())) > 0:
                        unique_reqs_check[parsed_request["headers"]["Host"]["value"]].append(f"{parsed_request['method']}_{'_'.join(get_all_keys(parsed_request['body']))}")

            # if "response" in req_and_resp.keys() and "forms" in req_and_resp["response"].keys():
            #     for form in req_and_resp["response"]["forms"]:
            #         url = form['action']
            #         action_hostname = urlparse(url).netloc
            #         if action_hostname not in unique_reqs_check.keys():
            #             unique_reqs_check[action_hostname] = list()

            #         try:
            #             if f"{form['method']}_{'_'.join(get_all_values(form['parameters']))}" not in unique_reqs_check[action_hostname]:

            #                 path = extract_path(url)
            #                 queries = extract_query_parameters(url)
            #                 body = dict()

            #                 hostname = urlparse(url).hostname

            #                 if args.katana_match_host_value and args.katana_match_host_value != hostname.strip():
            #                     continue

            #                 if args.katana_in_host_value and args.katana_in_host_value not in hostname.strip():
            #                     continue

            #                 headers = dict()
            #                 headers["Host"] = {'value': hostname, 'params': {}}
            #                 headers['User-Agent'] = {'value': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'params': {}}
            #                 if args.header != None and args.header[0] not in list(headers.keys()):
            #                     headers[args.header[0]] = {'value': args.header[1], 'params': {}}

            #                 if form['method'] == "GET":
            #                     for param in get_all_values(form['parameters']):
            #                         if param.strip():
            #                             queries[param] = "inp"
            #                 else:
            #                     headers['Content-Type'] = {'value': form['enctype'], 'params': {}}

            #                     for param in get_all_values(form['parameters']):
            #                         # body = dict()
            #                         if param.strip():
            #                             body[param] = "inp"

            #                 if len(list(body.keys())) == 0:
            #                     body = ""

            #                 http_data = {
            #                     'method': form['method'],
            #                     'path': path,
            #                     'queries': queries,
            #                     'headers': headers,
            #                     'body': body
            #                 }

            #                 reqs.append(http_data)

            #                 unique_reqs_check[action_hostname].append(f"{form['method']}_{'_'.join(get_all_values(form['parameters']))}")
            #         except:
            #             print("error parsing:")
            #             print(form)
            #             # exit()


for request_and_response in unpack_burp_output:
    if request_and_response == '':
        continue
    
    request_and_response = json.loads(request_and_response)
    
    req_text = request_and_response["reqp"].replace("HTTP/2","HTTP/1.1") + "\r\n" + request_and_response["reqh"] + "\r\n\r\n" + request_and_response["reqb"]
    
    parsed_request = parse_http(req_text)
    if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
        reqs.append(parsed_request)
    else:
        print(req_text)
        # exit()

requests_len = len(reqs)

with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
    pool.map(permutate_and_send_request, reqs, chunksize=1)
