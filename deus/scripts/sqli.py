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
from urllib.parse import urlparse, parse_qs, parse_qsl, quote, unquote, urlencode
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
import fcntl
import base64
from collections import Counter
from ipwhois import IPWhois
from ipwhois.exceptions import IPDefinedError
import socket
import random
import string
from typing import Union, Any
import shlex
import signal

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
        if queries == {'': ''}:
            queries = dict()

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
        if args.header != None and args.header[0] not in list(headers.keys()):
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
        print("An exception occurred:", e)

def get_all_values(d):
    values = []
    
    def extract_values(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                extract_values(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_values(item)
        else:
            values.append(obj)
    
    extract_values(d)
    return values

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


def random_pair():
    key = ''.join(random.choices(string.ascii_lowercase, k=5))
    # val = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    val = ''.join(random.choices(string.ascii_letters + string.digits, k=8 * 1024))
    return key, val

def add_random_around(obj: Union[dict, list], key_to_add_around: str = None) -> Union[dict, list]:
    """
    For a dict: insert a random key/value before and after key 'mykey'.
    For a list: insert random strings before and after the element at key_to_add_around.
    """
    if isinstance(obj, dict):
        before_k, before_v = random_pair()
        after_k,  after_v  = random_pair()
        new_d = {}
        for k, v in obj.items():
            if k == key_to_add_around:
                new_d[before_k] = before_v
                new_d[k] = v
                new_d[after_k] = after_v
            else:
                new_d[k] = v
        return new_d

    elif isinstance(obj, list):
        # if key_to_add_around is None:
        #     raise ValueError("For lists you must provide key_to_add_around")
        before_v = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        # after_v  = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        after_v = ''.join(random.choices(string.ascii_letters + string.digits, k=8 * 1024))
        # slice and concatenate to keep order
        return obj[:key_to_add_around] + [before_v, obj[key_to_add_around], after_v] + obj[key_to_add_around+1:]

    # else:
    #     raise TypeError("obj must be dict or list")



def group_reqs_by_hostname(reqs):
    grouped = defaultdict(list)
    for req in reqs:
        hostname = req['headers']['Host']['value']

        if hostname:
            grouped[hostname].append(req)
    return grouped



def is_port_available(port, host='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


user_agents = set()


base_path = '/home/deus/documents'
for f_or_d in os.listdir(base_path):
    if "user_agent" in f_or_d:
        user_agents.add(os.path.join(base_path, f_or_d))

def get_url_rate_config(url):
    if not args.rate_config:
        return
    
    url_hostname = urlparse(url).hostname
    with open(args.rate_config, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            if urlparse(data["url"]).hostname == url_hostname:
                return data

def get_proxy_port(hostname, rate_limit, used_user_agents):
    try:

        available_port = ""
        available_user_agent = ""

        print("Entered get_proxy_port")

        ports = list(range(8000, 15000))
        random.shuffle(ports)

        for port in ports:
            if is_port_available(port):
                available_port = port
                break

        rate_config = get_url_rate_config(f'http://{hostname}')
        if rate_config:
            mimick_users = rate_config["is_cookie_used"]

        # if args.mimic_user and mimick_users:
        if rate_config and mimick_users:

            domain_arg = f"--domain {hostname}"


            if rate_limit < 190:
                rate_limit += 5

            if rate_config:
                user_count_arg = f"-u {min(rate_limit, rate_config['rate'] * 10)}"
            else:
                user_count_arg = f"-u {rate_limit}"



            for user_agent in user_agents:
                if user_agent not in used_user_agents:
                    used_user_agents.add(user_agent)

                    user_agent_arg = f"-g {user_agent}"

        else:
            domain_arg = ""
            user_count_arg = ""
            user_agent_arg = ""

        rota_proc = subprocess.Popen(
            ["rota", "--config", "/home/deus/documents/rota_config.yml",*shlex.split(domain_arg),*shlex.split(user_count_arg),*shlex.split(user_agent_arg), "-p", f"{available_port}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )

        if user_count_arg:
            user_count_arg_time = (int(user_count_arg.split(" ")[1]) / 10) * 5

            time_slept = 0

        while is_port_available(available_port):
            time.sleep(5)
            
            if user_count_arg:
                time_slept += 5
                if user_count_arg_time + 60 < time_slept:
                    domain_arg = ""
                    user_count_arg = ""
                    user_agent_arg = ""

                    rota_exit_handler(rota_proc)

                    rota_proc = subprocess.Popen(
                        ["rota", "--config", "/home/deus/documents/rota_config.yml",*shlex.split(domain_arg),*shlex.split(user_count_arg),*shlex.split(user_agent_arg), "-p", f"{available_port}"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        preexec_fn=os.setsid
                    )

                    while is_port_available(available_port):
                        time.sleep(5)

                    break


        print("Leaving get_proxy_port")

        return available_port, rota_proc
    except Exception as e:
        print("Error:", e)

def rota_exit_handler(rota_proc):
    os.killpg(os.getpgid(rota_proc.pid), signal.SIGKILL)

    try:
        rota_proc.wait(timeout=5)
    except Exception:
        pass

# def response_has_cookies(domain: str) -> bool:
#     try:
#         # Step 1: DNS Lookup
#         ip = socket.gethostbyname(domain)
        
#         # Step 2: WHOIS Lookup
#         obj = IPWhois(ip)
#         whois_info = obj.lookup_rdap()

#         # Step 3: Check for Cloudflare in WHOIS data
#         org = whois_info.get('network', {}).get('name', '') or whois_info.get('network', {}).get('remarks', '')
#         description = whois_info.get('network', {}).get('description', '')
#         entities = whois_info.get('network', {}).get('entities', [])
#         org_str = f"{org} {description} {entities}".lower()

#         return "cloudflare" in org_str

#     except socket.gaierror:
#         print(f"[!] DNS lookup failed for domain: {domain}")
#     except IPDefinedError:
#         print(f"[!] The IP address {ip} is reserved (e.g. private, loopback).")
#     except Exception as e:
#         print(f"[!] Error: {e}")
    
#     return False

def response_has_cookies(url: str, retries: int = 0) -> bool:
    try:
        proxies = {
            "http": "http://isp.decodo.com:10000",
            "https": "https://isp.decodo.com:10000"
        }
    
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }

        response = requests.get(f'http://{url}', proxies=proxies, headers=headers, timeout=30)
        return bool(response.cookies)
    except requests.RequestException as e:
        print(f"Request failed (attempt {retries + 1}): {e}")
        if retries < 2:
            return response_has_cookies(url, retries + 1)
        return False



def permutate_and_send_request(req):
    global victim_params
    global payloads
    global args
    global used_proxies_across_processes
    global proxies
    global req_lock
    global signatures_and_their_data_lock
    global requests_with_special_needs_lock
    global proxy_setting_lock
    global common_http_headers
    global counter
    global req_number
    global requests_len
    # global reqs

    with proxy_setting_lock:
        counter1 = Counter(proxies)
        counter2 = Counter(used_proxies_across_processes)
        result_counter = counter1 - counter2
        result = list(result_counter.elements())
        proxy = result[0]

        used_proxies_across_processes.append(proxy)
    
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
                        
                        yield permd_dict_or_list
                
                for payload in payloads:
                    
                    permd_dict_or_list = copy.copy(dict_or_list)
                    permd_dict_or_list[key] = str(permd_dict_or_list[key]).replace(str(value), str(value) + payload)
                    permd_dict_or_list = add_random_around(permd_dict_or_list, key)
                    
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
                        
                        yield permd_dict_or_list
                
                for payload in payloads:
    
                    # Replace with original value + payload
                    permd_dict_or_list = copy.copy(dict_or_list)
                    permd_dict_or_list[key] = str(permd_dict_or_list[key]).replace(str(value), str(value) + payload)
                    permd_dict_or_list = add_random_around(permd_dict_or_list, key)
                    
                    yield permd_dict_or_list
                    

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
                    

    def run_feroxbuster(perm_req, output_folder_name='normal', injection_point='', idx_of_payload=0, last3c=False):
        
        url = f"https://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"
        
        # log_file = open("logfile.log", "a")
        # log_file.write(str(counter.value) + " start 2\n")
        # log_file.close()

        if args.delay != None and idx_of_payload % args.payloads_number == 0:
            time.sleep(args.delay)
        
        # log_file = open("logfile.log", "a")
        # log_file.write(str(counter.value) + " end 2\n")
        # log_file.close()

        with req_lock:
            if args.request_file != None:
                # if args.payloads_number != None and args.token_expiration == None and args.token_script != None and idx_of_payload % args.payloads_number == 0:
                #     subprocess.run(f"python3 {args.token_script}", shell=True)
                
                # log_file = open("logfile.log", "a")
                # log_file.write(str(counter.value) + " start 5\n")
                # log_file.close()

                headers = extract_headers(args.request_file)
                queries = extract_query_parameters(args.request_file)

                # log_file = open("logfile.log", "a")
                # log_file.write(str(counter.value) + " mid 5\n")
                # log_file.close()
        
                update_dict_with_matches(perm_req["queries"], queries)
                update_dict_with_matches(perm_req["headers"], headers)

                # log_file = open("logfile.log", "a")
                # log_file.write(str(counter.value) + " end 5\n")
                # log_file.close()
        
        # log_file = open("logfile.log", "a")
        # log_file.write(str(counter.value) + " start 3\n")
        # log_file.close()

        if args.delay != None and args.token_script != None and idx_of_payload % args.payloads_number == 0 and args.token_expiration == None:
            time.sleep(args.delay)

        # log_file = open("logfile.log", "a")
        # log_file.write(str(counter.value) + " end 3\n")
        # log_file.close()

        # Add queries

        queries = None
        if perm_req["queries"]:
            queries = dict()
            for key, value in perm_req.get('queries', {}).items():
                # cmd.append("-Q")
                # cmd.append(f"{key}={value}")
                queries[key] = value.strip()
        
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
                if 'params' in header_info.keys():
                    for key,value in header_info['params'].items():
                        key_count += 1
                        if key_count != len(header_info['params'].keys()):
                            header_value += f"{key}={value};"
                        else:
                            header_value += f"{key}={value}"
    
                # cmd.append("-H")
                # cmd.append(f"{header_name}:{header_value}")
                headers[header_name] = header_value.strip()
    
            headers = sanitize_headers(headers)

        def build_multipart_form_data(form_data, content_type):
            """Builds a multipart/form-data body from a Python dictionary."""
            
            boundary = content_type.split("boundary=")[1]
            
            body = BytesIO()
            
            for name, value in form_data.items():
                if isinstance(value, dict) and 'filename' in value:
                    # This is a file
                    filename = value['filename']
                    content = value['content']
                    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                    
                    body.write(f'{boundary}\r\n'.encode())
                    body.write(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode())
                    body.write(f'Content-Type: {content_type}\r\n\r\n'.encode())
                    body.write(content.encode())
                    body.write(b'\r\n')
                else:
                    # This is a regular form field
                    body.write(f'{boundary}\r\n'.encode())
                    body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
                    body.write(f'{value}\r\n'.encode())
            
            # End boundary
            body.write(f'{boundary}--\r\n'.encode())
            
            return body.getvalue()
        
        # def save_response_content(response, output_filename):
        #     # Check the Content-Type to determine if it's binary
        #     content_type = response.headers.get('Content-Type', '').lower()

        #     # List of common binary content types
        #     binary_types = ['application/octet-stream', 'image/', 'audio/', 'video/']

        #     # Check if content type is binary
        #     if any(binary_type in content_type for binary_type in binary_types):
        #         # Write in binary mode
        #         print(f"Detected binary content ({content_type}), saving as binary.")
        #         with open(output_filename, 'wb') as binary_file:
        #             binary_file.write(response.content)
        #     else:
        #         # Write in text mode
        #         # print(f"Detected text content ({content_type}), saving as text.")
        #         with open(output_filename, 'a', encoding=response.encoding if response.encoding else 'utf-8') as text_file:
        #             text_file.write(response.text)
        
        

        def save_response_details(response, output_filename):

            # Detect if content is binary or text
            content_type = response.headers.get('Content-Type', 'unknown')
            binary_types = ['application/octet-stream', 'image/', 'audio/', 'video/']
            response_content = None

            try:
                # Check if content type is binary
                if any(binary_type in content_type for binary_type in binary_types):
                    # Write in binary mode
                    # print(f"Detected binary content ({content_type}), saving as binary.")
                    with open(output_filename + ".body", 'rb') as binary_file:
                        response_content = binary_file.read()
                else:
                    # Write in text mode
                    # print(f"Detected text content ({content_type}), saving as text.")
                    with open(output_filename + ".body", 'r', encoding=response.encoding if response.encoding else 'utf-8') as text_file:
                        response_content = text_file.read()
            except:
                pass

            # Default values for word count and line count
            word_count = None
            line_count = None
            content_length = None

            # If the content type indicates it's JSON, handle JSON specifically
            if response_content != None:
                if 'application/json' in content_type:
                    try:
                        json_data = response_content
                        # Flatten JSON and count keys and values as 'words'
                        word_count = len(json.dumps(json_data).split())  # Count keys and values as "words"
                        line_count = len(json.dumps(json_data, indent=2).splitlines())  # Pretty-print and count lines

                        content_length = response.headers.get('Content-Length', len(response_content.encode("utf-8")))
                        # word_count = len(json.dumps(json_data).split(" "))
                        # line_count = len(json.dumps(json_data).splitlines())
                    except json.JSONDecodeError:
                        word_count = 0
                        line_count = 0
                # If the content type indicates it's text-based, process as text
                elif 'text' in content_type:
                    # content = response_content
                    word_count = len(response_content.split(" "))
                    line_count = len(response_content.splitlines())

                    content_length = response.headers.get('Content-Length', len(response_content.encode("utf-8")))
                else:
                    # For binary content, don't count words or lines
                    # content = response_content
                    content_length = response.headers.get('Content-Length', len(response_content))
            
            # content_length = response.headers.get('Content-Length', None)

            # Get the HTTP status code
            status = response.status_code

            # Prepare the data for JSON output
            data = {
                "word_count": word_count,
                "line_count": line_count,
                "content_type": content_type,
                "content_length": content_length,
                "status": status
            }

            data = json.dumps(data)
            output_file = open(output_filename + '.json', 'w')
            fcntl.flock(output_file, fcntl.LOCK_EX)
            # with open(output_filename + '.json', 'a') as output_file:
            output_file.write(data)
            
            fcntl.flock(output_file, fcntl.LOCK_UN)
            output_file.close()


        # Add body if present
        body = None
        if perm_req.get('body'):
            content_type = str(perm_req["headers"]["Content-Type"])
            if "json" in content_type.lower():
                
                # with open(f"./body_{req_signature}.txt", "w") as body:
                #     body.write(json.dumps(perm_req['body']))
                body = json.dumps(perm_req['body'])

            elif "x-www-form-urlencoded" in content_type.lower():

                # with open(f"./body_{req_signature}.txt", "w") as body:
                #     body.write(urllib.parse.urlencode(perm_req['body']))
                body = safe_urlencode(perm_req['body'])
            
            elif "multipart/form-data" in content_type.lower():
                # multipart_body = build_multipart_form_data(perm_req['body'], content_type)
                # with open(f"./body_{req_signature}.txt", "w") as body:
                #     body.write(multipart_body.decode())
                body = build_multipart_form_data(perm_req['body'], content_type)
                    
            # cmd.extend(f"--data @body_{req_signature}.txt".split(" "))
        
        output_path = str()
        if output_folder_name == "normal" and args.normal_directory == None:
            output_path = f"./output/normal/{req_signature}"
        elif output_folder_name == "normal_checkup" and args.normal_directory == None:
            output_path = f"./output/normal/{req_signature}_checkup"
        elif output_folder_name == "normal" and args.normal_directory != None:
            output_path = f"{args.normal_directory}/{req_signature}"
        elif output_folder_name == "normal_checkup" and args.normal_directory != None:
            output_path = f"{args.normal_directory}/{req_signature}_checkup"
        else:
            if last3c == False:
                # cmd.extend(f"--json -o ./output/{output_folder_name}/{req_signature}_{clean_filename(injection_point)}_{idx_of_payload}.json".split(" "))
                output_path = f"./output/{output_folder_name}/{req_signature}_{clean_filename(injection_point)}_{idx_of_payload}"
            else:
                # cmd.extend(f"--json -o ./output/{output_folder_name}/{req_signature}_{clean_filename(injection_point)}_last3c.json".split(" "))
                output_path = f"./output/{output_folder_name}/{req_signature}_{clean_filename(injection_point)}_last3c"
        
        # construct HTTP request file
        # Parse URL
        parsed_url = urlparse(url)
        path = parsed_url.path or "/"
        query_string = parsed_url.query

        if queries:
            query_string = safe_urlencode(queries)

        # Build the request line
        request_line = f"{perm_req['method'].upper()} {path}"
        if query_string:
            request_line += f"?{query_string}"
        request_line += f" HTTP/1.1\n"

        # Build headers
        host_header = f"Host: {parsed_url.netloc}\n"
        headers_block = ""
        if headers:
            headers_block = "".join(f"{key}: {value}\n" for key, value in headers.items())
        
        body_block = ""
        if body:
            body_block = body

        # Combine all parts
        http_request = f"{request_line}{host_header}{headers_block}\n{body_block}"

        # Write to a file
        with open(req_signature, "w") as file:
            file.write(http_request)

        # log_file = open("logfile.log", "a")
        # log_file.write(f"\n")
        # log_file.write(f"\n")
        # log_file.write(f"{req_signature} is the suppose to contain {http_request}\n")
        # log_file.write(f"\n")
        # log_file.write(f"\n")
        # log_file.close()

        technique_for_sql = ""
        if args.technique:
            technique_for_sql = f"--technique={args.technique}"

        level_for_sql = ""
        if args.level:
            level_for_sql = f"--level {args.level}"
        
        delay_for_sql = ""
        if args.delay_sql:
            delay_for_sql = f"--delay {args.delay_sql}"

        proxy_for_sql = ""
        if proxy != "self":
            proxy_for_sql = f"--proxy http://{proxy}"
        
        subprocess.run(f"sqlmap -r {req_signature} --batch --ignore-stdin --ignore-code '*' --flush-session {level_for_sql} {proxy_for_sql} --time-sec 5 {technique_for_sql} {delay_for_sql} > {output_path}_sqlmap", shell=True, preexec_fn=os.setsid)
        # subprocess.run(f"ghauri -r {req_signature} --batch --level 3 {proxy_for_sql} --time-sec 5 {technique_for_sql} {delay_for_sql} > {output_path}_ghauri", shell=True)
        if os.path.exists(req_signature):
            os.remove(req_signature)

        # log_file = open("logfile.log", "a")
        # log_file.write(f"\n")
        # log_file.write(f"\n")
        # log_file.write(f"deleted {req_signature}\n")
        # log_file.write(f"\n")
        # log_file.write(f"\n")
        # log_file.close()

        # log_file = open("logfile.log", "a")
        # log_file.write(str(counter.value) + " end 4\n")
        # log_file.close()
    
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
    
    def get_nested_value(d, key_path):
        keys = key_path.split('.')
        retrieved = True
        value = copy.deepcopy(d)
        for key in keys:
            try:
                value = value[key]
            except:
                retrieved = False
        if retrieved:
            return value
        else:
            return ""

    req_unhashed_signature = f'{req["headers"]["Host"]["value"]}_{req["method"]}_{req["path"]}_{"_".join(get_all_keys(req))}'
    
    req_signature = ""
    with req_number.get_lock():
        req_number.value += 1
        req_signature = str(req_number.value) + str(generate_md5(req_unhashed_signature))
    
    with signatures_and_their_data_lock:
        with open(f"./signatures_and_their_data.txt", "a") as signatures_and_their_data:
            signatures_and_their_data.write(f'{req_signature} is {req_unhashed_signature}' + "\n")
    
    # log_file = open("logfile.log", "a")
    # log_file.write(str(counter.value) + " start of path\n")
    # log_file.close()

    def get_params_with_interested_value(params, interested_value):
        params_with_interested_value = list()
        if isinstance(params, dict):
            for k, v in params.items():
                if interested_value == v:
                    params_with_interested_value.append({k:v})
                if isinstance(v, dict) or isinstance(v, list):
                    payload = get_params_with_interested_value(v, interested_value)
                    if payload:
                        params_with_interested_value.extend(payload)
                else:
                    json_obj, escaped_or_unescaped = process_and_load_json(v)
                    if isinstance(json_obj, dict) or isinstance(json_obj, list):
                        payload = get_params_with_interested_value(json_obj, interested_value)
                        if payload:
                            params_with_interested_value.extend(payload)
        elif isinstance(params, list):
            for v in params:
                if isinstance(v, dict) or isinstance(v, list):
                    payload = get_params_with_interested_value(v, interested_value)
                    if payload:
                        params_with_interested_value.extend(payload)
                else:
                    json_obj, escaped_or_unescaped = process_and_load_json(v)
                    if isinstance(json_obj, dict) or isinstance(json_obj, list):
                        payload = get_params_with_interested_value(json_obj, interested_value)
                        if payload:
                            params_with_interested_value.extend(payload)
        return params_with_interested_value

    # fuzzing path
    
    if not args.waf:

        subpaths = req["path"].split("/")
        for subpath in subpaths:
            if not subpath or (not (sum(1 for ch in subpath if ch.isdigit()) > 2) and not (sum(1 for ch in subpath if ch.isupper()) > 5) ):
                continue

            # if not subpath or subpath.isalnum() and not subpath.isdigit() and subpath.lower() not in ("payloaddd", "expr"):
            for payload in payloads:
                preserved_payload = payload
                
                permd_req = copy.deepcopy(req)
                permd_req["path"] = permd_req["path"].replace(subpath, subpath + payload)
                run_feroxbuster(permd_req,"path",f"{subpaths.index(subpath) + 1}_subpath",payloads.index(preserved_payload))
    
        # log_file = open("logfile.log", "a")
        # log_file.write(str(counter.value) + " end of path and start of queries\n")
        # log_file.close()
    
        # fuzzing queries
    
        tried_queries_keys_1 = list()

        # print(req["queries"])
        # print(bool(req["queries"]))
                    
        if req["queries"]:
            # print("hereeeeeeee")
            for key,value in req["queries"].items():
                if key in tried_queries_keys_1:
                    continue
                
                tried_queries_keys_1.append(key)

                for payload in payloads:
                    
                    permd_req = copy.deepcopy(req)
                    permd_req["queries"][key] = value + payload
                    run_feroxbuster(permd_req,"queries",key,payloads.index(payload))
                    
                
                tried_queries_keys_2 = list()
                    
                json_obj, escaped_or_unescaped = process_and_load_json(value)
                if json_obj != None:
                    for index, variation in enumerate(generate_payload_variations(json_obj)):
                        key_for_output = ".".join(list_different_values(json_obj, variation))
                        last_key = key_for_output.split(".")[-1]

                        if last_key in tried_queries_keys_2:
                            continue

                        tried_queries_keys_2.append(last_key)
                            
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
                        idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
                        
                        run_feroxbuster(permd_req,"queries",key_for_output,(idx_of_payload - 1) % len(payloads))
                    
    
    # log_file = open("logfile.log", "a")
    # log_file.write(str(counter.value) + " end of queries and start of headers\n")
    # log_file.close()


    # fuzzing headers
    # temporarily not fuzzing other headers
    # keys_to_delete = [key for key in req["headers"] if key not in ["Host", "Cookie","Authorization"]]
    # for key in keys_to_delete:
    #     del req["headers"][key]
    # if args.header[0] in req["headers"].keys():
    #     del req["headers"][args.header[0]]
    


    # if req["headers"] and not args.exclude_headers:
    #     for key,value in req["headers"].items():
    #         # if key.lower() != "host":
    #             # continue
    #         if key.upper() in common_http_headers:
    #             continue
    #         for payload in payloads:
    #             # permd_req = copy.deepcopy(req)
    #             # permd_req["headers"][key]["value"] = permd_req["headers"][key]["value"].replace(permd_req["headers"][key]["value"], payload)
    #             # run_feroxbuster(permd_req,"headers",key,payloads.index(payload))
    #             permd_req = copy.deepcopy(req)
    #             permd_req["headers"][key]["value"] = permd_req["headers"][key]["value"].replace(permd_req["headers"][key]["value"], permd_req["headers"][key]["value"] + payload)
    #             run_feroxbuster(permd_req,"headers",key,payloads.index(payload))
    #         # permd_req = copy.deepcopy(req)
    #         # permd_req["headers"][key]["value"] = permd_req["headers"][key]["value"].replace(permd_req["headers"][key]["value"], modify_to_unexisting_id(permd_req["headers"][key]["value"]))
    #         # run_feroxbuster(permd_req,"headers",key, 0, True)
    #         json_obj, escaped_or_unescaped = process_and_load_json(permd_req["headers"][key]["value"])
    #         if json_obj != None:
    #             # variations = enumerate(generate_payload_variations(json_obj))
    #             for index, variation in enumerate(generate_payload_variations(json_obj)):
    #                 key_for_output = "_".join(list_different_values(json_obj, variation))
    #                 if escaped_or_unescaped == 0:
    #                     json_string = json.dumps(variation)
    #                 elif escaped_or_unescaped == 1:
    #                     json_string = escape_json(variation)
    #                 elif escaped_or_unescaped == 2:
    #                     json_string = encode_json_with_url_encoding(variation)
    #                 elif escaped_or_unescaped == 3:
    #                     json_string = encode_base64(variation)
    #                 permd_req = copy.deepcopy(req)
    #                 permd_req["headers"][key]["value"] = json_string
    #                 idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
    #                 # if idx_of_payload != 0:
    #                 run_feroxbuster(permd_req,"headers",key_for_output,(idx_of_payload - 1) % len(payloads))
    #                 # else:
    #                 #     run_feroxbuster(permd_req,"headers",key_for_output, 0, True)
    #         for p_key,p_value in req["headers"][key]["params"].items():
    #             for payload in payloads:
    #                 # permd_req = copy.deepcopy(req)
    #                 # permd_req["headers"][key]["params"][p_key] = permd_req["headers"][key]["params"][p_key].replace(p_value, payload)
    #                 # run_feroxbuster(permd_req,"headers",f"{key}_{p_key}",payloads.index(payload))
    #                 permd_req = copy.deepcopy(req)
    #                 permd_req["headers"][key]["params"][p_key] = permd_req["headers"][key]["params"][p_key].replace(p_value, p_value + payload)
    #                 run_feroxbuster(permd_req,"headers",f"{key}_{p_key}",payloads.index(payload))
    #             # permd_req = copy.deepcopy(req)
    #             # permd_req["headers"][key]["params"][p_key] = permd_req["headers"][key]["params"][p_key].replace(p_value, modify_to_unexisting_id(p_value))
    #             # run_feroxbuster(permd_req,"headers",f"{key}_{p_key}", 0, True)
    #             json_obj, escaped_or_unescaped = process_and_load_json(p_value)
    #             if json_obj != None:
    #                 # variations = enumerate(generate_payload_variations(json_obj))
    #                 for index, variation in enumerate(generate_payload_variations(json_obj)):
    #                     key_for_output = "_".join(list_different_values(json_obj, variation))
    #                     if escaped_or_unescaped == 0:
    #                         json_string = json.dumps(variation)
    #                     elif escaped_or_unescaped == 1:
    #                         json_string = escape_json(variation)
    #                     elif escaped_or_unescaped == 2:
    #                         json_string = encode_json_with_url_encoding(variation)
    #                     elif escaped_or_unescaped == 3:
    #                         json_string = encode_base64(variation)
    #                     permd_req = copy.deepcopy(req)
    #                     permd_req["headers"][key]["params"][p_key] = json_string
    #                     idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
    #                     # if idx_of_payload != 0:
    #                     run_feroxbuster(permd_req,"headers",key_for_output,(idx_of_payload - 1) % len(payloads))
    #                     # else:
    #                     #     run_feroxbuster(permd_req,"headers",key_for_output, 0, True)
    

    
    # log_file = open("logfile.log", "a")
    # log_file.write(str(counter.value) + " end of headers and start of body\n")
    # log_file.close()
    
    # fuzzing body
    if req["body"]:
        
        tried_body_keys = list()
        for index, variation in enumerate(generate_payload_variations(req["body"])):
            permd_req = copy.deepcopy(req)
            permd_req["body"] = variation
            key = ".".join(list_different_values(req["body"], permd_req["body"]))

            last_key = key.split(".")[-1]
                            
            if last_key in tried_body_keys:
                continue
                            
            tried_body_keys.append(last_key)
            
            idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
            # if idx_of_payload != 0:
            run_feroxbuster(permd_req,"body",key,(idx_of_payload - 1) % len(payloads))
            # else:
            #     run_feroxbuster(permd_req,"body",key, 0, True)
        if type(req["body"]) is dict:
            for key,value in req["body"].items():
                tried_body_keys = list()
                json_obj, escaped_or_unescaped = process_and_load_json(value)
                if json_obj != None:
                    # variations = enumerate(generate_payload_variations(json_obj))
                    # log_file = open("logfile.log", "a")
                    # log_file.write("\n")
                    # log_file.write("\n")
                    # log_file.write(str(counter.value) + " got out of the second generate_payload_variations " + str(variations) + "\n")
                    # log_file.write("\n")
                    # log_file.write("\n")
                    # log_file.close()
                    for index, variation in enumerate(generate_payload_variations(json_obj)):
                        # log_file = open("logfile.log", "a")
                        # log_file.write("\n")
                        # log_file.write("\n")
                        # log_file.write(str(counter.value) + " start of variation " + str(variation) +  " \n")
                        # log_file.write("\n")
                        # log_file.write("\n")
                        # log_file.close()
                        key_for_output = ".".join(list_different_values(json_obj, variation))
                        last_key = key_for_output.split(".")[-1]

                        if last_key in tried_body_keys:
                            continue

                        tried_body_keys.append(last_key)
                        
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
                        # log_file = open("logfile.log", "a")
                        # log_file.write("\n")
                        # log_file.write("\n")
                        # log_file.write(str(counter.value) + " mid of variation " + str(variation) +  " \n")
                        # log_file.write("\n")
                        # log_file.write("\n")
                        # log_file.close()
                        idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
                        # if idx_of_payload != 0:
                        run_feroxbuster(permd_req,"body",key_for_output,(idx_of_payload - 1) % len(payloads))
                        # else:
                        #     run_feroxbuster(permd_req,"body",key_for_output, 0, True)
                        # log_file = open("logfile.log", "a")
                        # log_file.write(str(counter.value) + " end of variation " + str(index) +  " \n")
                        # log_file.close()
        elif type(req["body"]) is list:
            for key in range(0, len(req["body"])):
                tried_body_keys = list()
                value = req["body"][key]
                json_obj, escaped_or_unescaped = process_and_load_json(value)
                if json_obj != None:
                    # variations = enumerate(generate_payload_variations(json_obj))
                    # log_file = open("logfile.log", "a")
                    # log_file.write("\n")
                    # log_file.write("\n")
                    # log_file.write(str(counter.value) + " got out of the second generate_payload_variations " + str(variations) + "\n")
                    # log_file.write("\n")
                    # log_file.write("\n")
                    # log_file.close()
                    for index, variation in enumerate(generate_payload_variations(json_obj)):
                        # log_file = open("logfile.log", "a")
                        # log_file.write("\n")
                        # log_file.write("\n")
                        # log_file.write(str(counter.value) + " start of variation " + str(variation) +  " \n")
                        # log_file.write("\n")
                        # log_file.write("\n")
                        # log_file.close()
                        key_for_output = ".".join(list_different_values(json_obj, variation))
                        last_key = key_for_output.split(".")[-1]

                        if last_key in tried_body_keys:
                            continue

                        tried_body_keys.append(last_key)
                        
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
                        # log_file = open("logfile.log", "a")
                        # log_file.write("\n")
                        # log_file.write("\n")
                        # log_file.write(str(counter.value) + " mid of variation " + str(variation) +  " \n")
                        # log_file.write("\n")
                        # log_file.write("\n")
                        # log_file.close()
                        idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
                        # if idx_of_payload != 0:
                        run_feroxbuster(permd_req,"body",key_for_output,(idx_of_payload - 1) % len(payloads))
    
    with proxy_setting_lock:
        used_proxies_across_processes.remove(proxy)

    log_file = open("logfile.log", "a")
    log_file.write("Finished " + str(counter.value) + "/" + str(requests_len) + "\n")
    log_file.close()
    
    with counter.get_lock():
        counter.value += 1

stop_event = threading.Event()
# def token_loop():

#     if stop_event.is_set():
#         return
#     with req_lock:
#         if args.delay != None:
#             time.sleep(args.delay)
#         subprocess.run(f"python3 {args.token_script}", shell=True)
        
#     threading.Timer(args.token_expiration, token_loop).start()

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

parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument("-r", "--request-file", required=False, help="Path to the request file containing headers.")
parser.add_argument("-rc", "--rate-config", required=False, help="Path to the rate config.")
parser.add_argument("-rsl", "--requests-list", required=False, help="obtain requests out of a list of reqs json")
parser.add_argument("-a", "--avoid-path", required=False, help="Filter this path or a path that has the input path (deny list) (ex: -a /logout,/deleteuser )")
parser.add_argument('-rl', '--rate-limit', required=False, type=int, help='Limit number of requests per second (per directory) (default: 1, i.e. 1 r/s)')
parser.add_argument('-np', '--no-proxy', action='store_true', help='don\'t use proxies and instead use the server ip')
parser.add_argument('-eh', '--exclude-headers', action='store_true', help='don\'t test headers')
parser.add_argument('-pn', '--payloads-number', type=int, required=False, help='number of payloads supplied per updating req.txt for like new authorization keys')
parser.add_argument('-ts', '--token-script', required=False, help='a python script to execute to generate new authorization keys')
parser.add_argument('-H', '--header', required=False, help='a header to add all requests like -H "X-Hackerone: seudxs"')
parser.add_argument('-w', '--wordlist', required=False, help='wordlist to use for fuzzing')
parser.add_argument('-d', '--delay', type=int, required=False, help='delay in seconds between --payloads-number requests')
parser.add_argument("-nd", "--normal-directory", required=False, help="other account's normal output directory to check against the main output directory for shared injection point value")
parser.add_argument('-te', '--token-expiration', type=int, required=False, help='executes token script everytime token expiration time in minutes is reached')
parser.add_argument("-uf", "--urls-file", required=False, help="urls file to add in the search")
parser.add_argument("-t", "--technique", required=False, help="technique to use for sqlmap")
parser.add_argument("-l", "--level", required=False, help="level to use for sqlmap")
parser.add_argument('-ds', '--delay-sql', type=int, required=False, help='delay for sqlmap and ghauri')
parser.add_argument("-kd", "--katana-directory", required=False, help="a directory that has the outputs of katana to parse as requests")
parser.add_argument("-kmhv", "--katana-match-host-value", required=False, help="test requests that are parsed from katana's output with matching host to this value")
parser.add_argument("-kihv", "--katana-in-host-value", required=False, help="test requests that are parsed from katana's output with host that contain this value")
parser.add_argument("-wa", "--waf", required=False, help="don't inject in path or queries")
args = parser.parse_args()


# proxies = []
# if args.no_proxy:
#     proxies.append("self")
# else:
#     if not args.rate_limit:
#         with open('/home/deus/documents/proxies.txt') as proxy_file:
#             for proxy in proxy_file:
#                 proxy = proxy.strip()
#                 if proxy != "":
#                     proxy = proxy.split(':')
#                     proxies.append(f"isp.smartproxy.com:{proxy[1]}")
#     else:
#         available_proxies = list()
#         with open('/home/deus/documents/proxies.txt') as proxy_file:
#             for proxy in proxy_file:
#                 proxy = proxy.strip()
#                 if proxy != "":
#                     proxy = proxy.split(':')
#                     available_proxies.append(f"isp.smartproxy.com:{proxy[1]}")
        
#         available_proxies_len = len(available_proxies)
        
#         for i in range(0, args.rate_limit):
#             proxies.append(available_proxies[i % available_proxies_len])

manager = multiprocessing.Manager()
used_proxies_across_processes = manager.list()
req_lock = multiprocessing.Lock()
signatures_and_their_data_lock = multiprocessing.Lock()
requests_with_special_needs_lock = multiprocessing.Lock()
proxy_setting_lock = multiprocessing.Lock()
counter = multiprocessing.Value('i',1)
req_number = multiprocessing.Value('i',1)
victim_params = list()

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

common_http_headers = [header.upper() for header in common_http_headers]

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

# if args.rate_limit != None and args.rate_limit < 1:
#     print("lmao enter rate limit properly")
#     exit()

# if args.wordlist == None:
#     with open("/home/deus/documents/fuzz_wordlist.txt", 'r') as fuzz_wordlist:
#         for payload in fuzz_wordlist:
#             payload = payload.strip()
#             payloads.append(payload)
# else:
#     with open(args.wordlist, 'r') as fuzz_wordlist:
#         for payload in fuzz_wordlist:
#             payload = payload.strip()
#             payloads.append(payload)

def get_all_keys_with_their_value(d):
    keys = []
    if isinstance(d, dict):
        for k, v in d.items():
            keys.append({k:v})
            if isinstance(v, dict) or isinstance(v, list):
                keys.extend(get_all_keys_with_their_value(v))
            else:
                json_obj, escaped_or_unescaped = process_and_load_json(v)
                if isinstance(json_obj, dict) or isinstance(json_obj, list):
                    keys.extend(get_all_keys_with_their_value(json_obj))
    elif isinstance(d, list):
        for v in d:
            if isinstance(v, dict) or isinstance(v, list):
                keys.extend(get_all_keys_with_their_value(v))
            else:
                json_obj, escaped_or_unescaped = process_and_load_json(v)
                if isinstance(json_obj, dict) or isinstance(json_obj, list):
                    keys.extend(get_all_keys_with_their_value(json_obj))
    return keys

val = ''.join(random.choices(string.ascii_letters + string.digits, k=8 * 1024))
payloads.extend(["*", f"{val}*"])

unpack_burp_output = list()
for burp_file in os.listdir('./input'):
    if os.path.exists("/home/deus/downloads"):
        subprocess.run(f"php /home/deus/downloads/unpack-burp/unpack-burp.php ./input/{burp_file} all > unpack_burp_output.txt", shell=True)
    else:
        subprocess.run(f"php /home/kali/Downloads/unpack-burp/unpack-burp.php ./input/{burp_file} all > unpack_burp_output.txt", shell=True)


    with open('unpack_burp_output.txt', 'r') as file:
        unpack_burp_output.extend(file.read().split("\n\n"))

reqs = list()
unique_reqs_check = dict()

for request_and_response in unpack_burp_output:
    if request_and_response == '':
        continue
    
    request_and_response = json.loads(request_and_response)
    
    if  args.avoid_path != None and any(avoid_path in request_and_response["reqp"].lower() for avoid_path in args.avoid_path):
        continue
    
    req_text = request_and_response["reqp"].replace("HTTP/2","HTTP/1.1") + "\r\n" + request_and_response["reqh"] + "\r\n\r\n" + request_and_response["reqb"]
    
    parsed_request = parse_http(req_text)
    if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
        parsed_request["internal"] = True
        
        try:
            for param in get_all_keys_with_their_value(json.loads(request_and_response["resb"])):
                if param not in victim_params:
                    victim_params.append(param)
            
            for param in get_all_keys_with_their_value(parsed_request["body"]):
                if param not in victim_params:
                    victim_params.append(param)
        except Exception as e:
            print(f"An ignored error occurred while parsing resb: {e}")
        
        reqs.append(parsed_request)
    else:
        print(req_text)

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
            if args.header != None and args.header[0] not in list(headers.keys()):
                headers[args.header[0]] = {'value': args.header[1], 'params': {}}
            
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

            if "response" in req_and_resp.keys() and "forms" in req_and_resp["response"].keys():
                for form in req_and_resp["response"]["forms"]:
                    url = form['action']
                    action_hostname = urlparse(url).netloc
                    if action_hostname not in unique_reqs_check.keys():
                        unique_reqs_check[action_hostname] = list()

                    try:
                        if f"{form['method']}_{'_'.join(get_all_values(form['parameters']))}" not in unique_reqs_check[action_hostname]:

                            path = extract_path(url)
                            queries = extract_query_parameters(url)
                            body = dict()

                            hostname = urlparse(url).hostname

                            if args.katana_match_host_value and args.katana_match_host_value != hostname.strip():
                                continue

                            if args.katana_in_host_value and args.katana_in_host_value not in hostname.strip():
                                continue

                            headers = dict()
                            headers["Host"] = {'value': hostname, 'params': {}}
                            headers['User-Agent'] = {'value': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'params': {}}
                            if args.header != None and args.header[0] not in list(headers.keys()):
                                headers[args.header[0]] = {'value': args.header[1], 'params': {}}

                            if form['method'] == "GET":
                                for param in get_all_values(form['parameters']):
                                    if param.strip():
                                        queries[param] = "inp"
                            else:
                                headers['Content-Type'] = {'value': form['enctype'], 'params': {}}

                                for param in get_all_values(form['parameters']):
                                    # body = dict()
                                    if param.strip():
                                        body[param] = "inp"

                            if len(list(body.keys())) == 0:
                                body = ""

                            http_data = {
                                'method': form['method'],
                                'path': path,
                                'queries': queries,
                                'headers': headers,
                                'body': body
                            }

                            reqs.append(http_data)

                            unique_reqs_check[action_hostname].append(f"{form['method']}_{'_'.join(get_all_values(form['parameters']))}")
                    except:
                        print("error parsing:")
                        print(form)
                        # exit()

# if args.requests_list:
#     with open(args.requests_list, 'r') as json_file:
#         args.requests_list = json.load(json_file)
    
#     for req in args.requests_list:
#         parsed_request = parse_http(req)
#         parsed_request["internal"] = True
#         reqs.append(parsed_request)

# if args.requests_list:
#     with open(args.requests_list, 'r') as json_file:
#         args.requests_list = json.load(json_file)
    
#     for req in args.requests_list:
#         parsed_request = parse_http(req)

#         if args.avoid_path != None and any(avoid_path in parsed_request["path"].lower() for avoid_path in args.avoid_path):
#             continue
        
#         if not parsed_request["path"]:
#             continue

#         reqs.append(parsed_request)

if args.requests_list:
    with open(args.requests_list, 'r') as requests_list_file:
        for req in requests_list_file:
            req = json.loads(req)
            reqs.append(req)

# for key,values in unique_reqs_check.items():
#     print(key)
#     # for value in values:
#     #     if "eq_class" in value:
#     #         print(value)
#     print("\n".join(values))
# exit()

requests_len = len(reqs)

# if args.rate_limit == None:
#     pool = multiprocessing.Pool(len(proxies))
# else:
    
#     # log_file = open("logfile.log", "a")
#     # log_file.write(f" {len(proxies) * args.rate_limit} \n")
#     # log_file.close()
#     pool = multiprocessing.Pool(int(len(proxies) * args.rate_limit))

# pool = multiprocessing.Pool(len(proxies))
# pool.map(permutate_and_send_request, reqs, chunksize=1)

grouped_reqs = group_reqs_by_hostname(reqs)

for hostname, reqs in grouped_reqs.items():

    requests_len = len(reqs)
    used_user_agents = set()
    proxies = []
    if args.no_proxy:
        proxies.append("self")
        # proxies.append(f"127.0.0.1:8080")
    else:
        port, rota_proc = get_proxy_port(hostname, args.rate_limit, used_user_agents)
        proxies.append(f"127.0.0.1:{port}")
    
    counter.value = 1
    pool = multiprocessing.Pool(len(proxies))
    pool.map(permutate_and_send_request, reqs, chunksize=1)


    if not args.no_proxy:
        rota_exit_handler(rota_proc)

stop_event.set()

# for filename in glob.glob('endpoint_*.txt') + glob.glob('body_*.txt'):
#     os.remove(filename)