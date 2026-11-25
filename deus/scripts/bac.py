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
from collections import defaultdict, Counter
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
import sys
import fcntl
import base64
import shlex
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
import humps
import random
import signal
from collections.abc import Sized
import select
import urllib3
from ipwhois import IPWhois
from ipwhois.exceptions import IPDefinedError
import socket
from itertools import repeat
from collections import Counter
import string
import gc
import tracemalloc
from datetime import datetime
import statistics
import itertools
# Load the SBERT model
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from sentence_transformers import SentenceTransformer, util



# at the very top of your script:
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# def print_traceback(sig, frame):
#     # print(f"Process {os.getpid()} - Stack Trace:")
#     # traceback.print_stack(frame)

#     log_file = open("logfile.log", "a")
#     log_file.write(f"Process {os.getpid()} - Stack Trace:")
#     log_file.write("Traceback:\n")
#     log_file.write(traceback.format_stack())
#     log_file.close()


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

def filter_params(param):
    global key_value_pair_for_x8
    for k_v_pair in key_value_pair_for_x8:
        key = list(k_v_pair.keys())[0]
        if key == param:
            return k_v_pair

def split_list(lst, n):
    """
    Splits a list into a list of lists, with each sublist containing `n` elements.

    :param lst: The original list to be split.
    :param n: The number of elements per sublist.
    :return: A list of sublists.
    """
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def split_param(param):
    return humps.kebabize(param).split("-")

def same_shit_different_story(param1, param2, loose, id_limited):
    if id_limited:
        if not are_they_similar_params(param1, "id") or not are_they_similar_params(param2, "id") or not are_they_similar_params(param1, "email") or not are_they_similar_params(param2, "email"):
            return False
    
    two_params = [param1, param2]
    are_they_the_same = ""
    for param in two_params:
        if not are_they_the_same:
            are_they_the_same = humps.camelize(param)
        else:
            are_they_the_same = are_they_the_same == humps.camelize(param)
    
    if not are_they_the_same or type(are_they_the_same) is str:
        are_they_the_same = two_params[0].lower() == two_params[1].lower()
    
    if not loose:
        return are_they_the_same
    
    if not are_they_the_same or type(are_they_the_same) is str:
        are_they_the_same = len(set(split_param(two_params[0].replace("es","").replace("s",""))).intersection(set(split_param(two_params[1].replace("es","").replace("s",""))))) > 0
    
    # if not are_they_the_same or type(are_they_the_same) is str:
    #     ascii_specials = set(string.punctuation)
    #     for ascii_special in ascii_specials:
    #         param1 = param1.replace(ascii_special, "")
    #         param2 = param2.replace(ascii_special, "")
    #     two_params = [param1, param2]

    #     if len(two_params[0]) > 1 and len(two_params[1]) > 1:
    #         if len(two_params[0]) > len(two_params[1]):
    #             are_they_the_same = two_params[1] in two_params[0]
    #         elif len(two_params[0]) < len(two_params[1]):
    #             are_they_the_same = two_params[0] in two_params[1]
    
    return are_they_the_same


embedding_cache = {}
synonyms_cache = {}

model = SentenceTransformer('all-MiniLM-L6-v2')  # A lightweight, efficient SBERT model


def get_embedding(text):
    if text not in embedding_cache:
        embedding_cache[text] = model.encode(text, convert_to_tensor=True)
    return embedding_cache[text]

def are_they_similar_params(params1, params2):
    # similarity_and_context_pairs = []

    for param1 in split_param(params2):
        if not param1 or len(param1) < 3:
            continue
    
        for param2 in split_param(params2):
            if not param2 or len(param2) < 3:
                continue

            # if (param1, param2) in synonyms_cache:
            #     similarity_and_context_pairs.append(synonyms_cache[(param1, param2)])
            #     continue

            embedding1 = get_embedding(param1)
            embedding2 = get_embedding(param2)
            similarity = util.cos_sim(embedding1, embedding2)
            similarity_num = round(similarity.item(), 1)
            similarity_bool = similarity_num >= 0.4
            if similarity_bool:
                synonyms_cache[(param1, param2)] = [similarity_bool, param1]
                return similarity_bool

    # return similarity_and_context_pairs


def list_subdirectories_recursive(directory):
    """
    Recursively list all subdirectories in the given directory.

    :param directory: The param of the directory to search.
    :return: A list of subdirectory params.
    """
    subdirectories = []
    for root, dirs, files in os.walk(directory):
        for subdir in dirs:
            subdirectories.append(os.path.join(root, subdir))
    return subdirectories



def search_string_in_file(file_path, search_string):
    """Search for the string in a specific file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if search_string.lower() == line.lower():
                    return True
    except (IOError, UnicodeDecodeError):
        # Skip files that can't be opened or read
        return True
    return False


param_pattern_1 = re.compile(r"[a-zA-Z0-9@$.!_-]+")
param_pattern_2 = re.compile(r"[a-zA-Z0-9@$.!_-]*(\[[a-zA-Z0-9@$.!_-]*\])?[a-zA-Z0-9@$.!_-]*")

def is_it_param(param):
    return bool(param_pattern_1.fullmatch(param) or param_pattern_2.fullmatch(param))
    #     return True
    #     parts_of_param = split_param(param)
        
    #     for part_of_param in parts_of_param:
    #         part_check = search_string_in_file('/home/deus/documents/sam-cc-parameters-mixedcase-all.txt', part_of_param)
    #         if part_check:
    #             return True
    
    # return False


def kill_process_and_children(pid):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):  # or parent.children() for non-recursive
            child.kill()
        parent.kill()
    except psutil.NoSuchProcess:
        pass

def extract_params(dir):
    global params
    global subdirectories

    # subprocess.run(f"cd {dir} && ~/scripts/encoded_part_of_name_remover.sh", shell=True, executable="/bin/bash")
    subprocess.run(["/home/deus/scripts/encoded_part_of_name_remover.sh"], cwd=dir)

    files = os.listdir(dir)
    for file in files:
        if os.path.isfile(f"{dir}/{file}"):
            quote_separators = [
                "'",
                '\"',
                "`"
            ]
            
            for sep in quote_separators:

                with open(f"params_output_{subdirectories.index(dir)}_{files.index(file)}.txt", "w") as output_file:
                    subprocess.run(
                        ["awk", f"-F{sep}", "{for (i=2; i<=NF; i+=2) print $i}", f"{dir}/{file}"],
                        stdout=output_file
                    )

                    subprocess.run(
                        ["sort", "-u", "-o", f"params_output_{subdirectories.index(dir)}_{files.index(file)}.txt"],
                        stdin=open(f"params_output_{subdirectories.index(dir)}_{files.index(file)}.txt", "r")
                    )

                # subprocess.run(
                #     ["anew", f"params_output_{subdirectories.index(dir)}_{files.index(file)}.txt"],
                #     stdin=open(f"params_output_{subdirectories.index(dir)}_{files.index(file)}.txt", "r"),
                #     stdout=subprocess.PIPE,
                #     stderr=subprocess.PIPE,
                #     text=True
                # )

                if os.path.exists(f"params_output_{subdirectories.index(dir)}_{files.index(file)}.txt"):
                    with open(f"params_output_{subdirectories.index(dir)}_{files.index(file)}.txt", "r") as params_file:
                        for param in params_file:
                            param = param.strip()

                            if bool(re.fullmatch(r"[a-zA-Z0-9._-]+", param)) and param not in params:
                                params.append(param)
                    
            os.remove(f"params_output_{subdirectories.index(dir)}_{files.index(file)}.txt")


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
                if method != "GET" and method != "DELETE":
                    if content_type and "json" in content_type.lower():
                        parsed_body = {}
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
        # pass

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

def get_all_values_including_dict_and_list(d):
    values = []
    
    def extract_values(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                extract_values(value)
            values.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                extract_values(item)
            values.append(obj)
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
def group_reqs_by_hostname(reqs):
    grouped = defaultdict(list)
    for req in reqs:
        # print(req)
        hostname = req['headers']['Host']['value']
        # print(f"hostname: {hostname}")

        if hostname:
            grouped[hostname].append(req)
        
    return grouped

def convert_to_manager_obj(obj, manager):
    if isinstance(obj, dict):
        return manager.dict({k: convert_to_manager_obj(v, manager) for k, v in obj.items()})
    elif isinstance(obj, list):
        return manager.list([convert_to_manager_obj(v, manager) for v in obj])
    else:
        return obj  # int, str, float, etc. remain as is

def convert_from_manager_obj(obj):
    from multiprocessing.managers import DictProxy, ListProxy
    
    if isinstance(obj, DictProxy):
        return {k: convert_from_manager_obj(v) for k, v in obj.items()}
    elif isinstance(obj, ListProxy):
        return [convert_from_manager_obj(v) for v in obj]
    else:
        return obj  # int, str, float, etc. remain as is

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

        response = requests.get(f'http://{url}', proxies=proxies, headers=headers, timeout=20)
        return bool(response.cookies)
    except requests.RequestException as e:
        print(f"Request failed (attempt {retries + 1}): {e}")
        if retries < 2:
            return response_has_cookies(url, retries + 1)
        return False


def most_common_keys_values_by_type(dict_list, n=1):
    # Initialize dictionaries to hold (count, value) for each key per type.
    # if type(dict_list) 
    type_data = {
        'None': {},
        'list': {},
        'dict': {},
        'bool': {},
        'int': {},
        'str': {}
    }
    
    # Process each one-pair dictionary in the list.
    for d in dict_list:
        if type(d) is not dict:
            continue
        for key, value in d.items():
            if not value:
                # For None, store the count and value (which is always None)
                # count, _ = type_data['None'].get(key, (0, None))
                # type_data['None'][key] = (count + 1, value)
                continue
            elif isinstance(value, list):
                count, _ = type_data['list'].get(key, (0, None))
                type_data['list'][key] = (count + 1, value)
            elif isinstance(value, dict):
                count, _ = type_data['dict'].get(key, (0, None))
                type_data['dict'][key] = (count + 1, value)
            # elif isinstance(value, bool):
                # Check for bool before int since bool is a subclass of int.
                # count, _ = type_data['bool'].get(key, (0, None))
                # type_data['bool'][key] = (count + 1, value)
                # pass
            elif isinstance(value, int):
                count, _ = type_data['int'].get(key, (0, None))
                type_data['int'][key] = (count + 1, value)
            elif isinstance(value, str):
                count, _ = type_data['str'].get(key, (0, None))
                type_data['str'][key] = (count + 1, value)
    
    # Now, sort each type's keys by count (in descending order) and retrieve the top n keys with their associated value.
    result = {}
    for type_name in ['list', 'dict', 'int', 'str']:
        sorted_items = sorted(
            type_data[type_name].items(),
            key=lambda item: item[1][0],
            reverse=True
        )
        # Instead of returning the count, we return the associated value.
        top_n = [(key, value) for key, (count, value) in sorted_items[:n]]
        result[type_name] = top_n
    return result


def most_common_keys_values_by_types_int_and_str(dict_list, n=1):
    # Initialize dictionaries to hold (count, value) for each key per type.
    # if type(dict_list) 
    type_data = {
        'None': {},
        'list': {},
        'dict': {},
        'bool': {},
        'int': {},
        'str': {}
    }
    
    # Process each one-pair dictionary in the list.
    for d in dict_list:
        if type(d) is not dict:
            continue
        for key, value in d.items():
            if not value:
                # For None, store the count and value (which is always None)
                # count, _ = type_data['None'].get(key, (0, None))
                # type_data['None'][key] = (count + 1, value)
                continue
            # elif isinstance(value, list):
            #     count, _ = type_data['list'].get(key, (0, None))
            #     type_data['list'][key] = (count + 1, value)
            # elif isinstance(value, dict):
            #     count, _ = type_data['dict'].get(key, (0, None))
            #     type_data['dict'][key] = (count + 1, value)
            # elif isinstance(value, bool):
                # Check for bool before int since bool is a subclass of int.
                # count, _ = type_data['bool'].get(key, (0, None))
                # type_data['bool'][key] = (count + 1, value)
                # pass
            elif isinstance(value, int):
                count, _ = type_data['int'].get(key, (0, None))
                type_data['int'][key] = (count + 1, value)
            elif isinstance(value, str):
                count, _ = type_data['str'].get(key, (0, None))
                type_data['str'][key] = (count + 1, value)
    
    # Now, sort each type's keys by count (in descending order) and retrieve the top n keys with their associated value.
    result = {}
    for type_name in ['list', 'dict', 'int', 'str']:
        sorted_items = sorted(
            type_data[type_name].items(),
            key=lambda item: item[1][0],
            reverse=True
        )
        # Instead of returning the count, we return the associated value.
        top_n = [(key, value) for key, (count, value) in sorted_items[:n]]
        result[type_name] = top_n
    return result


def all_unique_sets(items):
    results = []
    for r in range(1, 5):
        for combo in itertools.combinations(items, r):
            results.append(combo)
    return results

def get_same_context_urls(url):
    all_urls = []

    with open("grouped_paths.json", "r") as f:
        data = json.load(f)

    for key, urls in data.items():
        if isinstance(urls, list) and url in urls:
            all_urls.extend(urls)
    
    return all_urls
        

def permutate_and_send_request(req):
    global params
    global args
    global used_proxies_across_processes
    global proxies
    global manager
    global req_lock
    global signatures_and_their_data_lock
    global requests_with_special_needs_lock
    global proxy_setting_lock
    global x8_lock
    global common_http_headers
    global counter
    global req_number
    global requests_len
    global reqs
    global key_value_pair
    global keys_of_key_value_pair
    global key_value_pair_len
    global param_file_lock
    global paths_output_count
    global bac_reqs_and_their_signatures_lock
    global param_pattern_1
    global param_pattern_2
    # global key_counts
    # global seen_values
    global reqs_variations_for_context
    global loop_count
    global key_value_pair_for_x8

    # log_file = open("logfile.log", "a")
    # log_file.write(f"loooop_count: {loop_count}\n")
    # log_file.close()

    # checking if it's successful request by checking if it has 2xx status code. add a boolean that tells if parameter length was put for this request
    if args.stop_at_success:
        for key in list(reqs_variations_for_context.keys()):
            if f"req_{reqs.index(req)}" == key:
                for req_var in reqs_variations_for_context[key]:
                    if req_var["status_code"] == 200:
                        return


    # log_file = open("logfile.log", "a")
    # log_file.write(f"in {reqs.index(req)}: {req} \n")
    # log_file.close()


    def print_traceback(sig, frame):
        # print(f"Process {os.getpid()} - Stack Trace:")
        # traceback.print_stack(frame)

        log_file = open("logfile.log", "a")
        log_file.write(f"Process {os.getpid()} - Stack Trace:\n")
        log_file.write("Traceback:\n")
        log_file.write(traceback.format_stack())
        log_file.close()
    
    signal.signal(signal.SIGUSR1, print_traceback)

    # sys.setrecursionlimit(5000)
    
    # from sentence_transformers import SentenceTransformer, util
    # model = SentenceTransformer('all-MiniLM-L6-v2')  # A lightweight, efficient SBERT model

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
    #     counter1 = Counter(proxies)
    #     counter2 = Counter(used_proxies_across_processes)
    #     result_counter = counter1 - counter2
    #     result = list(result_counter.elements())
    #     proxy = result[0]
    #     used_proxies_across_processes.append(proxy)

    
    proxy = proxies[0]



        
        # while True:
        #     try:
        #         # proxy = ""
        #         if args.rate_limit == None:
        #             proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
        #         else:
        #             for l_proxy in proxies:
        #                 l_proxy_count = used_proxies_across_processes.count(l_proxy)

        #                 # log_file = open("logfile.log", "a")
        #                 # log_file.write(f" {l_proxy} {l_proxy_count} \n")
        #                 # log_file.close()
        #                 if l_proxy_count < args.rate_limit:
        #                     # log_file = open("logfile.log", "a")
        #                     # log_file.write(f" assigned proxy \n")
        #                     # log_file.close()
        #                     proxy = l_proxy
                
        #         if proxy:
        #             used_proxies_across_processes.append(proxy)
        #         else:
        #              raise ValueError("proxy is empty")
        #         break
        #     except ValueError as e:
        #         log_file = open("fuzz.log", "a")
        #         log_file.write(f" Error: {e} from {','.join(proxies)}\n")
        #         log_file.close()
        #         time.sleep(2)
    
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
    
    def split_param(param):

        if re.match(r'^[a-z]+(?:[A-Z][a-z]*)*$', param):  # camelCase
            param_with_spaces_as_its_separator = " ".join(re.findall(r'[a-z]+|[A-Z][a-z]*', param))
        elif re.match(r'^[A-Z][a-z]*(?:[A-Z][a-z]*)*$', param):  # PascalCase
            param_with_spaces_as_its_separator = " ".join(re.findall(r'[A-Z][a-z]*', param))
        elif re.match(r'^[a-z]+(?:_[a-z]+)*$', param):  # snake_case
            param_with_spaces_as_its_separator = " ".join(param.split('_'))
        elif re.match(r'^[a-z]+(?:-[a-z]+)*$', param):  # kebab-case
            param_with_spaces_as_its_separator = " ".join(param.split('-'))

        return param


    
                
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
                    update_dict_with_matches(target_dict[key], copy.deepcopy(value))
                else:
                    target_dict[key] = value

    def run_feroxbuster(perm_req, part_to_be_enumed):
        nonlocal req_signature
        
        url = f"https://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"
        
        # log_file = open("logfile.log", "a")
        # log_file.write(str(counter.value) + " start 2\n")
        # log_file.close()

        if args.delay != None and idx_of_param % args.params_number == 0:
            time.sleep(args.delay)
        
        # log_file = open("logfile.log", "a")
        # log_file.write(str(counter.value) + " end 2\n")
        # log_file.close()

        with req_lock:
            if args.request_file != None:
                if args.params_number != None and args.token_expiration == None and args.token_script != None and idx_of_param % args.params_number == 0:
                    subprocess.run(f"python3 {args.token_script}", shell=True)
                
                # log_file = open("logfile.log", "a")
                # log_file.write(str(counter.value) + " start 5\n")
                # log_file.close()

                headers = extract_headers(args.request_file)
                queries = extract_query_parameters(args.request_file)

                # log_file = open("logfile.log", "a")
                # log_file.write(f"queries: {queries}\n")
                # log_file.write(f"type(queries): {type(queries)}\n")
                # log_file.write(f'perm_req["queries"]: {perm_req["queries"]}\n')
                # log_file.write(f'type(perm_req["queries"]): {type(perm_req["queries"])}\n')
                # log_file.close()

                if queries and perm_req["queries"]:
        
                    update_dict_with_matches(perm_req["queries"], queries)
                # print("Before: ")
                # print("First: " + str(perm_req["headers"]))
                # print("Second: " + str(headers))

                if headers and perm_req["headers"]:
                    update_dict_with_matches(perm_req["headers"], headers)
                # print("After: ")
                # print("First: " + str(perm_req["headers"]))
                # print("Second: " + str(headers))
                # exit()

                # log_file = open("logfile.log", "a")
                # log_file.write(str(counter.value) + " end 5\n")
                # log_file.close()
        
        # log_file = open("logfile.log", "a")
        # log_file.write(str(counter.value) + " start 3\n")
        # log_file.close()

        if args.delay != None and args.token_script != None and idx_of_param % args.params_number == 0 and args.token_expiration == None:
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
                queries[key] = str(value).strip()
        
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
        headers = perm_req["headers"]
        
        # def safe_urlencode(data):
        #     def ensure_not_encoded(value):
        #         while True:
        #             decoded = unquote(value)
        #             if decoded == value:  # Stop when decoding no longer changes the value
        #                 return decoded
        #             value = decoded
            
        #     # Apply the encoding to each key-value pair
        #     safe_data = { key: ensure_not_encoded(value) if isinstance(value, str) else value for key, value in data.items() }
        #     return urlencode(safe_data)
        
            

        def get_the_new_or_updated_key_and_its_value(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    # log_file = open("logfile.log", "a")
                    # log_file.write(f"Checking key: {k}")
                    # log_file.close()

                    if "PAYLOADDDD" in k:
                        # log_file = open("logfile.log", "a")
                        # log_file.write(f"found payload pair: {k} {v}\n")
                        # log_file.close()
                        return {k:v}
                    if isinstance(v, dict) or isinstance(v, list):
                        payload = get_the_new_or_updated_key_and_its_value(v)
                        if payload:
                            return payload
                    else:
                        json_obj, escaped_or_unescaped = process_and_load_json(v)
                        if isinstance(json_obj, dict) or isinstance(json_obj, list):
                            payload = get_the_new_or_updated_key_and_its_value(json_obj)
                            if payload:
                                return payload
            elif isinstance(d, list):
                # log_file = open("logfile.log", "a")
                # log_file.write(f"entered list: {d}")
                # log_file.close()
                for v in d:
                    if isinstance(v, dict) or isinstance(v, list):
                        payload = get_the_new_or_updated_key_and_its_value(v)
                        if payload:
                            return payload
                    else:
                        json_obj, escaped_or_unescaped = process_and_load_json(v)
                        if isinstance(json_obj, dict) or isinstance(json_obj, list):
                            payload = get_the_new_or_updated_key_and_its_value(json_obj)
                            if payload:
                                return payload

        # types_of_values = [0, 1, 1.1, "test", "$100.99", "email@aaaaa.com", "+1-555-123-4567","+44-20-7946-0958","15551234567","442079460958","123 Main St, New York, NY 10001","San Francisco","California","United States","US","USA","90210","37.7749, -122.4194", "America/New_York","https://www.example.com","192.168.1.1","#FF5733","/etc/passwd","14:30:00","1925000000","2037-03-03T07:06:40Z","2037-03-03","631152000","1990-01-01T00:00:00Z","1990-01-01",True, False,123456789012,"123456789012","DE89370400440532013000",[],dict()]
        
        # types_of_values = [0, 1, 1.1, "test", "email@aaaaa.com", "+1-555-123-4567","+44-20-7946-0958","15551234567","442079460958","US","USA", "America/New_York","https://www.example.com","/etc/passwd","14:30:00","1925000000","2037-03-03T07:06:40Z","2037-03-03","631152000","1990-01-01T00:00:00Z","1990-01-01",True, False,[],dict()]
        types_of_values = ["aaaaa",1, 1.1, True, False, [],[{}], dict(), None]
        # key_value_pair.extend(types_of_values)

        def generate_value_variations(dict_or_list, current_switched_points, perform_delete_keys, id_limited):
            dict_or_list = copy.deepcopy(dict_or_list)
            # log_file = open("logfile.log", "a")
            # log_file.write(f"has entered here 3 \n")
            # log_file.close()
            
            nonlocal discovered_keys
            if type(dict_or_list) is dict:
                for key, value in dict_or_list.items():
                    if args.avoid_keys and key in args.avoid_keys:
                        continue

                    if type(value) is dict or type(value) is list:

                        for variation in generate_value_variations(value, current_switched_points, perform_delete_keys, id_limited):
                            permd_dict_or_list = copy.deepcopy(dict_or_list)
                            permd_dict_or_list[key] = variation
                            yield permd_dict_or_list
                    # else:
                    
                    # exists_in_key_value_pair = any(same_shit_different_story(list(type_of_value.keys())[0], key) for type_of_value in key_value_pair)
                    # exists_in_context_access_params = any(are_they_similar_params(list(type_of_value.keys())[0], key) for type_of_value in context_access_params)
                    exists_in_context_access_params = any(
    same_shit_different_story(list(type_of_value.keys())[0], key, True, id_limited)
    for type_of_value in context_access_params
)

                    # if not exists_in_key_value_pair and not exists_in_context_access_params and len(current_switched_points) < 2:
                    # if not exists_in_context_access_params and len(current_switched_points) < 2:
                    #     for type_of_value in types_of_values:
                    #         # log_file = open("logfile.log", "a")
                    #         # log_file.write(f"has entered here 6 \n")
                    #         # log_file.close()
                    #         # if len(current_switched_points) >= 2:
                    #         #     continue
                    #         # log_file = open("logfile.log", "a")
                    #         # log_file.write(f"has entered here 5 \n")
                    #         # log_file.close()
                    #         permd_dict_or_list = copy.deepcopy(dict_or_list)
                    #         permd_dict_or_list[key] = type_of_value
                    #         yield permd_dict_or_list
                    
                    if exists_in_context_access_params and len(current_switched_points) < 2:
                        # change_cnt = 0
                        for type_of_value in context_access_params:
                            if not same_shit_different_story(list(type_of_value.keys())[0], key, True, id_limited):
                                continue
                            
                            # change_cnt += 1
                            # if change_cnt == 6:
                            #     break
                            
                            type_of_value = list(type_of_value.values())[0]
                            
                            permd_dict_or_list = copy.deepcopy(dict_or_list)
                            permd_dict_or_list[key] = type_of_value
                            yield permd_dict_or_list
                    
                        # if exists_in_key_value_pair:
                        #     change_cnt = 0
                        #     for type_of_value in key_value_pair:
                        #         change_cnt += 1
                        #         if change_cnt == 6:
                        #             break

                        #         # log_file = open("logfile.log", "a")
                        #         # log_file.write(f"has entered here 7 \n")
                        #         # log_file.close()

                        #         # if list(type_of_value.keys())[0] != key:
                        #         if not same_shit_different_story(list(type_of_value.keys())[0], key):
                        #             continue
                                
                        #         type_of_value = list(type_of_value.values())[0]

                        #         # log_file = open("logfile.log", "a")
                        #         # log_file.write(f"has entered here 4 {type_of_value}\n")
                        #         # log_file.close()


                        #         # if type_of_value == value:
                        #         #     continue
                                
                        #         # log_file = open("logfile.log", "a")
                        #         # log_file.write(f"has entered here 8 \n")
                        #         # log_file.close()

                        #         permd_dict_or_list = copy.deepcopy(dict_or_list)
                        #         permd_dict_or_list[key] = type_of_value
                        #         yield permd_dict_or_list
                    
                    if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:
                        permd_dict_or_list = copy.deepcopy(dict_or_list)
                        del permd_dict_or_list[key]
                        yield permd_dict_or_list
                    

                        # while True:
                        #     key_to_delete = ""
                        #     log_file = open("logfile.log", "a")
                        #     log_file.write(f"before ddddfddddddd call in here 1\n")
                        #     log_file.close()
                        #     if key_to_delete:
                        #         permd_req = copy.deepcopy(current_req)
                        #         del permd_dict_or_list[key_to_delete]

                        #         avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                        #     else:
                        #         avg, std, status_std = measure_average_content_length(current_req, current_switched_points)
                        #     break_out_of_loop = False
                        #     restart_loop = False
                        #     for key, value in (current_req.get("queries") or {}).items():
                        #         permd_req = copy.deepcopy(current_req)
                        #         del permd_dict_or_list[key]
                        #         # current_switched_points = current_switched_points + [f"{key}_deleted"]
                        #         log_file = open("logfile.log", "a")
                        #         log_file.write(f"before generate_req_variations call in heeeeeeeeeeeeere 1\n")
                        #         log_file.close()
                    
                        #         res = get_status_code_and_resb(permd_req, current_switched_points)
                        #         log_file = open("logfile.log", "a")
                        #         log_file.write(f"after generate_req_variations calllllllllllllllll in here 2\n")
                        #         log_file.close()
                    
                        #         if not res:
                        #             continue
                        #         if res['resb']:
                        #             new_length = len(str(res['resb']))
                        #         else:
                        #             new_length = 0
                        #         if res['status_code'] == status_std:
                        #             if is_length_unusual(new_length, avg, std_dev=std, tolerance=1):
                        #                 key_to_delete = key
                        #                 yield permd_dict_or_list
                        #                 restart_loop = True
                        #                 break
                        #         else:
                        #             # stack.append((permd_req, new_switched_points))
                        #             yield permd_dict_or_list
                        #             break_out_of_loop = True
                        #             break

                        #     if break_out_of_loop:
                        #         break

                        #     if restart_loop:
                        #         continue

                        #     if break_out_of_loop == False and restart_loop == False:
                        #         break

                        # permd_dict_or_list = copy.deepcopy(dict_or_list)
                        # del permd_dict_or_list[key]
                        # yield permd_dict_or_list
                    
            elif type(dict_or_list) is list:
                if len(dict_or_list) == 0:
                    dict_or_list.append(999999999999999999999999999999999999999)
                
                for key in range(0, len(dict_or_list)):
                    
                    value = dict_or_list[key]
                    if type(value) is dict or type(value) is list:

                        for variation in generate_value_variations(value, current_switched_points, perform_delete_keys, id_limited):
                            permd_dict_or_list = copy.deepcopy(dict_or_list)
                            permd_dict_or_list[key] = variation
                            yield permd_dict_or_list
                    # elif type(value) is not str or (type(value) is str and " " not in value):
                        # exists_in_key_value_pair = any(same_shit_different_story(list(type_of_value.keys())[0], key) for type_of_value in key_value_pair)
                    # exists_in_context_access_params = any(are_they_similar_params(list(type_of_value.keys())[0], key) for type_of_value in context_access_params)
                    
                    # if not exists_in_key_value_pair and not exists_in_context_access_params and len(current_switched_points) < 2:
                    if len(current_switched_points) < 2:
                        for type_of_value in types_of_values:
                            # if len(current_switched_points) >= 2:
                            #     continue
                            permd_dict_or_list = copy.deepcopy(dict_or_list)
                            permd_dict_or_list[key] = type_of_value
                            yield permd_dict_or_list
                    
                    # if exists_in_context_access_params:
                        # change_cnt = 0
                    for type_of_value in values_of_context_access_params:
                        # change_cnt += 1
                        # if change_cnt == 6:
                        #     break
                        
                        # type_of_value = list(type_of_value.values())[0]
                        
                        permd_dict_or_list = copy.deepcopy(dict_or_list)
                        permd_dict_or_list[key] = type_of_value
                        yield permd_dict_or_list
                
                        # if exists_in_key_value_pair:
                        #     change_cnt = 0
                        #     for type_of_value in key_value_pair:
                        #         change_cnt += 1
                        #         if change_cnt == 6:
                        #             break
                                
                        #         if not same_shit_different_story(list(type_of_value.keys())[0], key):
                        #             continue

                        #         type_of_value = list(type_of_value.values())[0]

                        #         # if type_of_value == value:
                        #         #     continue

                        #         permd_dict_or_list = copy.deepcopy(dict_or_list)
                        #         permd_dict_or_list[key] = type_of_value
                        #         yield permd_dict_or_list
                    
                    if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:
                        permd_dict_or_list = copy.deepcopy(dict_or_list)
                        del permd_dict_or_list[key]
                        yield permd_dict_or_list
                    
                    # if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:

                    #     while True:
                    #         key_to_delete = ""
                    #         log_file = open("logfile.log", "a")
                    #         log_file.write(f"before genefdsfsdfdsfsdfsfsdfsdfsdfsdrate_req_variationkkkkkkkkkkks call in here 1\n")
                    #         log_file.close()
                    #         if key_to_delete:
                    #             permd_req = copy.deepcopy(current_req)
                    #             del permd_dict_or_list[key_to_delete]

                    #             avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                    #         else:
                    #             avg, std, status_std = measure_average_content_length(current_req, current_switched_points)
                    #         break_out_of_loop = False
                    #         restart_loop = False
                    #         for key, value in (current_req.get("queries") or {}).items():
                    #             permd_req = copy.deepcopy(current_req)
                    #             del permd_dict_or_list[key]
                    #             # current_switched_points = current_switched_points + [f"{key}_deleted"]
                    #             log_file = open("logfile.log", "a")
                    #             log_file.write(f"before generate_req_variationkkkkkkkkkkks call in here 1\n")
                    #             log_file.close()
                    #             res = get_status_code_and_resb(permd_req, current_switched_points)
                    #             log_file = open("logfile.log", "a")
                    #             log_file.write(f"after generate_req_variations call in here 2\n")
                    #             log_file.close()
                    #             if not res:
                    #                 continue
                    #             if res['resb']:
                    #                 new_length = len(str(res['resb']))
                    #             else:
                    #                 new_length = 0
                    #             if res['status_code'] == status_std:
                    #                 if is_length_unusual(new_length, avg, std_dev=std, tolerance=1):
                    #                     key_to_delete = key
                    #                     yield permd_dict_or_list
                    #                     restart_loop = True
                    #                     break
                    #             else:
                    #                 # stack.append((permd_req, new_switched_points))
                    #                 yield permd_dict_or_list
                    #                 break_out_of_loop = True
                    #                 break

                    #         if break_out_of_loop:
                    #             break

                    #         if restart_loop:
                    #             continue

                    #         if break_out_of_loop == False and restart_loop == False:
                    #             break


                        # permd_dict_or_list = copy.deepcopy(dict_or_list)
                        # del permd_dict_or_list[key]
                        # yield permd_dict_or_list
        
                
        # def key_deletion_variations(dict_or_list, current_switched_points, perform_delete_keys=True):
        #     dict_or_list = copy.deepcopy(dict_or_list)
        #     # log_file = open("logfile.log", "a")
        #     # log_file.write(f"has entered here 3 \n")
        #     # log_file.close()
            
        #     nonlocal discovered_keys
        #     if type(dict_or_list) is dict:
        #         for key, value in dict_or_list.items():
        #             if args.avoid_keys and key in args.avoid_keys:
        #                 continue

        #             if type(value) is dict or type(value) is list:

        #                 for variation in key_deletion_variations(value, current_switched_points, perform_delete_keys):
        #                     permd_dict_or_list = copy.deepcopy(dict_or_list)
        #                     permd_dict_or_list[key] = variation
        #                     yield permd_dict_or_list
                    
        #             if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:
        #                 permd_dict_or_list = copy.deepcopy(dict_or_list)
        #                 del permd_dict_or_list[key]
        #                 yield permd_dict_or_list

        #     elif type(dict_or_list) is list:
        #         if len(dict_or_list) == 0:
        #             dict_or_list.append(999999999999999999999999999999999999999)
                
        #         for key in range(0, len(dict_or_list)):
                    
        #             value = dict_or_list[key]
        #             if type(value) is dict or type(value) is list:

        #                 for variation in key_deletion_variations(value, current_switched_points, perform_delete_keys):
        #                     permd_dict_or_list = copy.deepcopy(dict_or_list)
        #                     permd_dict_or_list[key] = variation
        #                     yield permd_dict_or_list
                
        #         if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:
        #             for key in range(0, len(dict_or_list)):
                        
        #                 permd_dict_or_list = copy.deepcopy(dict_or_list)
        #                 del permd_dict_or_list[key]
        #                 yield permd_dict_or_list
        def is_length_unusual(new_length, avg, std_dev, tolerance=1):
            """
            Check if a new length is unusual compared to avg ± (tolerance * std_dev).

            :param new_length: Length of the new response body in bytes
            :param avg: Average content length from previous runs
            :param std_dev: Standard deviation from previous runs
            :param tolerance: How many deviations away from avg is still considered normal
            :return: True if unusual, False otherwise
            """
            lower_bound = avg - (tolerance * std_dev)
            upper_bound = avg + (tolerance * std_dev)
            return not (lower_bound <= new_length <= upper_bound)

        def measure_average_content_length(permd_req, new_switched_points):
            """
            Measure average and standard deviation of content length from repeated requests.

            :param request_func: Function that returns the response body (string or bytes)
            :param runs: Number of times to repeat the request
            :return: (average_length, std_dev)
            """
            lengths = []
            statuses = []
            for _ in range(3):
                log_file = open("logfile.log", "a")
                log_file.write(f"before generate_req_variations hkjcall in here 1\n")
                log_file.close()
                resp = get_status_code_and_resb(permd_req, new_switched_points, True)

                log_file = open("logfile.log", "a")
                log_file.write(f"after generate_req_variations call in hehkjhkjre 2\n")
                log_file.close()

                if not resp:
                    continue
                
                body = resp['resb']
                statuses.append(resp['status_code'])
                if body is not None:
                    length = len(str(body))
                else:
                    length = 0
                
                lengths.append(length)

            avg_length = statistics.mean(lengths)
            std_dev = statistics.stdev(lengths) if len(lengths) > 1 else 0
            status_std = max(set(statuses), key=statuses.count)

            return avg_length, std_dev, status_std, res

        discovered_keys = set()
        def generate_req_variations(perm_req, switched_injection_points, perform_delete_keys, id_limited):
            log_file = open("logfile.log", "a")
            log_file.write(f"start of generate_req_variations\n")
            log_file.close()

            nonlocal injection_point_count
            nonlocal discovered_keys
            status_codes_and_variation = []
            stack = [(perm_req, switched_injection_points)]

            max_workers = 1
            if args.concurrency:
                max_workers = args.concurrency
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:  # Adjust workers as needed
                future_to_request = {}

                while stack:
                    current_req, current_switched_points = stack.pop()
                    log_file = open("logfile.log", "a")
                    log_file.write(f"injection_point_count: {injection_point_count}\n")
                    log_file.write(f"len(current_switched_points): {len(current_switched_points)}\n")
                    log_file.close()
                    
                    # if len(current_switched_points) >= min(2, injection_point_count):
                    #     continue

                    # limiting to 2 permutations for injection_point_count that's equal or less than 5 and limiting to 1 permutation for injection_point_count that's greater than 5
                    if id_limited:
                        if len(current_switched_points) >= min(5, injection_point_count):
                            continue
                    else:
                        if (len(current_switched_points) >= min(2, injection_point_count) and 5 >= injection_point_count) or (len(current_switched_points) >= min(1, injection_point_count) and 5 < injection_point_count):
                            continue
                    
                    # Fuzzing path
                    subpaths = current_req["path"].split("/")
                    for i, subpath in enumerate(subpaths):
                        
                        if not subpath or (not (sum(1 for ch in subpath if ch.isdigit()) > 2) and not (sum(1 for ch in subpath if ch.isupper()) > 5) ):
                            continue
                        
                        for type_of_value in values_of_context_access_params:
                        # for type_of_value in context_access_params:
                            
                            type_of_value_original = copy.deepcopy(type_of_value)
                            key_of_type_of_value = ""
                            for context_access_param in context_access_params:
                                key_of_context_access_param = list(context_access_param.keys())[0]
                                value_of_context_access_param = list(context_access_param.values())[0]
                                if type_of_value_original == value_of_context_access_param:
                                    key_of_type_of_value = key_of_context_access_param
                                    break



                            # if not isinstance(type_of_value, (str, int)) or type_of_value == subpath or ("id" not in key_of_type_of_value and "slug" not in key_of_type_of_value) or (type(type_of_value) is str and " " in type_of_value):
                            if not isinstance(type_of_value, (str, int)) or (type(type_of_value) is str and " " in type_of_value):
                                continue
                            
                            permd_req = copy.deepcopy(current_req)
                            permd_req["path"] = permd_req["path"].replace(subpath, str(type_of_value))
                            new_switched_points = current_switched_points + [f"{i+1}_subpath_{values_of_context_access_params.index(type_of_value_original)+1}_value--key--{key_of_type_of_value}--key--"]

                            log_file = open("logfile.log", "a")
                            log_file.write(f"before generate_req_variations call in fuzzing path\n")
                            log_file.close()
                    
                            future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                            log_file = open("logfile.log", "a")
                            log_file.write(f"after generate_req_variations call in fuzzing path\n")
                            log_file.close()
                    
                            future_to_request[future] = (permd_req, new_switched_points)
                            
                            stack.append((permd_req, new_switched_points))
                            
                    log_file = open("logfile.log", "a")
                    log_file.write(f"after fuzzing path: {injection_point_count}\n")
                    log_file.close()
                    
                    # Fuzzing queries
                    tried_queries_keys = []
                    for key, value in (current_req.get("queries") or {}).items():
                        # log_file = open("logfile.log", "a")
                        # log_file.write(f"checking out query key before not in discovered_keys: {key}\n")
                        # log_file.close()

                        # last_key = key_for_output.split("--key--")[-1]
        
                        if key in tried_queries_keys:
                            continue
        
                        tried_queries_keys.append(key)
                        
                        if args.avoid_keys and key in args.avoid_keys:
                            continue

                        # if args.discovered_keys_only:
                        #     if key not in discovered_keys:
                        #         continue
                        
                        # log_file = open("logfile.log", "a")
                        # log_file.write(f"checking out query key after not in discovered_keys: {key}\n")
                        # log_file.close()
                        
                        # exists_in_key_value_pair = any(same_shit_different_story(list(type_of_value.keys())[0], key) for type_of_value in key_value_pair)
                        exists_in_context_access_params = any(same_shit_different_story(list(type_of_value.keys())[0], key, True, id_limited) for type_of_value in context_access_params)
                        
                        # if not exists_in_key_value_pair and not exists_in_context_access_params and len(current_switched_points) < 2:
                        if not exists_in_context_access_params and len(current_switched_points) < 2:
                            for type_of_value in types_of_values:


                                # if len(current_switched_points) >= 2:
                                #     continue

                                permd_req = copy.deepcopy(current_req)
                                permd_req["queries"][key] = type_of_value
                                new_switched_points = current_switched_points + [f"--key--{key}--key--{types_of_values.index(type_of_value)+1+key_value_pair_len}_value"]

                                log_file = open("logfile.log", "a")
                                log_file.write(f"before generate_req_variations call in queries 1\n")
                                log_file.close()

                                future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                                future_to_request[future] = (permd_req, new_switched_points)

                                log_file = open("logfile.log", "a")
                                log_file.write(f"after generate_req_variations call in queries 2\n")
                                log_file.close()

                                stack.append((permd_req, new_switched_points))
                        
                        if exists_in_context_access_params and len(current_switched_points) < 2:
                            # change_cnt = 0
                            for type_of_value in context_access_params:
                                if not same_shit_different_story(list(type_of_value.keys())[0], key, True, id_limited):
                                    continue
                                
                                # change_cnt += 1
                                # if change_cnt == 6:
                                #     break
                                
                                type_of_value_original = copy.deepcopy(type_of_value)

                                type_of_value = list(type_of_value.values())[0]

                                permd_req = copy.deepcopy(current_req)
                                permd_req["queries"][key] = type_of_value
                                new_switched_points = current_switched_points + [f"--key--{key}--key--{context_access_params.index(type_of_value_original)+1}_value"]


                                log_file = open("logfile.log", "a")
                                log_file.write(f"before generate_req_variations call in queries 3\n")
                                log_file.close()
                                future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                                future_to_request[future] = (permd_req, new_switched_points)

                                log_file = open("logfile.log", "a")
                                log_file.write(f"after generate_req_variations call in here 4\n")
                                log_file.close()
                                stack.append((permd_req, new_switched_points))
                        
                        # if exists_in_key_value_pair:
                        #     change_cnt = 0
                        #     for type_of_value in key_value_pair:
                        #         change_cnt += 1
                        #         if change_cnt == 6:
                        #             break
                                
                        #         if not same_shit_different_story(list(type_of_value.keys())[0], key):
                        #             continue
                                
                        #         type_of_value_original = copy.deepcopy(type_of_value)

                        #         type_of_value = list(type_of_value.values())[0]

                        #         # if type_of_value == value:
                        #         #     continue

                        #         permd_req = copy.deepcopy(current_req)
                        #         permd_req["queries"][key] = type_of_value
                        #         new_switched_points = current_switched_points + [f"{key}_{key_value_pair.index(type_of_value_original)+1}_value"]


                        #         future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                        #         future_to_request[future] = (permd_req, new_switched_points)

                        #         stack.append((permd_req, new_switched_points))
                        
                        
                        json_obj, escaped_or_unescaped = process_and_load_json(value)
                        if json_obj != None:
                        
                            tried_body_keys = list()
                            for index, variation in enumerate(generate_value_variations(json_obj, current_switched_points, perform_delete_keys, id_limited)):
                                key_for_output = "--key--".join(list_different_values(json_obj, variation))
                        
                                last_key = key_for_output.split("--key--")[-1]
        
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
    
                                new_switched_points = current_switched_points + [f"--key--{key_for_output}--key--{index}_value"]
                                permd_req = copy.deepcopy(perm_req)
                                permd_req["queries"][key] = json_string
                                # status_code = get_status_code_and_resb(permd_req, new_switched_points)
                                # status_codes_and_variation.append({"status_code": status_code, "permd_req": permd_req})
    
                                # if status_code and 200 <= status_code < 300:
                                #     return status_codes_and_variation
    
                                log_file = open("logfile.log", "a")
                                log_file.write(f"before generate_req_variations cajkljlll in here 1\n")
                                log_file.close()
                                future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                                future_to_request[future] = (permd_req, new_switched_points)

                                log_file = open("logfile.log", "a")
                                log_file.write(f"after generate_req_varjkljliations call in here 2\n")
                                log_file.close()
                                stack.append((permd_req, new_switched_points))
    
                       
                            # for index, variation in enumerate(key_deletion_variations(json_obj, current_switched_points, perform_delete_keys)):
                            #     key_for_output = ".".join(list_different_values(json_obj, variation))
                            #     if escaped_or_unescaped == 0:
                            #         json_string = json.dumps(variation)
                            #     elif escaped_or_unescaped == 1:
                            #         json_string = escape_json(variation)
                            #     elif escaped_or_unescaped == 2:
                            #         json_string = encode_json_with_url_encoding(variation)
                            #     elif escaped_or_unescaped == 3:
                            #         json_string = encode_base64(variation)
    
                            #     new_switched_points = current_switched_points + [f"{key_for_output}_{index}_value"]
                            #     permd_req = copy.deepcopy(perm_req)
                            #     permd_req["queries"][key] = json_string
                            #     # status_code = get_status_code_and_resb(permd_req, new_switched_points)
                            #     # status_codes_and_variation.append({"status_code": status_code, "permd_req": permd_req})
    
                            #     # if status_code and 200 <= status_code < 300:
                            #     #     return status_codes_and_variation
    
                            #     future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                            #     future_to_request[future] = (permd_req, new_switched_points)

                            #     stack.append((permd_req, new_switched_points))
                    
                    # if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2 and current_req.get("queries"):
                    #     queries_keys = get_all_keys(current_req.get("queries"))
                    #     for item in all_unique_sets(queries_keys):
                    #         permd_req = copy.deepcopy(current_req)
                    #         for i in range(0, len(item)):
                    #             del permd_req["queries"][item[i]]
                            
                    #         new_switched_points = current_switched_points + [f"{key}_deleted"]
                    #         future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                    #         future_to_request[future] = (permd_req, new_switched_points)
                    #         stack.append((permd_req, new_switched_points))
                    
                    # if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:
                    #     key_to_delete = []
                    #     while True:
                    #         log_file = open("logfile.log", "a")
                    #         log_file.write(f"before fjdlsjflksdjfkldsjfklsdjfklsdjfl call in here 1\n")
                    #         log_file.close()
                    #         permd_req = copy.deepcopy(current_req)
                    #         if key_to_delete:
                    #             for key in key_to_delete:
                    #                 del permd_req["queries"][key]
                    #                 # permd_req["queries"].pop(key, None)

                    #         #     avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                    #         # else:
                    #         avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                    #         std = max(1, std)
                            
                    #         break_out_of_loop = False
                    #         restart_loop = False
                    #         for key, value in (copy.deepcopy(permd_req.get("queries")) or {}).items():
                    #             del permd_req["queries"][key]
                    #             # permd_req["queries"].pop(key, None)
                    #             new_switched_points = current_switched_points + [f"{key}_deleted"]
                    #             log_file = open("logfile.log", "a")
                    #             log_file.write(f"before generate_req_variations call in perform_delete_keys 11\n")
                    #             log_file.close()
                    #             res = get_status_code_and_resb(permd_req, new_switched_points, True)
                    #             log_file = open("logfile.log", "a")
                    #             log_file.write(f"after generate_req_variations call in perform_delete_keys 222\n")
                    #             log_file.close()
                    #             if not res:
                    #                 continue
                    #             if res['resb']:
                    #                 new_length = len(str(res['resb']))
                    #             else:
                    #                 new_length = 0
                                
                    #             k_std = std + len(key)
                    #             if not (res['status_code'] >= 200 and res['status_code'] < 300):
                    #                 if is_length_unusual(new_length, avg, std_dev=k_std, tolerance=1):
                    #                     key_to_delete.append(key)
                    #                     stack.append((permd_req, new_switched_points))
                    #                     fake_future = Future()
                    #                     fake_future.set_result(res)
                    #                     future_to_request[fake_future] = (permd_req, new_switched_points)
                    #                     restart_loop = True
                    #                     break
                    #             else:
                    #                 log_file = open("logfile.log", "a")
                    #                 log_file.write(f"key_to_delete2 permd_req: {permd_req}\n")
                    #                 log_file.close()

                    #                 stack.append((permd_req, new_switched_points))
                    #                 fake_future = Future()
                    #                 fake_future.set_result(res)
                    #                 future_to_request[fake_future] = (permd_req, new_switched_points)
                    #                 break_out_of_loop = True
                    #                 break

                    #         if break_out_of_loop:
                    #             break

                    #         if restart_loop:
                    #             continue
                            
                    #         if break_out_of_loop == False and restart_loop == False:
                    #             break


                            # future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                            # future_to_request[future] = (permd_req, new_switched_points)
                            # stack.append((permd_req, new_switched_points))

                       
                    # if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:
                    #     key_to_delete = []
                    #     while True:
                    #         log_file = open("logfile.log", "a")
                    #         log_file.write(f"before aaaaaaaaaaaaaaaaa call in here 1\n")
                    #         log_file.close()
                    #         permd_req = copy.deepcopy(current_req)
                    #         if key_to_delete:
                    #             for key in key_to_delete:
                    #                 del permd_req["queries"][key]
                    #                 # permd_req["queries"].pop(key, None)

                    #         #     avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                    #         # else:
                    #         avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                    #         std = max(1, std)
                            
                    #         break_out_of_loop = False
                    #         restart_loop = False
                    #         for key, value in (copy.deepcopy(permd_req.get("queries")) or {}).items():
                    #             del permd_req["queries"][key]
                    #             # permd_req["queries"].pop(key, None)
                    #             new_switched_points = current_switched_points + [f"{key}_deleted"]
                    #             log_file = open("logfile.log", "a")
                    #             log_file.write(f"before generate_req_variations call in peddddddddddddrform_delete_keys 11\n")
                    #             log_file.close()
                    #             res = get_status_code_and_resb(permd_req, new_switched_points, True)
                    #             log_file = open("logfile.log", "a")
                    #             log_file.write(f"after generate_req_variations call in perfoddffffffffffffffrm_delete_keys 222\n")
                    #             log_file.close()
                    #             if not res:
                    #                 continue
                    #             if res['resb']:
                    #                 new_length = len(str(res['resb']))
                    #             else:
                    #                 new_length = 0
                                
                    #             k_std = std + len(key)
                    #             if res['status_code'] and not (res['status_code'] >= 200 and res['status_code'] < 300) and (res['resb'] and key in str(res['resb'])):
                    #                 if is_length_unusual(new_length, avg, std_dev=k_std, tolerance=1):
                    #                     key_to_delete.append(key)
                    #                     stack.append((permd_req, new_switched_points))
                    #                     fake_future = Future()
                    #                     fake_future.set_result(res)
                    #                     future_to_request[fake_future] = (permd_req, new_switched_points)
                    #                     restart_loop = True
                    #                     break
                    #             elif res['status_code'] and res['status_code'] >= 200 and res['status_code'] < 300:
                    #                 log_file = open("logfile.log", "a")
                    #                 log_file.write(f"key_to_delete2 permd_req: {permd_req}\n")
                    #                 log_file.close()

                    #                 stack.append((permd_req, new_switched_points))
                    #                 fake_future = Future()
                    #                 fake_future.set_result(res)
                    #                 future_to_request[fake_future] = (permd_req, new_switched_points)
                    #                 break_out_of_loop = True
                    #                 break

                    #         if break_out_of_loop:
                    #             break

                    #         if restart_loop:
                    #             continue
                            
                    #         if break_out_of_loop == False and restart_loop == False:
                    #             break


                            # future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                            # future_to_request[future] = (permd_req, new_switched_points)
                            # stack.append((permd_req, new_switched_points))


                    if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:
                        key_to_delete = []
                        while True:
                            
                            log_file = open("logfile.log", "a")
                            log_file.write(f"befodddddre fjdlsjflksdjfkldsjfklsdjfklsdjfl call in hfdsfsdfere 1\n")
                            log_file.close()

                            permd_req = copy.deepcopy(current_req)
                            if key_to_delete:
                                for key in key_to_delete:
                                    del permd_req["queries"][key]
                                    # permd_req["queries"].pop(key, None)

                            #     avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                            # else:
                            # avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                            # std = max(1, std)

                            while True:
                                main_res = get_status_code_and_resb(permd_req, current_switched_points, True)
                                if main_res and main_res['resb']:
                                    break
                            
                            # log_file = open("logfile.log", "a")
                            # log_file.write(f"avg: {avg}, std: {std}, status_std: {status_std}\n")
                            # log_file.close()

                            break_out_of_loop = False
                            restart_loop = False
                            for key, value in (copy.deepcopy(permd_req.get("queries")) or {}).items():
                                if key not in str(main_res['resb']):
                                    continue
                                
                                del permd_req["queries"][key]
                                # permd_req["queries"].pop(key, None)
                                new_switched_points = current_switched_points + [f"--key--{key}--key--deleted"]

                                log_file = open("logfile.log", "a")
                                log_file.write(f"befsdfsore generate_req_variations call in perform_delete_keys 11\n")
                                log_file.close()

                                while True:
                                    res = get_status_code_and_resb(permd_req, new_switched_points, True)
                                    if res and res['resb']:
                                        break
                            

                                log_file = open("logfile.log", "a")
                                log_file.write(f"aftessssssr generate_req_variations call in perfoddddrm_delete_keys 222 {str(permd_req)}\n")
                                log_file.write(f"affffffffffter generate_req_variations call in perfoddddrm_delete_keys 222 {str(res)}\n")
                                log_file.close()

                                # if not res:
                                #     continue
                                # if res['resb']:
                                #     new_length = len(str(res['resb']))
                                # else:
                                #     new_length = 0
                                
                                # k_std = std + len(key)
                                
                                # successful request detection here!! detect them by searching 200 number or smtn
                                if (res['resb'] and key not in str(res['resb'])) and not (res['status_code'] and res['status_code'] >= 200 and res['status_code'] < 300):
                                    # if is_length_unusual(new_length, avg, std_dev=k_std, tolerance=1):
                                    log_file = open("logfile.log", "a")
                                    log_file.write(f"start key_ttttttttto_delete1: {key_to_delete} {permd_req}\n")
                                    log_file.close()
                                    key_to_delete.append(key)

                                    stack.append((permd_req, new_switched_points))
                                    fake_future = Future()
                                    fake_future.set_result(res)
                                    future_to_request[fake_future] = (permd_req, new_switched_points)

                                    restart_loop = True
                                    log_file = open("logfile.log", "a")
                                    log_file.write(f"end keeeeeeey_to_delete1: {key_to_delete}\n")
                                    log_file.close()
                                    break
                                elif res['status_code'] and res['status_code'] >= 200 and res['status_code'] < 300:
                                    log_file = open("logfile.log", "a")
                                    log_file.write(f" key_to_delete222222 persssmd_req: {permd_req}\n")
                                    log_file.close()

                                    log_file = open("logfile.log", "a")
                                    log_file.write(f"staaaaaaart keeeeeey_to_delete2: {key_to_delete}\n")
                                    log_file.close()

                                    stack.append((permd_req, new_switched_points))
                                    fake_future = Future()
                                    fake_future.set_result(res)
                                    future_to_request[fake_future] = (permd_req, new_switched_points)

                                    break_out_of_loop = True
                                    log_file = open("logfile.log", "a")
                                    log_file.write(f"enddddddd key_to_delete2: {key_to_delete}\n")
                                    log_file.close()

                                    break

                            if break_out_of_loop:
                                break

                            if restart_loop:
                                continue

                            if break_out_of_loop == False and restart_loop == False:
                                break

                       
                    log_file = open("logfile.log", "a")
                    log_file.write(f"after fuzzing queries: {injection_point_count}\n")
                    log_file.close()
                    
                    # Fuzzing body
                    if current_req["body"]:

                        # log_file = open("logfile.log", "a")
                        # log_file.write(f"has entered here 1 \n")
                        # log_file.close()
                        # if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:
                        #     log_file = open("logfile.log", "a")
                        #     log_file.write(f"has enterfsdfsdfsded here 22222 \n")
                        #     log_file.close()

                        #     bodies_keys = get_all_keys(current_req.get("body"))

                        #     log_file = open("logfile.log", "a")
                        #     log_file.write(f"hafdsfsdfs entered here 22222 bodies_keys: {bodies_keys} \n")
                        #     log_file.close()

                        #     log_file = open("logfile.log", "a")
                        #     log_file.write(f"hafdsfsdfs entered here 22222 len(bodies_keys): {len(bodies_keys)} \n")
                        #     log_file.close()

                        #     all_keys = all_unique_sets(bodies_keys)

                        #     for keys in all_keys:
                        #         permd_req = copy.deepcopy(current_req)
                        #         for i in range(0, len(keys)):
                        #             del permd_req["body"][keys[i]]

                        #         log_file = open("logfile.log", "a")
                        #         log_file.write(f"has entfdsfsdered here 22222 \n")
                        #         log_file.close()

                        #         new_switched_points = current_switched_points + [f"{key}_deleted"]
                        #         future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                        #         future_to_request[future] = (permd_req, new_switched_points)
                        #         stack.append((permd_req, new_switched_points))
                    
                        # log_file = open("logfile.log", "a")
                        # log_file.write(f"hssas entfdsfsdfered here 22222 \n")
                        # log_file.close()


                        # if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:
                        #     key_to_delete = []
                        #     while True:
                        #         log_file = open("logfile.log", "a")
                        #         log_file.write(f"before fjdlsjflksdjfkldsjfklsdjfklsdjfl call in here 1\n")
                        #         log_file.close()
                        #         permd_req = copy.deepcopy(current_req)
                        #         if key_to_delete:
                        #             for key in key_to_delete:
                        #                 del permd_req["body"][key]
                        #                 # permd_req["body"].pop(key, None)

                        #         #     avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                        #         # else:
                        #         avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                        #         std = max(1, std)
                                
                        #         log_file = open("logfile.log", "a")
                        #         log_file.write(f"avg: {avg}, std: {std}, status_std: {status_std}\n")
                        #         log_file.close()

                        #         break_out_of_loop = False
                        #         restart_loop = False
                        #         for key, value in (copy.deepcopy(permd_req.get("body")) or {}).items():
                        #             del permd_req["body"][key]
                        #             # permd_req["body"].pop(key, None)
                        #             new_switched_points = current_switched_points + [f"{key}_deleted"]
                        #             log_file = open("logfile.log", "a")
                        #             log_file.write(f"before generate_req_variations call in perform_delete_keys 11\n")
                        #             log_file.close()
                        #             res = get_status_code_and_resb(permd_req, new_switched_points, True)
                        #             log_file = open("logfile.log", "a")
                        #             log_file.write(f"after generate_req_variations call in perform_delete_keys 222\n")
                        #             log_file.close()
                        #             if not res:
                        #                 continue
                        #             if res['resb']:
                        #                 new_length = len(str(res['resb']))
                        #             else:
                        #                 new_length = 0
                                    
                        #             k_std = std + len(key)
                        #             if res['status_code'] and res['resb'] and not (res['status_code'] >= 200 and res['status_code'] < 300):
                        #                 if is_length_unusual(new_length, avg, std_dev=k_std, tolerance=1):
                        #                     log_file = open("logfile.log", "a")
                        #                     log_file.write(f"start key_to_delete1: {key_to_delete} {permd_req}\n")
                        #                     log_file.close()
                        #                     key_to_delete.append(key)
                        #                     stack.append((permd_req, new_switched_points))
                        #                     fake_future = Future()
                        #                     fake_future.set_result(res)
                        #                     future_to_request[fake_future] = (permd_req, new_switched_points)
                        #                     restart_loop = True
                        #                     log_file = open("logfile.log", "a")
                        #                     log_file.write(f"end key_to_delete1: {key_to_delete}\n")
                        #                     log_file.close()
                        #                     break
                        #             elif res['status_code'] and res['status_code'] >= 200 and res['status_code'] < 300:
                        #                 log_file = open("logfile.log", "a")
                        #                 log_file.write(f" key_to_delete2 permd_req: {permd_req}\n")
                        #                 log_file.close()

                        #                 log_file = open("logfile.log", "a")
                        #                 log_file.write(f"start key_to_delete2: {key_to_delete}\n")
                        #                 log_file.close()

                        #                 stack.append((permd_req, new_switched_points))
                        #                 fake_future = Future()
                        #                 fake_future.set_result(res)
                        #                 future_to_request[fake_future] = (permd_req, new_switched_points)
                        #                 break_out_of_loop = True
                        #                 log_file = open("logfile.log", "a")
                        #                 log_file.write(f"end key_to_delete2: {key_to_delete}\n")
                        #                 log_file.close()

                        #                 break

                        #         if break_out_of_loop:
                        #             break

                        #         if restart_loop:
                        #             continue

                        #         if break_out_of_loop == False and restart_loop == False:
                        #             break


                        if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:
                            key_to_delete = []
                            while True:
                                
                                log_file = open("logfile.log", "a")
                                log_file.write(f"before fjdlsjflksdjfkldsjfklsdjfklsdjfl call in hfdsfsdfere 1\n")
                                log_file.close()

                                permd_req = copy.deepcopy(current_req)
                                if key_to_delete:
                                    for key in key_to_delete:
                                        if "-idx-" in key:
                                            potentialy_dict_idx = key.split("-idx-")[0]
                                            potentialy_dict_key = key.split("-idx-")[1]
                                            del permd_req["body"][potentialy_dict_idx][potentialy_dict_key]
                                        else:
                                            del permd_req["body"][key]
                                        # permd_req["body"].pop(key, None)

                                #     avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                                # else:
                                # avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                                # std = max(1, std)

                                while True:
                                    main_res = get_status_code_and_resb(permd_req, current_switched_points, True)
                                    if main_res and main_res['resb']:
                                        break
                                
                                # log_file = open("logfile.log", "a")
                                # log_file.write(f"avg: {avg}, std: {std}, status_std: {status_std}\n")
                                # log_file.close()

                                break_out_of_loop = False
                                restart_loop = False
                                if isinstance(permd_req.get("body"), dict):
                                    for key, value in (copy.deepcopy(permd_req.get("body")) or {}).items():
                                        if key not in str(main_res['resb']):
                                            continue

                                        del permd_req["body"][key]
                                        # permd_req["body"].pop(key, None)
                                        new_switched_points = current_switched_points + [f"--key--{key}--key--deleted"]

                                        log_file = open("logfile.log", "a")
                                        log_file.write(f"before generate_req_variations call in perform_delete_keys 11\n")
                                        log_file.close()

                                        while True:
                                            res = get_status_code_and_resb(permd_req, new_switched_points, True)
                                            if res and res['resb']:
                                                break


                                        log_file = open("logfile.log", "a")
                                        log_file.write(f"after generate_req_variations call in perfoddddrm_delete_keys 222 {str(permd_req)}\n")
                                        log_file.write(f"after generate_req_variations call in perfoddddrm_delete_keys 222 {str(res)}\n")
                                        log_file.close()

                                        # if not res:
                                        #     continue
                                        # if res['resb']:
                                        #     new_length = len(str(res['resb']))
                                        # else:
                                        #     new_length = 0

                                        # k_std = std + len(key)

                                        # successful request detection here!! detect them by searching 200 number or smtn
                                        if (res['resb'] and key not in str(res['resb'])) and not (res['status_code'] and res['status_code'] >= 200 and res['status_code'] < 300):
                                            # if is_length_unusual(new_length, avg, std_dev=k_std, tolerance=1):
                                            log_file = open("logfile.log", "a")
                                            log_file.write(f"start key_to_delete1: {key_to_delete} {permd_req}\n")
                                            log_file.close()
                                            key_to_delete.append(key)

                                            stack.append((permd_req, new_switched_points))
                                            fake_future = Future()
                                            fake_future.set_result(res)
                                            future_to_request[fake_future] = (permd_req, new_switched_points)

                                            restart_loop = True
                                            log_file = open("logfile.log", "a")
                                            log_file.write(f"end key_to_delete1: {key_to_delete}\n")
                                            log_file.close()
                                            break
                                        elif res['status_code'] and res['status_code'] >= 200 and res['status_code'] < 300:
                                            log_file = open("logfile.log", "a")
                                            log_file.write(f" key_to_delete2 permd_req: {permd_req}\n")
                                            log_file.close()

                                            log_file = open("logfile.log", "a")
                                            log_file.write(f"start key_to_delete2: {key_to_delete}\n")
                                            log_file.close()

                                            stack.append((permd_req, new_switched_points))
                                            fake_future = Future()
                                            fake_future.set_result(res)
                                            future_to_request[fake_future] = (permd_req, new_switched_points)

                                            break_out_of_loop = True
                                            log_file = open("logfile.log", "a")
                                            log_file.write(f"end key_to_delete2: {key_to_delete}\n")
                                            log_file.close()

                                            break
                                elif isinstance(permd_req.get("body"), list):
                                    for potentialy_dict_idx in range(0, len(permd_req.get("body"))):
                                        potentialy_dict = permd_req["body"][potentialy_dict_idx]
                                        if not isinstance(potentialy_dict, dict):
                                            continue
                                        
                                        for key, value in (copy.deepcopy(potentialy_dict) or {}).items():
                                            if key not in str(main_res['resb']):
                                                continue

                                            del permd_req["body"][potentialy_dict_idx][key]
                                            # permd_req["body"].pop(key, None)
                                            new_switched_points = current_switched_points + [f"{potentialy_dict_idx}-idx--key--{key}--key--deleted"]

                                            log_file = open("logfile.log", "a")
                                            log_file.write(f"before generate_req_variations call in perform_delete_keys 11\n")
                                            log_file.close()

                                            while True:
                                                res = get_status_code_and_resb(permd_req, new_switched_points, True)
                                                if res and res['resb']:
                                                    break


                                            log_file = open("logfile.log", "a")
                                            log_file.write(f"after generate_req_variations call in perfoddddrm_delete_keys 222 {str(permd_req)}\n")
                                            log_file.write(f"after generate_req_variations call in perfoddddrm_delete_keys 222 {str(res)}\n")
                                            log_file.close()

                                            # if not res:
                                            #     continue
                                            # if res['resb']:
                                            #     new_length = len(str(res['resb']))
                                            # else:
                                            #     new_length = 0

                                            # k_std = std + len(key)

                                            # successful request detection here!! detect them by searching 200 number or smtn
                                            if (res['resb'] and key not in str(res['resb'])) and not (res['status_code'] and res['status_code'] >= 200 and res['status_code'] < 300):
                                                # if is_length_unusual(new_length, avg, std_dev=k_std, tolerance=1):
                                                log_file = open("logfile.log", "a")
                                                log_file.write(f"start key_to_delete1: {key_to_delete} {permd_req}\n")
                                                log_file.close()
                                                key_to_delete.append(f"{potentialy_dict_idx}-idx-{key}")

                                                stack.append((permd_req, new_switched_points))
                                                fake_future = Future()
                                                fake_future.set_result(res)
                                                future_to_request[fake_future] = (permd_req, new_switched_points)

                                                restart_loop = True
                                                log_file = open("logfile.log", "a")
                                                log_file.write(f"end key_to_delete1: {key_to_delete}\n")
                                                log_file.close()
                                                break
                                            elif res['status_code'] and res['status_code'] >= 200 and res['status_code'] < 300:
                                                log_file = open("logfile.log", "a")
                                                log_file.write(f" key_to_delete2 permd_req: {permd_req}\n")
                                                log_file.close()

                                                log_file = open("logfile.log", "a")
                                                log_file.write(f"start key_to_delete2: {key_to_delete}\n")
                                                log_file.close()

                                                stack.append((permd_req, new_switched_points))
                                                fake_future = Future()
                                                fake_future.set_result(res)
                                                future_to_request[fake_future] = (permd_req, new_switched_points)

                                                break_out_of_loop = True
                                                log_file = open("logfile.log", "a")
                                                log_file.write(f"end key_to_delete2: {key_to_delete}\n")
                                                log_file.close()

                                                break

                                if break_out_of_loop:
                                    break

                                if restart_loop:
                                    continue

                                if break_out_of_loop == False and restart_loop == False:
                                    break


                        tried_body_keys = list()
                        for index, variation in enumerate(generate_value_variations(current_req["body"], current_switched_points, perform_delete_keys, id_limited)):
                            # log_file = open("logfile.log", "a")
                            # log_file.write(f"has entered here 2 \n")
                            # log_file.close()
                            permd_req = copy.deepcopy(current_req)
                            permd_req["body"] = variation
                            key_for_output = "--key--".join(list_different_values(current_req["body"], variation))
                            
                            last_key = key_for_output.split("--key--")[-1]
        
                            if last_key in tried_body_keys:
                                continue
        
                            tried_body_keys.append(last_key)
                        
                            new_switched_points = current_switched_points + [f"--key--{key_for_output}--key--{index}_value"]
                            # status_code = get_status_code_and_resb(permd_req, new_switched_points)
                            # status_codes_and_variation.append({"status_code": status_code, "permd_req": permd_req})
                            
                            # if status_code and 200 <= status_code < 300:
                            #     return status_codes_and_variation

                            log_file = open("logfile.log", "a")
                            log_file.write(f"before generate_req_variations caljljlkjjll in fuzzing body 1\n")
                            log_file.close()
                            
                            future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                            future_to_request[future] = (permd_req, new_switched_points)

                            log_file = open("logfile.log", "a")
                            log_file.write(f"after generate_req_variations call in fuzzing bodjljy 2\n")
                            log_file.close()
                            
                            stack.append((permd_req, new_switched_points))

                            
                            # if perform_delete_keys and len(discovered_keys) > 0 and len(current_switched_points) < 2:
                            #     key_to_delete = ""
                            #     while True:
                            #         log_file = open("logfile.log", "a")
                            #         log_file.write(f"before fjdlsjflksdjfkldsjfklsdjfklsdjfl callllllllllll in here 1\n")
                            #         log_file.close()

                            #         permd_req = copy.deepcopy(current_req)
                            #         permd_req["body"] = variation

                            #         if key_to_delete:
                            #             del permd_req["body"][key_to_delete]
    
                            #             avg, std, status_std = measure_average_content_length(permd_req, current_switched_points)
                            #         else:
                            #             avg, std, status_std = measure_average_content_length(current_req, current_switched_points)
                                    
                            #         break_out_of_loop = False
                            #         restart_loop = False

                            #         for key, value in (copy.deepcopy(permd_req.get("body")) or {}).items():
                            #             del permd_req["body"][key]
                            #             new_switched_points = current_switched_points + [f"{key}_deleted"]

                            #             log_file = open("logfile.log", "a")
                            #             log_file.write(f"before generate_req_variations call in perform_delete_keys 11\n")
                            #             log_file.close()

                            #             res = get_status_code_and_resb(permd_req, new_switched_points)

                            #             log_file = open("logfile.log", "a")
                            #             log_file.write(f"after generate_req_variations call in perform_delete_keys 222\n")
                            #             log_file.close()

                            #             if not res:
                            #                 continue
                                        
                            #             if res['resb']:
                            #                 new_length = len(str(res['resb']))
                            #             else:
                            #                 new_length = 0
                            #             if res['status_code'] == status_std:
                            #                 if is_length_unusual(new_length, avg, std_dev=std, tolerance=1):
                            #                     key_to_delete = key
                            #                     fake_future = Future()
                            #                     fake_future.set_result(res)
                            #                     future_to_request[fake_future] = (permd_req, new_switched_points)
                            #                     restart_loop = True
                            #                     break
                            #             else:
                            #                 stack.append((permd_req, new_switched_points))
                            #                 fake_future = Future()
                            #                 fake_future.set_result(res)
                            #                 future_to_request[fake_future] = (permd_req, new_switched_points)
                            #                 break_out_of_loop = True
                            #                 break
    
                            #         if break_out_of_loop:
                            #             break
    
                            #         if restart_loop:
                            #             continue
    
                            #         if break_out_of_loop == False and restart_loop == False:
                            #             break

                        
                        # for index, variation in enumerate(key_deletion_variations(current_req["body"], current_switched_points, perform_delete_keys)):
                        #     # log_file = open("logfile.log", "a")
                        #     # log_file.write(f"has entered here 2 \n")
                        #     # log_file.close()
                        #     permd_req = copy.deepcopy(current_req)
                        #     permd_req["body"] = variation
                        #     key_for_output = ".".join(list_different_values(current_req["body"], variation))
                            
                        #     new_switched_points = current_switched_points + [f"{key_for_output}_{index}_value"]
                        #     # status_code = get_status_code_and_resb(permd_req, new_switched_points)
                        #     # status_codes_and_variation.append({"status_code": status_code, "permd_req": permd_req})
                            
                        #     # if status_code and 200 <= status_code < 300:
                        #     #     return status_codes_and_variation

                        #     future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                        #     future_to_request[future] = (permd_req, new_switched_points)

                        #     stack.append((permd_req, new_switched_points))
                        
                        if type(perm_req["body"]) is dict:
                            for key,value in perm_req["body"].items():

                                if args.avoid_keys and key in args.avoid_keys:
                                    continue
                                
                                json_obj, escaped_or_unescaped = process_and_load_json(value)
                                if json_obj != None:
                                
                                    tried_body_keys = list()
                                    for index, variation in enumerate(generate_value_variations(json_obj, current_switched_points, perform_delete_keys, id_limited)):
                                    
                                        key_for_output = "--key--".join(list_different_values(json_obj, variation))

                                        last_key = key_for_output.split("--key--")[-1]

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
                                        
                                        new_switched_points = current_switched_points + [f"--key--{key_for_output}--key--{index}_value"]
                                        permd_req = copy.deepcopy(perm_req)
                                        permd_req["body"][key] = json_string
                                        # status_code = get_status_code_and_resb(permd_req, new_switched_points)
                                        # status_codes_and_variation.append({"status_code": status_code, "permd_req": permd_req})
    
                                        # if status_code and 200 <= status_code < 300:
                                        #     return status_codes_and_variation
    
                                        log_file = open("logfile.log", "a")
                                        log_file.write(f"before generate_req_variations call in fuzzing bofdsssssssssdy 1\n")
                                        log_file.close()
                            
                                        future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                                        future_to_request[future] = (permd_req, new_switched_points)

                                        log_file = open("logfile.log", "a")
                                        log_file.write(f"before generate_req_variations call in fuzzing bfdafasdfasdfody 1\n")
                                        log_file.close()
                            
                                        stack.append((permd_req, new_switched_points))
    
                                    # for index, variation in enumerate(key_deletion_variations(json_obj, current_switched_points, perform_delete_keys)):
                                    
                                    #     key_for_output = ".".join(list_different_values(json_obj, variation))
                                    #     if escaped_or_unescaped == 0:
                                    #        json_string = json.dumps(variation)
                                    #     elif escaped_or_unescaped == 1:
                                    #         json_string = escape_json(variation)
                                    #     elif escaped_or_unescaped == 2:
                                    #         json_string = encode_json_with_url_encoding(variation)
                                    #     elif escaped_or_unescaped == 3:
                                    #         json_string = encode_base64(variation)
                                        
                                    #     new_switched_points = current_switched_points + [f"{key_for_output}_{index}_value"]
                                    #     permd_req = copy.deepcopy(perm_req)
                                    #     permd_req["body"][key] = json_string
                                    #     # status_code = get_status_code_and_resb(permd_req, new_switched_points)
                                    #     # status_codes_and_variation.append({"status_code": status_code, "permd_req": permd_req})
    
                                    #     # if status_code and 200 <= status_code < 300:
                                    #     #     return status_codes_and_variation
    
                                    #     future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                                    #     future_to_request[future] = (permd_req, new_switched_points)

                                    #     stack.append((permd_req, new_switched_points))
    
                        elif type(perm_req["body"]) is list:
                            for key in range(0, len(perm_req["body"])):
                                value = perm_req["body"][key]
                                json_obj, escaped_or_unescaped = process_and_load_json(value)
                                if json_obj != None:
                                    tried_body_keys = list()
                                    for index, variation in enumerate(generate_value_variations(json_obj, current_switched_points, perform_delete_keys, id_limited)):
                                    
                                        key_for_output = "--key--".join(list_different_values(json_obj, variation))
                                        last_key = key_for_output.split("--key--")[-1]

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
        
                                        new_switched_points = current_switched_points + [f"--key--{key_for_output}--key--{index}_value"]
                                        permd_req = copy.deepcopy(perm_req)
                                        permd_req["body"][key] = json_string
                                        # status_code = get_status_code_and_resb(permd_req, new_switched_points)
                                        # status_codes_and_variation.append({"status_code": status_code, "permd_req": permd_req})
    
                                        # if status_code and 200 <= status_code < 300:
                                        #     return status_codes_and_variation
    
                                        log_file = open("logfile.log", "a")
                                        log_file.write(f"before generate_req_variations call in fdasfasfafd body 1\n")
                                        log_file.close()
                            
                                        future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                                        future_to_request[future] = (permd_req, new_switched_points)

                                        log_file = open("logfile.log", "a")
                                        log_file.write(f"before generate_req_variations call in fuzzinfdsfasdfasdfasfdag body 1\n")
                                        log_file.close()
                            
                                        stack.append((permd_req, new_switched_points))
                   
                                    # for index, variation in enumerate(key_deletion_variations(json_obj, current_switched_points, perform_delete_keys)):
                                    
                                    #     key_for_output = ".".join(list_different_values(json_obj, variation))
                                    #     if escaped_or_unescaped == 0:
                                    #        json_string = json.dumps(variation)
                                    #     elif escaped_or_unescaped == 1:
                                    #         json_string = escape_json(variation)
                                    #     elif escaped_or_unescaped == 2:
                                    #         json_string = encode_json_with_url_encoding(variation)
                                    #     elif escaped_or_unescaped == 3:
                                    #         json_string = encode_base64(variation)
        
                                    #     new_switched_points = current_switched_points + [f"{key_for_output}_{index}_value"]
                                    #     permd_req = copy.deepcopy(perm_req)
                                    #     permd_req["body"][key] = json_string
                                    #     # status_code = get_status_code_and_resb(permd_req, new_switched_points)
                                    #     # status_codes_and_variation.append({"status_code": status_code, "permd_req": permd_req})
    
                                    #     # if status_code and 200 <= status_code < 300:
                                    #     #     return status_codes_and_variation
    
                                    #     future = executor.submit(get_status_code_and_resb, permd_req, new_switched_points)
                                    #     future_to_request[future] = (permd_req, new_switched_points)

                                    #     stack.append((permd_req, new_switched_points))
                   
                    log_file = open("logfile.log", "a")
                    log_file.write(f"after fuzzing body: {injection_point_count}\n")
                    log_file.close()
                    
                for future in as_completed(future_to_request):
                    permd_req, new_switched_points = future_to_request[future]
                    status_code_and_resb = future.result()
                    if not status_code_and_resb:
                        continue
                    
                    status_code = status_code_and_resb["status_code"]
                    resb = status_code_and_resb["resb"]
                    status_codes_and_variation.append({"status_code": status_code, "resb": resb, "permd_req": permd_req})

                    # if status_code and (200 <= status_code < 300 or status_code == 429):
                    #     for f in future_to_request:
                    #         f.cancel()

                    #     # log_file = open("logfile.log", "a")
                    #     # log_file.write(f"req: {req} start 1\n")
                    #     # log_file.write(f"status_codes_and_variation: {status_codes_and_variation}\n")
                    #     # log_file.close()


                    #     log_file = open("logfile.log", "a")
                    #     log_file.write(f"end of generate_req_variations 1\n")
                    #     log_file.close()

                    #     return status_codes_and_variation
            

            # log_file = open("logfile.log", "a")
            # log_file.write(f"req: {req} start 2\n")
            # log_file.write(f"status_codes_and_variation: {status_codes_and_variation}\n")
            # log_file.close()

            log_file = open("logfile.log", "a")
            log_file.write(f"end of generate_req_variations 2\n")
            log_file.close()

            return status_codes_and_variation

        def insert_injection_points(dict_or_list):
            log_file = open("logfile.log", "a")
            log_file.write(" inside insert_injection_points\n")
            log_file.close()

            dict_or_list = copy.deepcopy(dict_or_list)

            if type(dict_or_list) is dict:
                permd_dict_or_list = copy.deepcopy(dict_or_list)
                permd_dict_or_list["injectionpoint"] = ""
                yield permd_dict_or_list

                for key, value in dict_or_list.items():
                    # if args.avoid_keys and key in args.avoid_keys:
                    #     continue

                    if type(value) is dict or type(value) is list:
                        permd_dict_or_list = copy.deepcopy(dict_or_list)
                        permd_dict_or_list[key] = {"injectionpoint":""}
                        yield permd_dict_or_list

                        if value:
                            for variation in insert_injection_points(value):
                                permd_dict_or_list = copy.deepcopy(dict_or_list)
                                permd_dict_or_list[key] = variation
                                yield permd_dict_or_list


            elif type(dict_or_list) is list:
                permd_dict_or_list = copy.deepcopy(dict_or_list)
                permd_dict_or_list = {"injectionpoint":""}
                yield permd_dict_or_list

                for key in range(0, len(dict_or_list)):


                    value = dict_or_list[key]
                    if type(value) is dict or type(value) is list:
                        permd_dict_or_list = copy.deepcopy(dict_or_list)
                        permd_dict_or_list[key] = {"injectionpoint":""}
                        yield permd_dict_or_list

                        if value:
                            for variation in insert_injection_points(value):
                                permd_dict_or_list = copy.deepcopy(dict_or_list)
                                permd_dict_or_list[key] = variation
                                yield permd_dict_or_list
        
        def is_it_repeated_injection_point(injection_point):
            injection_points = []
            for ip in injection_point:
                if "subpath" in ip:
                    injection_points.append("_".join(ip.split("_")[:2]))
                else:
                    injection_points.append("_".join(ip.split("_")[:1]))
    
            return len(injection_points) != len(set(injection_points))
        

        all_switched_injection_points = list()
        def get_status_code_and_resb(perm_req, switched_injection_points, first_check=False):
            # return
            switched_injection_points.sort()
    
    
            # log_file = open("logfile.log", "a")
            # log_file.write(" reached here 2 \n")
            # log_file.close()
    
            if switched_injection_points not in all_switched_injection_points and is_it_repeated_injection_point(switched_injection_points) == False:
                all_switched_injection_points.append(switched_injection_points)
            else:
                return
    
    
            # log_file = open("logfile.log", "a")
            # log_file.write(" reached here 3 \n")
            # log_file.close()
    
            nonlocal req_signature
            # nonlocal status_code_429
            
            url = f"https://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"
            
            # log_file = open("logfile.log", "a")
            # log_file.write(str(counter.value) + " start 2\n")
            # log_file.close()
    
    
            # log_file = open("logfile.log", "a")
            # log_file.write(" reached here 4 \n")
            # log_file.close()
    
            if args.delay != None and idx_of_param % args.params_number == 0:
                time.sleep(args.delay)
            
            # log_file = open("logfile.log", "a")
            # log_file.write(str(counter.value) + " end 2\n")
            # log_file.close()
    
            with req_lock:
                # if args.request_file != None:
                #     if args.token_script != None:
                #         subprocess.run(f"python3 {args.token_script}", shell=True)
                    
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
            # log_file.write(" reached here 5 \n")
            # log_file.close()
    
            # log_file = open("logfile.log", "a")
            # log_file.write(str(counter.value) + " start 3\n")
            # log_file.close()
    
            if args.delay != None:
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
                    queries[key] = str(value).strip()
            
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
            
    
            def get_the_new_or_updated_key_and_its_value(d):
                if isinstance(d, dict):
                    for k, v in d.items():
                        if "PAYLOADDDD" in k:
                        
                            # log_file = open("logfile.log", "a")
                            # log_file.write(f"found payload pair: {k} {v}\n")
                            # log_file.close()
    
                            return {k:v}
                        if isinstance(v, dict) or isinstance(v, list):
                            payload = get_the_new_or_updated_key_and_its_value(v)
                            if payload:
                                return payload
                        else:
                            json_obj, escaped_or_unescaped = process_and_load_json(v)
                            if isinstance(json_obj, dict) or isinstance(json_obj, list):
                                payload = get_the_new_or_updated_key_and_its_value(json_obj)
                                if payload:
                                    return payload
    
                elif isinstance(d, list):
                    for v in d:
                        if isinstance(v, dict) or isinstance(v, list):
                            payload = get_the_new_or_updated_key_and_its_value(v)
                            if payload:
                                return payload
                        else:
                            json_obj, escaped_or_unescaped = process_and_load_json(v)
                            if isinstance(json_obj, dict) or isinstance(json_obj, list):
                                payload = get_the_new_or_updated_key_and_its_value(json_obj)
                                if payload:
                                    return payload
    
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
                # with status_code_lock:
                #     status_code_429 = status == 429
    
    
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
                content_type = str(perm_req["headers"].get("Content-Type"))
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
            
            # log_file = open("logfile.log", "a")
            # log_file.write(" reached here 6 \n")
            # log_file.close()

            output_path = f"./output/{prepend_to_output_paths}_{req_signature}_{'ANDDDD'.join(switched_injection_points)}"
            # if output_folder_name == "normal" and args.normal_directory == None:
            #     output_path = f"./output/normal/{req_signature}"
            # elif output_folder_name == "normal_checkup" and args.normal_directory == None:
            #     output_path = f"./output/normal/{req_signature}_checkup"
            # elif output_folder_name == "normal" and args.normal_directory != None:
            #     output_path = f"{args.normal_directory}/{req_signature}"
            # elif output_folder_name == "normal_checkup" and args.normal_directory != None:
            #     output_path = f"{args.normal_directory}/{req_signature}_checkup"
            # else:
            #     if last3c == False:
            #         # cmd.extend(f"--json -o ./output/{output_folder_name}/{req_signature}_{clean_filename(injection_point)}_{idx_of_param}.json".split(" "))
            #         output_path = f"./output/{output_folder_name}/{req_signature}_{clean_filename(injection_point)}_{idx_of_param}"
            #     else:
            #         # cmd.extend(f"--json -o ./output/{output_folder_name}/{req_signature}_{clean_filename(injection_point)}_last3c.json".split(" "))
            #         output_path = f"./output/{output_folder_name}/{req_signature}_{clean_filename(injection_point)}_last3c"
            
            # Set proxy
            # proxies_for_request = {
            #     'http': f'socks5h://{proxy}',
            #     'https': f'socks5h://{proxy}'
            # } if proxy != "self" else None
            
            proxies_for_request = {
                'http': proxy,
                'https': proxy
            } if proxy != "self" else None

            # log_file = open("logfile.log", "a")
            # log_file.write(str(counter.value) + " start 4\n")
            # log_file.close()
    
            requests_count = 0
            successful_request = False
    
            max_size_mb = 100
            max_size_bytes = max_size_mb * 1024 * 1024  # 100 MB in bytes
            chunk_size = 1024 * 1024  # 1 MB per chunk
    
            # if output_folder_name == 'queries' or output_folder_name == 'body':
    
            #     param_exists = does_the_parameter_exist(perm_req['method'], url, copy.deepcopy(headers), copy.deepcopy(queries), copy.deepcopy(body))
            #     # param_exists = False
            # else:
            #     param_exists = True
            
            # does_the_parameter_exist(perm_req['method'], url, copy.deepcopy(headers), copy.deepcopy(queries), copy.deepcopy(body))
            # print(output_path)
            # return
    
    
            
    
            while True:
                try:
                    binary_file = open(output_path + ".body", 'wb')
                    response = requests.request(
                        method=perm_req['method'],
                        url=url,
                        headers=headers,
                        # params=queries,  # Add query parameters to the URL
                        data=body,  # For form or raw body
                        timeout=30,  # Set a reasonable timeout
                        proxies=proxies_for_request,  # Proxy configuration
                        verify=False,  # Disable SSL verification like `-k` in feroxbuster
                        allow_redirects=True,  # Follow redirects if needed
                        stream=True  # Stream the response to read in chunks
                    )
                    
                    # save the response data
                    successful_request = True
                    total_size = 0
                    # Read response content in chunks and track the size
                    
                    # fcntl.flock(binary_file, fcntl.LOCK_EX)
                    
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        total_size += len(chunk)
                        if total_size > max_size_bytes:
                            print(f"Response exceeds {max_size_mb} MB, stopping download.")
                            break  # Break out of the chunk loop if size exceeds 100 MB
                        
                        binary_file.write(chunk)
                    
                    binary_file.close()
                    
                    break
                except Exception as e:
                    log_file = open("fuzz.log", "a")
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
                save_response_details(response, output_path)
            
            try:
                try:
                    return {"status_code": response.status_code, "resb": response.json(), "output_path": output_path}
                except Exception as e:
                    log_file = open("logfile.log", "a")
                    log_file.write(f"Error: {e} \n")
                    log_file.close()

                    return {"status_code": response.status_code, "resb": None, "output_path": output_path}
            except Exception as e:
                log_file = open("logfile.log", "a")
                log_file.write(f"Error: {e} \n")
                log_file.close()

                return {"status_code": None, "resb": None, "output_path": output_path}
                    

                
        
    
    

        # all_switched_injection_points = list()
        # def get_status_code_and_resb(perm_req, switched_injection_points, first_check=False):
        #     # if not first_check:
        #     #     switched_injection_points.sort()
        #     #     if switched_injection_points not in all_switched_injection_points and is_it_repeated_injection_point(switched_injection_points) == False:
        #     #         all_switched_injection_points.append(switched_injection_points)
        #     #     else:
        #     #         return
            

        #     log_file = open("logfile.log", "a")
        #     log_file.write(f"get_status_code_and_resb perm_req: {perm_req}\n")
        #     log_file.close()

        #     # nonlocal req_signature

        #     url = f"https://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"

        #     # log_file = open("logfile.log", "a")
        #     # log_file.write(str(counter.value) + " start 2\n")
        #     # log_file.close()
        #     if args.delay != None and idx_of_param % args.params_number == 0:
        #         time.sleep(args.delay)

        #     # log_file = open("logfile.log", "a")
        #     # log_file.write(str(counter.value) + " end 2\n")
        #     # log_file.close()
        #     with req_lock:
        #         if args.request_file != None:
        #             if args.params_number != None and args.token_expiration == None and args.token_script != None and idx_of_param % args.params_number == 0:
        #                 subprocess.run(f"python3 {args.token_script}", shell=True)

        #             # log_file = open("logfile.log", "a")
        #             # log_file.write(str(counter.value) + " start 5\n")
        #             # log_file.close()
        #             headers = extract_headers(args.request_file)
        #             queries = extract_query_parameters(args.request_file)
        #             # log_file = open("logfile.log", "a")
        #             # log_file.write(str(counter.value) + " mid 5\n")
        #             # log_file.close()

        #             # update_dict_with_matches(perm_req["queries"], queries)
        #             # update_dict_with_matches(perm_req["headers"], headers)


        #             if queries and perm_req["queries"]:
                    
        #                 update_dict_with_matches(perm_req["queries"], queries)
        #             # print("Before: ")
        #             # print("First: " + str(perm_req["headers"]))
        #             # print("Second: " + str(headers))

        #             if headers and perm_req["headers"]:
        #                 update_dict_with_matches(perm_req["headers"], headers)

        #             # log_file = open("logfile.log", "a")
        #             # log_file.write(str(counter.value) + " end 5\n")
        #             # log_file.close()

        #     # log_file = open("logfile.log", "a")
        #     # log_file.write(str(counter.value) + " start 3\n")
        #     # log_file.close()
        #     if args.delay != None and args.token_script != None and idx_of_param % args.params_number == 0 and args.token_expiration == None:
        #         time.sleep(args.delay)
        #     # log_file = open("logfile.log", "a")
        #     # log_file.write(str(counter.value) + " end 3\n")
        #     # log_file.close()
        #     # Add queries
        #     queries = None
        #     if perm_req["queries"]:
        #         queries = dict()
        #         for key, value in perm_req.get('queries', {}).items():
        #             # cmd.append("-Q")
        #             # cmd.append(f"{key}={value}")
        #             queries[key] = str(value).strip()
            

        #         url = add_query_params(url, queries)

        #     def sanitize_headers(headers):
        #         sanitized = {}
        #         for header_name, header_value in headers.items():
        #             try:
        #                 # Ensure header values are latin-1 compatible or URL-encode if needed
        #                 header_value.encode('latin-1')
        #                 sanitized[header_name] = header_value
        #             except UnicodeEncodeError:
        #                 # Fallback to URL-encoding for non-latin-1 characters
        #                 sanitized[header_name] = quote(header_value)
        #         return sanitized
        #     # Add headers
        #     headers = None
        #     if perm_req["headers"]:
        #         headers = dict()
        #         for header_name, header_info in perm_req.get('headers', {}).items():
        #             if header_name.lower() == "host":
        #                 continue

        #             header_value = ""
        #             if header_info['value'] != "":
        #                 header_value = " " + header_info['value']

        #             key_count = 0
        #             if 'params' in header_info.keys():
        #                 for key,value in header_info['params'].items():
        #                     key_count += 1
        #                     if key_count != len(header_info['params'].keys()):
        #                         header_value += f"{key}={value};"
        #                     else:
        #                         header_value += f"{key}={value}"

        #             # cmd.append("-H")
        #             # cmd.append(f"{header_name}:{header_value}")
        #             headers[header_name] = header_value.strip()

        #         headers = sanitize_headers(headers)

        #     # def get_the_new_or_updated_key_and_its_value(d):
        #     #     if isinstance(d, dict):
        #     #         for k, v in d.items():
        #     #             if "PAYLOADDDD" in k:
        #     #                 # log_file = open("logfile.log", "a")
        #     #                 # log_file.write(f"found payload pair: {k} {v}\n")
        #     #                 # log_file.close()
        #     #                 return {k:v}
        #     #             if isinstance(v, dict) or isinstance(v, list):
        #     #                 payload = get_the_new_or_updated_key_and_its_value(v)
        #     #                 if payload:
        #     #                     return payload
        #     #             else:
        #     #                 json_obj, escaped_or_unescaped = process_and_load_json(v)
        #     #                 if isinstance(json_obj, dict) or isinstance(json_obj, list):
        #     #                     payload = get_the_new_or_updated_key_and_its_value(json_obj)
        #     #                     if payload:
        #     #                         return payload
        #     #     elif isinstance(d, list):
        #     #         for v in d:
        #     #             if isinstance(v, dict) or isinstance(v, list):
        #     #                 payload = get_the_new_or_updated_key_and_its_value(v)
        #     #                 if payload:
        #     #                     return payload
        #     #             else:
        #     #                 json_obj, escaped_or_unescaped = process_and_load_json(v)
        #     #                 if isinstance(json_obj, dict) or isinstance(json_obj, list):
        #     #                     payload = get_the_new_or_updated_key_and_its_value(json_obj)
        #     #                     if payload:
        #     #                         return payload
            
        #     def build_multipart_form_data(form_data, content_type):
        #         """Builds a multipart/form-data body from a Python dictionary."""

        #         boundary = content_type.split("boundary=")[1]

        #         body = BytesIO()

        #         for name, value in form_data.items():
        #             if isinstance(value, dict) and 'filename' in value:
        #                 # This is a file
        #                 filename = value['filename']
        #                 content = value['content']
        #                 content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

        #                 body.write(f'{boundary}\r\n'.encode())
        #                 body.write(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode())
        #                 body.write(f'Content-Type: {content_type}\r\n\r\n'.encode())
        #                 body.write(content.encode())
        #                 body.write(b'\r\n')
        #             else:
        #                 # This is a regular form field
        #                 body.write(f'{boundary}\r\n'.encode())
        #                 body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        #                 body.write(f'{value}\r\n'.encode())

        #         # End boundary
        #         body.write(f'{boundary}--\r\n'.encode())

        #         return body.getvalue()

        #     def save_response_details(response, output_filename):
        #         # Detect if content is binary or text
        #         content_type = response.headers.get('Content-Type', 'unknown')
        #         binary_types = ['application/octet-stream', 'image/', 'audio/', 'video/']
        #         response_content = None
        #         try:
        #             # Check if content type is binary
        #             if any(binary_type in content_type for binary_type in binary_types):
        #                 # Write in binary mode
        #                 # print(f"Detected binary content ({content_type}), saving as binary.")
        #                 with open(output_filename + ".body", 'rb') as binary_file:
        #                     response_content = binary_file.read()
        #             else:
        #                 # Write in text mode
        #                 # print(f"Detected text content ({content_type}), saving as text.")
        #                 with open(output_filename + ".body", 'r', encoding=response.encoding if response.encoding else 'utf-8') as text_file:
        #                     response_content = text_file.read()
        #         except:
        #             pass
        #         # Default values for word count and line count
        #         word_count = None
        #         line_count = None
        #         content_length = None
        #         # If the content type indicates it's JSON, handle JSON specifically
        #         if response_content != None:
        #             if 'application/json' in content_type:
        #                 try:
        #                     json_data = response_content
        #                     # Flatten JSON and count keys and values as 'words'
        #                     word_count = len(json.dumps(json_data).split())  # Count keys and values as "words"
        #                     line_count = len(json.dumps(json_data, indent=2).splitlines())  # Pretty-print and count lines
        #                     content_length = response.headers.get('Content-Length', len(response_content.encode("utf-8")))
        #                     # word_count = len(json.dumps(json_data).split(" "))
        #                     # line_count = len(json.dumps(json_data).splitlines())
        #                 except json.JSONDecodeError:
        #                     word_count = 0
        #                     line_count = 0
        #             # If the content type indicates it's text-based, process as text
        #             elif 'text' in content_type:
        #                 # content = response_content
        #                 word_count = len(response_content.split(" "))
        #                 line_count = len(response_content.splitlines())
        #                 content_length = response.headers.get('Content-Length', len(response_content.encode("utf-8")))
        #             else:
        #                 # For binary content, don't count words or lines
        #                 # content = response_content
        #                 content_length = response.headers.get('Content-Length', len(response_content))

        #         # content_length = response.headers.get('Content-Length', None)
        #         # Get the HTTP status code
        #         status = response.status_code
        #         # Prepare the data for JSON output
        #         data = {
        #             "word_count": word_count,
        #             "line_count": line_count,
        #             "content_type": content_type,
        #             "content_length": content_length,
        #             "status": status
        #         }
        #         data = json.dumps(data)
        #         output_file = open(output_filename + '.json', 'w')
        #         fcntl.flock(output_file, fcntl.LOCK_EX)
        #         # with open(output_filename + '.json', 'a') as output_file:
        #         output_file.write(data)

        #         fcntl.flock(output_file, fcntl.LOCK_UN)
        #         output_file.close()
        #     # Add body if present
        #     body = None
        #     if perm_req.get('body'):
        #         content_type = str(perm_req["headers"].get("Content-Type"))
        #         if "json" in content_type.lower():

        #             # with open(f"./body_{req_signature}.txt", "w") as body:
        #             #     body.write(json.dumps(perm_req['body']))
        #             body = json.dumps(perm_req['body'])
        #         elif "x-www-form-urlencoded" in content_type.lower():
        #             # with open(f"./body_{req_signature}.txt", "w") as body:
        #             #     body.write(urllib.parse.urlencode(perm_req['body']))
        #             body = safe_urlencode(perm_req['body'])

        #         elif "multipart/form-data" in content_type.lower():
        #             # multipart_body = build_multipart_form_data(perm_req['body'], content_type)
        #             # with open(f"./body_{req_signature}.txt", "w") as body:
        #             #     body.write(multipart_body.decode())
        #             body = build_multipart_form_data(perm_req['body'], content_type)
        #     else:
        #         if perm_req['method'] != "GET" and perm_req['method'] != "DELETE":
        #             content_type = str(perm_req["headers"].get("Content-Type"))
        #             if content_type and "json" in content_type.lower():
        #                 body = "{}"




        #     # Set proxy

        #     # proxies_for_request = {
        #     #     'http': f'socks5h://{proxy}',
        #     #     'https': f'socks5h://{proxy}'
        #     # } if proxy != "self" else None

        #     proxies_for_request = {
        #         'http': proxy,
        #         'https': proxy
        #     } if proxy != "self" else None

        #     log_file = open("logfile.log", "a")
        #     log_file.write("get_status_code_and_resb start 4\n")
        #     log_file.close()

        #     requests_count = 0
        #     successful_request = False
        #     max_size_mb = 100
        #     max_size_bytes = max_size_mb * 1024 * 1024  # 100 MB in bytes
        #     chunk_size = 1024 * 1024  # 1 MB per chunk
        #     # while True:
        #     try:
        #         # binary_file = open(output_path + ".body", 'wb')
        #         response = requests.request(
        #             method=perm_req['method'],
        #             url=url,
        #             headers=headers,
        #             data=body,  # For form or raw body
        #             timeout=20,  # Set a reasonable timeout
        #             proxies=proxies_for_request,  # Proxy configuration
        #             verify=False,  # Disable SSL verification like `-k` in feroxbuster
        #             allow_redirects=True,  # Follow redirects if needed
        #             stream=True  # Stream the response to read in chunks
        #         )
        #         try:
        #             return {"status_code": response.status_code, "resb": response.json()}
        #         except Exception as e:
        #             log_file = open("logfile.log", "a")
        #             log_file.write(f"Error: {e} \n")
        #             log_file.close()
                    
        #             return {"status_code": response.status_code, "resb": None}
                
        #         # save the response data
        #         # total_size = 0
        #         # Read response content in chunks and track the size
        #         # fcntl.flock(binary_file, fcntl.LOCK_EX)
        #         # for chunk in response.iter_content(chunk_size=chunk_size):
        #         #     total_size += len(chunk)
        #         #     if total_size > max_size_bytes:
        #         #         print(f"Response exceeds {max_size_mb} MB, stopping download.")
        #         #         break  # Break out of the chunk loop if size exceeds 100 MB
        #         #     binary_file.write(chunk)
        #         # binary_file.close()
        #         # break
        #     except Exception as e:
        #         log_file = open("logfile.log", "a")
        #         log_file.write(f"Error: {e} \n")
        #         log_file.close()
        #         return {"status_code": None, "resb": None}

        #     log_file = open("logfile.log", "a")
        #     log_file.write("get_status_code_and_resb start 5\n")
        #     log_file.close()
            
        #             # if requests_count % 2 == 0:
        #             #     url = f"http://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"
        #             # else:
        #             #     url = f"https://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"


        #         # requests_count += 1
        #         # if requests_count == 3:
        #         #     break

        # def update_key_value_pair(target_dict, update_dict, req):
        #     for each_key_value_pair in update_dict:
        #         for key, value in each_key_value_pair.items():
        #             if isinstance(target_dict, dict):
        #                 for key_x, value_x in target_dict.items():
        #                     if isinstance(value_x, dict):

        #                         # log_file = open("logfile.log", "a")
        #                         # log_file.write(f"target_dict: {target_dict}\n")
        #                         # log_file.write(f"target_dict[key_x]: {target_dict[key_x]}\n")
        #                         # log_file.write(f"req: {req}\n")
        #                         # log_file.close()

        #                         update_key_value_pair(target_dict[key_x], update_dict)
        #                     elif isinstance(value_x, list) and any(isinstance(item, dict) for item in value_x):
        #                         update_key_value_pair(target_dict[key_x], update_dict)
        #                     else:
        #                         if same_shit_different_story(key_x, key):
        #                             target_dict[key_x] = copy.deepcopy(value)
        #             elif isinstance(target_dict, list):
        #                 for key_x in range(0, len(target_dict)):
        #                     if isinstance(target_dict[key_x], dict):
        #                         update_key_value_pair(target_dict[key_x], update_dict)
        
        def update_key_value_pair(target_dict, update_dict):
            stack = [(target_dict, update_dict)]  # Initialize a stack with the root dictionary

            while stack:
                current_dict, current_update = stack.pop()

                # log_file = open("logfile.log", "a")
                # log_file.write(f"stack: {stack}\n")
                # log_file.write(f"current_dict: {current_dict}\n")
                # log_file.close()

                # for each_key_value_pair in current_update:
                #     for key, value in each_key_value_pair.items():
                if isinstance(current_dict, dict):
                    for key_x, value_x in current_dict.items():
                        if args.avoid_keys and key_x in args.avoid_keys:
                            continue

                        if isinstance(value_x, dict):
                            stack.append((current_dict[key_x], current_update))
                        elif isinstance(value_x, list) and any(isinstance(item, dict) for item in value_x):
                            stack.append((current_dict[key_x], current_update))
                        else:
                            for key, value in ((k, v) for d in current_update for k, v in d.items()):

                                if args.avoid_keys and key in args.avoid_keys:
                                    continue

                                if same_shit_different_story(key_x, key, False, False):
                                # if key_x.lower() == key.lower():
                                    current_dict[key_x] = copy.deepcopy(value)
                                    if value:
                                        break
                            
                elif isinstance(current_dict, list):
                    for key_x in range(len(current_dict)):
                        if args.avoid_keys and key_x in args.avoid_keys:
                            continue

                        value_x = current_dict[key_x]

                        if isinstance(value_x, dict):
                            stack.append((current_dict[key_x], current_update))
                        elif isinstance(value_x, list) and any(isinstance(item, dict) for item in value_x):
                            stack.append((current_dict[key_x], current_update))
                        else:
                            for key, value in ((k, v) for d in current_update for k, v in d.items()):

                                if args.avoid_keys and key in args.avoid_keys:
                                    continue
                                
                                if same_shit_different_story(key_x, key, False, False):
                                # if key_x.lower() == key.lower():
                                    current_dict[key_x] = copy.deepcopy(value)
                                    if value:
                                        break

        prepend_to_output_paths = "user-req"
        def find_appropriate_values(this_req):

            nonlocal context_access_params
            nonlocal keys_of_context_access_params
            nonlocal values_of_context_access_params
            nonlocal prepend_to_output_paths


            # log_file = open("logfile.log", "a")
            # log_file.write(f"reached here 17\n")
            # log_file.close()


            # rota_proc = subprocess.Popen(
            #     ["rota", "--config", "/home/deus/documents/rota_config.yml"],
            #     stdout=subprocess.DEVNULL,
            #     stderr=subprocess.DEVNULL,
            #     preexec_fn=os.setsid
            # )

            # time.sleep(5)

            with req_lock:
                if args.request_file != None:
                    if args.params_number != None and args.token_expiration == None and args.token_script != None and idx_of_param % args.params_number == 0:
                        subprocess.run(f"python3 {args.token_script}", shell=True)

                    headers = extract_headers(args.request_file)
                    queries = extract_query_parameters(args.request_file)

                    # update_dict_with_matches(req["queries"], queries)
                    # update_dict_with_matches(req["headers"], headers)


                    if queries and this_req["queries"]:
                    
                        update_dict_with_matches(this_req["queries"], queries)
                    # print("Before: ")
                    # print("First: " + str(perm_req["headers"]))
                    # print("Second: " + str(headers))

                    if headers and this_req["headers"]:
                        update_dict_with_matches(this_req["headers"], headers)
            

            log_file = open("logfile.log", "a")
            log_file.write(f"before execution of get_status_code_and_resb \n")
            log_file.close()
            
            origin_req = get_status_code_and_resb(this_req, [], True)
            

            log_file = open("logfile.log", "a")
            log_file.write(f"after execution of get_status_code_and_resb \n")
            log_file.close()
            
            
            origin_req["permd_req"] = this_req

            # if status_code and (200 <= status_code < 300):
            #     return origin_req
            
            reqs_variations = [origin_req]

            # if args.parameter_length:
            #     return reqs_variations


            # log_file = open("logfile.log", "a")
            # log_file.write(f"reached here 19\n")
            # log_file.close()

            reqs_variations.extend(generate_req_variations(this_req, [], True, True))
            reqs_variations.extend(generate_req_variations(this_req, [], True, False))

            if this_req['queries']:
                update_key_value_pair(this_req['queries'], key_value_pair)
                update_key_value_pair(this_req['queries'], context_access_params)
            
            if this_req['body']:
                update_key_value_pair(this_req['body'], key_value_pair)
                update_key_value_pair(this_req['body'], context_access_params)
            
            context_access_params = context_non_variation_access_params
            keys_of_context_access_params = keys_of_context_non_variation_access_params
            values_of_context_access_params = values_of_context_non_variation_access_params
            
            prepend_to_output_paths = "attacker-req"

            reqs_variations.extend(generate_req_variations(this_req, [], True, True))
            reqs_variations.extend(generate_req_variations(this_req, [], True, False))

            # log_file = open("logfile.log", "a")
            # log_file.write(f"reqs_variations: {reqs_variations}\n")
            # log_file.close()
            
            # for getting the ones with the highest number of keys in the case of failure of successful (2xx) request
            sorted_reqs_variation_1 = sorted(
                reqs_variations,
                key=lambda x: (
                    -(len(get_all_keys(x["permd_req"]["queries"])) if isinstance(x["permd_req"]["queries"], dict) else 0) - 
                    (len(get_all_keys(x["permd_req"]["body"])) if isinstance(x["permd_req"]["body"], dict) or isinstance(x["permd_req"]["body"], list) else 0),  # Boolean: False (0) for other status codes, True (1) for 400
                     x.get("status_code") if isinstance(x.get("status_code"), int) else 999,  # Boolean: False (0) for other status codes, True (1) for 400
                    -(len(x.get("resb")) if isinstance(x.get("resb"), Sized) else 0),
                    x["status_code"] is None,
                )
            )
            # for getting the ones with a successful (2xx) request when a parameter is causing a failure of request and it needs a proper value
            sorted_reqs_variation_2 = sorted(
                reqs_variations,
                key=lambda x: (
                    x["status_code"] is None,
                    x["status_code"] == 400,  # Boolean: False (0) for other status codes, True (1) for 400
                    x["status_code"],  # Boolean: False (0) for other status codes, True (1) for 400
                    -(len(get_all_keys(x["permd_req"]["queries"])) if isinstance(x["permd_req"]["queries"], dict) else 0) - 
                    (len(get_all_keys(x["permd_req"]["body"])) if isinstance(x["permd_req"]["body"], dict) or isinstance(x["permd_req"]["body"], list) else 0),  # Boolean: False (0) for other status codes, True (1) for 400
                    -(len(x.get("resb")) if isinstance(x.get("resb"), Sized) else 0)  # Sort actual status codes normally
                )
            )


            if sorted_reqs_variation_1[0] == sorted_reqs_variation_2[0]:
                sorted_reqs_variations = [sorted_reqs_variation_1[0]]
            else:

                sorted_reqs_variations = [sorted_reqs_variation_1[0], sorted_reqs_variation_2[0]]

            log_file = open("logfile.log", "a")
            log_file.write(f"req: {req}\n")
            joined_variations = '\n'.join(map(str, reqs_variations))
            log_file.write(f"reqs_variations: {joined_variations}\n")
            log_file.close()

            # try:
            # if sorted_reqs_variations[0]["status_code"] == origin_req["status_code"]:
            #     return origin_req
            # else:

            # os.killpg(os.getpgid(rota_proc.pid), signal.SIGKILL)
            # # Reap the zombie
            # try:
            #     rota_proc.wait(timeout=5)
            # except Exception:
            #     pass


            for req_with_its_appropriate_values in sorted_reqs_variations:
                # checking if it's successful request by checking if it has 2xx status code. add a boolean that tells if parameter length was put for this request
                # if not isinstance(req_with_its_appropriate_values["status_code"], int) or not (req_with_its_appropriate_values["status_code"] >= 200 and req_with_its_appropriate_values["status_code"] < 300):
                
                # if isinstance(req_with_its_appropriate_values["status_code"], int) and req_with_its_appropriate_values["status_code"] >= 200 and req_with_its_appropriate_values["status_code"] < 300:
                #     with bac_reqs_and_their_signatures_lock:
                #         with open(f'successful_output_paths_{paths_output_count}.txt', 'a+') as successful_output_paths:
                #             existing_lines = set(f.readlines())
                #             line_to_add = f"{json.dumps(req_with_its_appropriate_values['output_path'])}\n"
                #             if line_to_add not in existing_lines:
                #                 successful_output_paths.write(line_to_add)
                
                if f"req_{reqs.index(req)}" not in list(reqs_variations_for_context.keys()):
                    reqs_variations_for_context[f"req_{reqs.index(req)}"] = manager.list()
                
                reqs_variations_for_context[f"req_{reqs.index(req)}"].append(convert_to_manager_obj(req_with_its_appropriate_values, manager))


            return sorted_reqs_variations
        

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
            # fcntl.flock(output_file, fcntl.LOCK_EX)
            # with open(output_filename + '.json', 'a') as output_file:
            output_file.write(data)
            
            # fcntl.flock(output_file, fcntl.LOCK_UN)
            output_file.close()


        # Add body if present
        
        # log_file = open("logfile.log", "a")
        # log_file.write(str(counter.value) + " start 4\n")
        # log_file.close()

        args.avoid_keys = list()
        if perm_req.get('body'):
            args.avoid_keys.extend(get_all_keys(perm_req.get('body')))
        
        if perm_req.get('queries'):
            args.avoid_keys.extend(get_all_keys(perm_req.get('queries')))

        # if part_to_be_enumed == 'queries' or part_to_be_enumed == 'body':
        # discovered_req = False
        content_type = str(perm_req["headers"].get("Content-Type"))

        context_variations = dict()
        context_access_params = list()
        context_non_variation_access_params = list()
        values_of_context_access_params = list()


        log_file = open("logfile.log", "a")
        log_file.write(f"before loop_count: {loop_count}. req: {reqs.index(req)}\n")
        log_file.close()
        
        # if loop_count == 0 or args.find_appropriate_values_only:
        #     return

        url = f"https://{req['headers']['Host']['value'].strip()}{req['path'].strip()}"

        if req["queries"]:
            queries = dict()
            for key, value in req.get('queries', {}).items():
                queries[key] = str(value).strip()

            url = add_query_params(url, queries)
        
        for c_url in get_same_context_urls(url):
            c_path = urlparse(c_url).path
        
            for a_req in reqs:
                if a_req['path'] == c_path:
                    idx = reqs.index(a_req)
                    if f"req_{idx}" in list(reqs_variations_for_context.keys()):
                        context_variations[f"req_{idx}"] = convert_from_manager_obj(reqs_variations_for_context[f"req_{idx}"])
                    
                    if a_req['queries']:
                        context_non_variation_access_params.extend(get_all_keys_with_their_value(a_req['queries']))
        
                    if a_req['body']:
                        context_non_variation_access_params.extend(get_all_keys_with_their_value(a_req['body']))
        
        for key, values in context_variations.items():
            # if type(value) is str:
            #     continue
            
            for value in values:
                context_access_params.extend(get_all_keys_with_their_value(value["resb"]))
        
        
        # key_counts = manager.dict()
        # seen_values = manager.dict()
        
        # # log_file = open("context_access_params_0.json", "w")
        # # log_file.write(json.dumps(context_access_params))
        # # log_file.close()

        # filtered_data = list(map(filter_keys, context_access_params, repeat(key_counts)))
        # # Remove empty dictionaries and reassign to context_access_params
        # filtered_data = [d for d in filtered_data if d is not None]
        # context_access_params = filtered_data
        
        # # Second filtering step: remove duplicate values per key
        # filtered_data = list(map(filter_duplicates, context_access_params, repeat(seen_values)))
        
        # # Remove empty dictionaries and reassign to context_access_params
        # filtered_data = [d for d in filtered_data if d is not None]
        # context_access_params = filtered_data

        def canonicalize(obj):
            """
            Turn obj into a hashable form where order doesn't matter.
            - Lists/tuples -> frozenset of canonicalized items
            - Dicts       -> frozenset of (key, canonicalized(value)) pairs
            - Everything else left as-is
            """
            if isinstance(obj, dict):
                return frozenset((k, canonicalize(v)) for k, v in obj.items())
            elif isinstance(obj, (list, tuple, set, frozenset)):
                return frozenset(canonicalize(x) for x in obj)
            else:
                return obj
        
        def filter_duplicates_2(d, seen_values):
            new_dict = {}
            for key, value in d.items():
                h = canonicalize(value)   # hashable & order-independent
                if key not in seen_values:
                    seen_values[key] = set()
                if h not in seen_values[key]:
                    seen_values[key].add(h)
                    new_dict[key] = value  # keep the original structure
            return new_dict or None
        
        # Example usage
        seen_values = {}  # ordinary dict of sets
        filtered_data = list(map(filter_duplicates_2, context_access_params, repeat(seen_values)))
        filtered_data = [d for d in filtered_data if d is not None]
        context_access_params = filtered_data

        filtered_data = list(map(filter_duplicates_2, context_non_variation_access_params, repeat(seen_values)))
        filtered_data = [d for d in filtered_data if d is not None]
        context_non_variation_access_params = filtered_data

        
        log_file = open("logfile.log", "a")
        log_file.write(f"after loop_count: {loop_count}. req: {reqs.index(req)}\n")
        log_file.close()

        keys_of_context_access_params = set(get_all_keys(context_access_params))
        # with open(f"{req_signature}_wordlists_to_be_used.txt", 'w') as wordlists_to_be_used_file:
        #     for key in keys_of_context_access_params:
        #         wordlists_to_be_used_file.write(f"{key}\n")

        keys_of_context_non_variation_access_params = set(get_all_keys(context_non_variation_access_params))

        # values_of_context_access_params_temp = list(get_all_values_including_dict_and_list(context_access_params))
        values_of_context_access_params = list()
        values_of_context_non_variation_access_params = list()
        # for value_of_context_access_param in values_of_context_access_params_temp:
        #     if type(value_of_context_access_param) is dict or type(value_of_context_access_param) is list:
        #         value_of_context_access_param = json.dumps(value_of_context_access_param).replace(" ","")

        #     if value_of_context_access_param not in values_of_context_access_params:
        #         values_of_context_access_params.append(value_of_context_access_param)
        
        for t, entries in most_common_keys_values_by_type(context_access_params, 2).items():
            if entries:
                for key, value in entries:
                    if type(value) is dict or type(value) is list:
                        value = json.dumps(value).replace(" ","")
                    if value not in values_of_context_access_params:
                        values_of_context_access_params.append(value)
                
        for t, entries in most_common_keys_values_by_type(context_non_variation_access_params, 2).items():
            if entries:
                for key, value in entries:
                    if type(value) is dict or type(value) is list:
                        value = json.dumps(value).replace(" ","")
                    if value not in values_of_context_non_variation_access_params:
                        values_of_context_non_variation_access_params.append(value)
                
        
        # with open(f"{req_signature}_values_for_x8.txt", 'w') as query_parameters_file:
        #     for value in values_of_context_access_params:
        #         query_parameters_file.write(f"{value}\n")

        # with open(f"{req_signature}_key_value_pair_for_x8.json", 'w') as key_value_pair_for_x8_file:
        #     key_value_pair_for_x8_file.write(json.dumps(context_access_params))
        
        injection_point_count = 0
        if req['queries']:
            injection_point_count += len(get_all_keys(req['queries']))
        
        if req['body']:
            injection_point_count += len(get_all_keys(req['body']))

        find_appropriate_values(copy.deepcopy(req))
        
        # for req_with_its_appropriate_values in find_appropriate_values(copy.deepcopy(req)):
        #     if args.stop_at_success and req_with_its_appropriate_values and req_with_its_appropriate_values["status_code"] and req_with_its_appropriate_values["status_code"] >= 200 and req_with_its_appropriate_values["status_code"] < 300:
        #         return
        
        
        
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
    
    # path_for_signature = ""
    # unidentified_subpath = 0
    # for subpath in req["path"].split("/"):
    #     if search_string_in_directory("/usr/share/seclists/Discovery/Web-Content/raft-large", subpath) and not subpath.isdigit():
    #         path_for_signature += subpath + "/"
    #     else:
    #         unidentified_subpath += 1
    
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

    req_unhashed_signature = ""
    if args.consider_key != None:
        req_unhashed_signature = f'{get_nested_value(req,args.consider_key)}_{req["headers"]["Host"]["value"]}_{req["method"]}_{req["path"]}_{"_".join(get_all_keys(req))}'
    else:
        req_unhashed_signature = f'{req["headers"]["Host"]["value"]}_{req["method"]}_{req["path"]}_{"_".join(get_all_keys(req))}'
    
    
    req_signature = ""
    with req_number.get_lock():
        req_number.value += 1
        req_signature = str(req_number.value) + str(generate_md5(req_unhashed_signature))
    
    with bac_reqs_and_their_signatures_lock:
        with open(f'bac_reqs_and_their_signatures.jsonl', 'a+') as f:
            existing_lines = set(f.readlines())
            req_and_req_sign = {"req": req, "req_signature": req_signature}
            line_to_add = f"{json.dumps(req_and_req_sign)}\n"
            if line_to_add not in existing_lines:
                f.write(line_to_add)

    # if req['method'] == "GET" or args.force_query_enum:
    #     permd_req = copy.deepcopy(req)
    #     run_feroxbuster(permd_req, "queries")
    
    # log_file = open("logfile.log", "a")
    # log_file.write(str(counter.value) + " end of queries and start of headers\n")
    # log_file.close()
    
    # headers
    # if req['method'] == "POST" or req['method'] == "PUT" or req['method'] == "PATCH":
    # permd_req = copy.deepcopy(req)
    # run_feroxbuster(permd_req, "headers")
    
    # log_file = open("logfile.log", "a")
    # log_file.write(str(counter.value) + " end of headers and start of body\n")
    # log_file.close()

    # body
    # if req['method'] == "POST" or req['method'] == "PUT" or req['method'] == "PATCH":
    permd_req = copy.deepcopy(req)
    run_feroxbuster(permd_req, "body")

        
    # log_file = open("logfile.log", "a")
    # log_file.write(str(counter.value) + " about to remove proxy\n")
    # log_file.close()
    # if args.rate_limit == None:




    # with proxy_setting_lock:
    #     used_proxies_across_processes.remove(proxy)



    
        # log_file = open("logfile.log", "a")
        # log_file.write(f" removed {proxy} \n")
        # log_file.close()

    # log_file = open("logfile.log", "a")
    # log_file.write(str(counter.value) + " removed proxy\n")
    # log_file.close()

    # print("Finished " + str(counter.value) + "/" + str(requests_len) + "\n")

    # log_file = open("logfile.log", "a")
    # log_file.write(f"out {reqs.index(req)}: {req} \n")
    # log_file.close()

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


def comma_separated_naming_conventions(value):
    values = value.split(",")  # Split input string by commas
    valid_choices = {"snake_case", "camelCase", "PascalCase", "kebab-case"}  # Define valid choices

    # Validate that all values are in the allowed choices
    invalid_choices = [v for v in values if v not in valid_choices]
    if invalid_choices:
        raise argparse.ArgumentTypeError(f"Invalid choices: {', '.join(invalid_choices)}. Allowed: snake_case, camelCase, PascalCase, kebab-case")
    
    return values

parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument("-r", "--request-file", required=False, help="Path to the request file containing headers.")
parser.add_argument("-rc", "--rate-config", required=False, help="Path to the rate config.")
parser.add_argument("-rsl", "--requests-list", required=False, help="obtain requests out of a list of reqs json")
parser.add_argument("-a", "--avoid-path", required=False, help="Filter this path or a path that has the input path (deny list) (ex: -a /logout,/deleteuser )")
parser.add_argument('-rl', '--rate-limit', required=False, type=int, help='Limit number of instances to create for handling a request')
parser.add_argument('-cc', '--concurrency', required=False, type=int, help='Limit number of requests per url for x8')
parser.add_argument('-np', '--no-proxy', action='store_true', help='don\'t use proxies and instead use the server ip')
parser.add_argument('-ado', '--allow-delete-operations', action='store_true', help='don\'t use proxies and instead use the server ip')
parser.add_argument('-pn', '--params-number', type=int, required=False, help='number of params supplied per updating req.txt for like new authorization keys')
parser.add_argument('-ts', '--token-script', required=False, help='a python script to execute to generate new authorization keys')
parser.add_argument('-te', '--token-expiration', type=int, required=False, help='executes token script everytime token expiration time in minutes is reached')
parser.add_argument('-H', '--header', required=False, help='a header to add all requests like -H "X-Hackerone: seudxs"')
parser.add_argument('-w', '--wordlist', required=False, help='wordlist to include in parameter check')
parser.add_argument('-v', '--values', required=False, help='values to include in parameters values')
parser.add_argument('-d', '--delay', type=int, required=False, help='delay in seconds between --params-number requests')
parser.add_argument('-dp', '--depth', type=int, required=False, help='for how deep should it look for nested object')
parser.add_argument("-nd", "--normal-directory", required=False, help="other account's normal output directory to check against the main output directory for shared injection point value")
parser.add_argument("-ck", "--consider-key", required=False, help="a key to consider in request identifying through hashing like body.operationName")
parser.add_argument('-ump', '--use-more-param', action='store_true', help='use common param wordlists')
parser.add_argument('-ee', '--extract-exit', action='store_true', help='extract params and exit')
parser.add_argument('-ipi', '--injection-points-iteration', action='store_true', help='iterate over the body and attempt to find parameters at different objects and lists of the obdy')
parser.add_argument('-ak', '--avoid-keys', action='store_true', required=False, help='will not attempt to find appropriate values for the supplied keys, supplied keys must be comma-separated')
parser.add_argument('-iorp', '--include-other-reqs-params', action='store_true', help='use common param wordlists')
parser.add_argument('-i', '--invert', action='store_true', help='pass --invert to x8')
parser.add_argument('-sas', '--stop-at-success', action='store_true', help='do a full scan')
parser.add_argument('-fpo', '--first-phase-only', action='store_true', help='do the first phase only, which means no using extracted wordlist, it\'s faster')
parser.add_argument('-fapv', '--find-appropriate-values-only', action='store_true', help='finds opposite for testing BAC')
# parser.add_argument('-fqe', '--force-query-enum', action='store_true', help='do query enum regardless if the method is GET')
parser.add_argument('-ew', '--extract-wordlist', help='extract params from files in the given directory and its subdirectory')
parser.add_argument("-fs", "--filter-status", required=False, help="filter params that returned a specific status, multiple status can be with supplied comma-separated")
parser.add_argument("-fz", "--filter-size", required=False, help="filter params that returned a size within a range like 35000-36000, multiple ranges can be with supplied comma-separated")
parser.add_argument("-fsz", "--filter-status-and-size", required=False, help="filter params with specific status that returned a size within a range like 35000-36000, multiple ranges can be with supplied comma-separated")
# parser.add_argument('-ir', '--ignore-reflection', action='store_true', help='ignore paramsreflection')
parser.add_argument("-uf", "--urls-file", required=False, help="urls file to add in the search")
parser.add_argument("-kd", "--katana-directory", required=False, help="a directory that has the outputs of katana to parse as requests")
parser.add_argument("-kmhv", "--katana-match-host-value", required=False, help="test requests that are parsed from katana's output with matching host to this value")
parser.add_argument("-kihv", "--katana-in-host-value", required=False, help="test requests that are parsed from katana's output with host that contain this value")
parser.add_argument("-bp", "--burp-pair", required=False, help="get key-value pairs from burp file for using in when finding an appropriate value for matching param")
parser.add_argument("-up", "--urls-pair", required=False, help="get key-value pairs from urls file for using in when finding an appropriate value for matching param")
parser.add_argument("-kvp", "--key-value-pair", required=False, help="get key-value pairs from key value pair extracted json file for using in when finding an appropriate value for matching param")
parser.add_argument('-nc','--naming-convention', type=comma_separated_naming_conventions, required=False, help="Choose one or more naming conventions from: snake_case, camelCase, PascalCase, kebab-case (comma-separated)")
parser.add_argument("-rvc", "--remove-value-containing", required=False, help="remove value containing a specified string or character like { or ]. you can specify multiple of them comma-separated")
parser.add_argument("-pl", "--parameter-length", type=int, required=False, help="parameter length supplied to x8")
parser.add_argument("-m", "--max", type=int, required=False, help="max number of parameters per request supplied to x8")

args = parser.parse_args()



# proxies = []
# if args.no_proxy:
#     proxies.append("self")
# else:
#     proxies.append("http://127.0.0.1:8080")
    # if not args.rate_limit:
    #     with open('/home/deus/documents/proxies.txt') as proxy_file:
    #         for proxy in proxy_file:
    #             proxy = proxy.strip()
    #             if proxy != "":
    #                 proxy = proxy.split(':')
    #                 proxies.append(f"isp.smartproxy.com:{proxy[1]}")
    # else:
    #     available_proxies = list()
    #     with open('/home/deus/documents/proxies.txt') as proxy_file:
    #         for proxy in proxy_file:
    #             proxy = proxy.strip()
    #             if proxy != "":
    #                 proxy = proxy.split(':')
    #                 available_proxies.append(f"isp.smartproxy.com:{proxy[1]}")
        
    #     available_proxies_len = len(available_proxies)
        
    #     for i in range(0, args.rate_limit):
    #         proxies.append(available_proxies[i % available_proxies_len])


manager = multiprocessing.Manager()
used_proxies_across_processes = manager.list()
req_lock = multiprocessing.Lock()
signatures_and_their_data_lock = multiprocessing.Lock()
requests_with_special_needs_lock = multiprocessing.Lock()
proxy_setting_lock = multiprocessing.Lock()
x8_lock = multiprocessing.Lock()
param_file_lock = multiprocessing.Lock()
bac_reqs_and_their_signatures_lock = multiprocessing.Lock()
counter = multiprocessing.Value('i',1)
req_number = multiprocessing.Value('i',1)
params = manager.list()
list_of_reqs = manager.list()
reqs_variations_for_context = manager.dict()
subdirectories = []
key_value_pair = list()
keys_of_key_value_pair = set()

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

if (args.params_number == None and args.token_expiration == None) and args.token_script != None:
    print("params number argument not supplied")
    exit()

if args.params_number == None and args.delay != None:
    print("params number argument not supplied")
    exit()

if args.params_number != None and ((args.token_script == None and args.token_expiration == None) and args.delay == None):
    print("token script or delay argument not supplied")
    exit()

if args.token_expiration != None and args.token_script == None:
    print("token script argument not supplied")
    exit()
    
if args.extract_exit != False and args.depth == None:
    print("you gotta supply depth if you're not extracting")
    exit()

if args.avoid_path != None:
    args.avoid_path = args.avoid_path.lower().split(",")

if args.header != None:
    args.header = args.header.split(":")

if args.token_expiration != None:
    args.token_expiration = args.token_expiration * 60
    # token_loop()
    threading.Thread(target=token_loop, daemon=True).start()

if args.filter_status:
    args.filter_status = args.filter_status.split(",")

if args.filter_size:
    args.filter_size = args.filter_size.split(",")

if args.filter_status_and_size:
    args.filter_status_and_size = args.filter_status_and_size.split(",")

# if args.avoid_keys:
#     args.avoid_keys = args.avoid_keys.split(",")

if args.extract_wordlist:
    for dire in list_subdirectories_recursive(args.extract_wordlist):
        subdirectories.append(dire)

    pool = multiprocessing.Pool(12)
    pool.map(extract_params, subdirectories, chunksize=1)

    with open('extracted_param_wordlist.txt', 'a') as outfile:
        for param in params: 
            outfile.write(param + "\n")
    

    subprocess.run(
        ["sort", "-u", "-o", "extracted_param_wordlist.txt"],
        stdin=open("extracted_param_wordlist.txt", "r")
                    )

if args.extract_exit:
    exit()

if args.wordlist:
    params = set(params)
    with open(args.wordlist, 'r') as parameter_wordlist:
        for param in parameter_wordlist:
            param = param.strip()
            # if param not in params:
            params.add(param)
    
    params = list(params)


if args.remove_value_containing:
    args.remove_value_containing = args.remove_value_containing.split(",")

write_or_append = "w"
if args.values:
    vals = set()
    with open(args.values, 'r') as values_wordlist:
        for val in values_wordlist:
            val = val.strip()
            if not val:
                continue
            
            vals.add(val)
    
    with open("/home/deus/documents/values_for_x8.txt", 'w') as values_wordlist:
        for val in vals:
            if args.remove_value_containing and any(remove_value_containing in str(val) for remove_value_containing in args.remove_value_containing):
                continue
            
            values_wordlist.write(f"{val}\n")
    
    # with open("/home/deus/documents/values_for_body.txt", 'w') as values_wordlist:
    #     for val in vals:
    #         if args.remove_value_containing and any(remove_value_containing in str(val) for remove_value_containing in args.remove_value_containing):
    #             continue
            
    #         values_wordlist.write(f"{val}\n")
    
    write_or_append = "a"


default_vals = ["null","{}","[]","[{}]", "true", "1", "payload"]
with open("/home/deus/documents/values_for_x8.txt", write_or_append) as values_wordlist:
    for val in default_vals:
        if args.remove_value_containing and any(remove_value_containing in str(val) for remove_value_containing in args.remove_value_containing):
            continue

        values_wordlist.write(f"{val}\n")

# with open("/home/deus/documents/values_for_body.txt", write_or_append) as values_wordlist:
#     for val in default_vals:

#         if args.remove_value_containing and any(remove_value_containing in str(val) for remove_value_containing in args.remove_value_containing):
#             continue

#         values_wordlist.write(f"{val}\n")



unpack_burp_output = list()
if os.path.isdir('./input'):
    for burp_file in os.listdir('./input'):
        if os.path.exists("/home/deus/downloads"):
            subprocess.run(f"php /home/deus/downloads/unpack-burp/unpack-burp.php ./input/{burp_file} all > unpack_burp_output.txt", shell=True)
        else:
            subprocess.run(f"php /home/kali/Downloads/unpack-burp/unpack-burp.php ./input/{burp_file} all > unpack_burp_output.txt", shell=True)


        with open('unpack_burp_output.txt', 'r') as file:
            unpack_burp_output.extend(file.read().split("\n\n"))

divide_conc = 6

if args.concurrency:
    args.concurrency = int(args.concurrency / divide_conc)

if args.use_more_param:
    # params = set(params)
    with open('/home/deus/documents/sam-cc-parameters-mixedcase-all.txt') as samlist_params:
        for param in samlist_params:
            param = param.strip()
            if param not in params:
                params.append(param)
    
    # params = list(params)


new_params = list()
with multiprocessing.Pool(processes=4) as pool:
    results = pool.map(is_it_param, params)
    for i in range(0, len(results)):
        if results[i]:
            new_params.append(params[i])

params = new_params

if args.naming_convention:
    new_params = list()
    for param in params:
        
        for naming_convention in args.naming_convention:
            if naming_convention == "snake_case":

                new_param = humps.decamelize(humps.camelize(param))
                # new_params.add(new_param)

            elif naming_convention == "camelCase":

                new_param = humps.camelize(param)
                # new_params.add(new_param)

            elif naming_convention == "PascalCase":

                new_param = humps.pascalize(param)
                # new_params.add(new_param)

            elif naming_convention == "kebab-case":

                new_param = humps.kebabize(param)
                # new_params.add(new_param)
            
            if new_param not in new_params:
                new_params.add(new_param)
    
    params = new_params

# params = list(params))


reqs = list()

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
    

for request_and_response in unpack_burp_output:
    if request_and_response == '':
        continue

    request_and_response = json.loads(request_and_response)

    if args.avoid_path != None and any(avoid_path in request_and_response["reqp"].lower() for avoid_path in args.avoid_path):
        continue

    req_text = request_and_response["reqp"].replace("HTTP/2","HTTP/1.1") + "\r\n" + request_and_response["reqh"] + "\r\n\r\n" + request_and_response["reqb"]

    parsed_request = parse_http(req_text)
    if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
        try:
            parsed_request["resb"] = get_all_keys_with_their_value(json.loads(request_and_response["resb"]))
            if args.include_other_reqs_params:
                for param in get_all_keys(parsed_request["resb"]):
                    if param not in params:
                        params.append(param)
        except Exception as e:
            print(f"An ignored error occurred while parsing resb: {e}")
        if parsed_request["body"] and args.include_other_reqs_params:
            for param in get_all_keys(parsed_request["body"]):
                if param not in params:
                    params.append(param)
            
            # params.extend(get_all_keys_with_their_value(parsed_request["body"]))
        
        if parsed_request["queries"] and args.include_other_reqs_params:
            for param in get_all_keys(parsed_request["queries"]):
                if param not in params:
                    params.append(param)
            
            # params.extend(get_all_keys_with_their_value(parsed_request["queries"]))

        reqs.append(parsed_request)
    else:
        print(req_text)

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
            
            path = extract_path(url)

            if f"GET_{path}" in unique_reqs_check[hostname]:
                continue
            
            unique_reqs_check[hostname].append(f"GET_{path}")

            
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

# def key_count_in_key_value_pair(k):

#     # Count occurrences of each key
#     key_counts = Counter(key for d in key_value_pair for key in d.keys())

#     return key_counts[k]

if args.burp_pair:
    unpack_burp_output = list()
    # for burp_file in os.listdir('./input'):
    if os.path.exists("/home/deus/downloads"):
        subprocess.run(f"php /home/deus/scripts/unpack-burp/unpack-burp.php {args.burp_pair} all > unpack_burp_output.txt", shell=True)
    else:
        subprocess.run(f"php /home/kali/Downloads/unpack-burp/unpack-burp.php {args.burp_pair} all > unpack_burp_output.txt", shell=True)


    with open('unpack_burp_output.txt', 'r') as file:
        unpack_burp_output.extend(file.read().split("\n\n"))
    
    # random.shuffle(unpack_burp_output)
    for request_and_response in unpack_burp_output:
        if request_and_response == '':
            continue

        request_and_response = json.loads(request_and_response)

        if  args.avoid_path != None and any(avoid_path in request_and_response["reqp"].lower() for avoid_path in args.avoid_path):
            continue

        req_text = request_and_response["reqp"].replace("HTTP/2","HTTP/1.1") + "\r\n" + request_and_response["reqh"] + "\r\n\r\n" + request_and_response["reqb"]

        parsed_request = parse_http(req_text)
        if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
            try:
                parsed_request["resb"] = get_all_keys_with_their_value(json.loads(request_and_response["resb"]))
                # for pair in parsed_request["resb"]:
                #     if key_count_in_key_value_pair(list(pair.keys())[0]) < 4:
                #         key_value_pair.append(pair)
                
                key_value_pair.extend(parsed_request["resb"])

                # if args.include_other_reqs_params:
                #     for param in get_all_keys(parsed_request["resb"]):
                #         if param not in params:
                #             params.append(param)
                
            except Exception as e:
                print(f"An ignored error occurred while parsing resb: {e}")
                # pass
            if parsed_request["body"]:
                # for param in get_all_keys(parsed_request["body"]):
                #     if param not in params:
                #         params.append(param)
                # for pair in get_all_keys_with_their_value(parsed_request["body"]):
                #     if key_count_in_key_value_pair(list(pair.keys())[0]) < 4:
                #         key_value_pair.append(pair)
                
                key_value_pair.extend(get_all_keys_with_their_value(parsed_request["body"]))

            if parsed_request["queries"]:
                # for param in get_all_keys(parsed_request["queries"]):
                #     if param not in params:
                #         params.append(param)

                # for pair in get_all_keys_with_their_value(parsed_request["queries"]):
                #     if key_count_in_key_value_pair(list(pair.keys())[0]) < 4:
                #         key_value_pair.append(pair)

                key_value_pair.extend(get_all_keys_with_their_value(parsed_request["queries"]))
                print(get_all_keys_with_their_value(parsed_request["queries"]))
                print(parsed_request["queries"])

        else:
            print(f"failed checkup: {parsed_request}")
            print(f"failed checkup: {req_text}")
            # pass

# print(key_value_pair)
# exit()
def get_all_keys_with_their_value_of_urls(url):
    return get_all_keys_with_their_value(extract_query_parameters(url))

if args.urls_pair:
    urls_to_be_processed = list()
    with open(args.urls_pair, "r") as urls:
        for url in urls:
            url = url.strip()
            urls_to_be_processed.append(url)
        
        with multiprocessing.Pool(processes=4) as pool:
            results = pool.map(get_all_keys_with_their_value_of_urls, urls_to_be_processed)
            results = [item for sublist in results for item in sublist]
            key_value_pair.extend(results)

if args.key_value_pair:
    urls_to_be_processed = list()
    with open(args.key_value_pair, "r") as key_value_pair_json_file:
        for key_value_pair_i in key_value_pair_json_file:
            key_value_pair_i = key_value_pair_i.strip()
            key_value_pair_json = json.loads(key_value_pair_i)
            key_value_pair.append(key_value_pair_json)


# # Track occurrences of each key
# key_counts = defaultdict(int)

# # Filter data while ensuring no key appears more than twice
# filtered_data = []
# for d in key_value_pair:
#     new_dict = {}
#     for key, value in d.items():
#         if key_counts[key] < 3:  # Allow at most 2 occurrences
#             new_dict[key] = value
#             key_counts[key] += 1
#     if new_dict:  # Only keep non-empty dictionaries
#         filtered_data.append(new_dict)

# key_value_pair = filtered_data


# # Dictionary to track unique values for each key
# seen_values = defaultdict(list)
# filtered_data = []

# # Remove duplicate values per key
# for d in key_value_pair:
#     new_dict = {}
#     for key, value in d.items():
#         if value not in seen_values[key]:  # Keep only the first occurrence
#             seen_values[key].append(value)
#             new_dict[key] = value
#     if new_dict:  # Avoid adding empty dictionaries
#         filtered_data.append(new_dict)

# key_value_pair = filtered_data

def filter_keys(d, key_counts):
    new_dict = {}
    for key, value in d.items():
        # Get current count, defaulting to 0
        count = key_counts.get(key, 0)
        if count < 5:  # Allow at most 2 occurrences
            new_dict[key] = value
            key_counts[key] = count + 1
    return new_dict if new_dict else None

def filter_duplicates(d, seen_values):
    new_dict = {}
    for key, value in d.items():
        # Get list of seen values, defaulting to an empty list
        seen = seen_values.get(key, [])
        if value not in seen:  # Keep only the first occurrence
            seen.append(value)
            seen_values[key] = seen
            new_dict[key] = value
    return new_dict if new_dict else None

key_counts = manager.dict()
seen_values = manager.dict()

with multiprocessing.Pool(processes=4) as pool:
    filtered_data = pool.starmap(filter_keys, [(d, key_counts) for d in key_value_pair])
        
# Remove empty dictionaries and reassign to key_value_pair
filtered_data = [d for d in filtered_data if d is not None]
key_value_pair = filtered_data

# Second filtering step: remove duplicate values per key
with multiprocessing.Pool(processes=4) as pool:
    filtered_data = pool.starmap(filter_duplicates, [(d, seen_values) for d in key_value_pair])

# Remove empty dictionaries and reassign to key_value_pair
filtered_data = [d for d in filtered_data if d is not None]
key_value_pair = filtered_data

key_counts = manager.dict()
seen_values = manager.dict()

# print(key_value_pair)
keys_of_key_value_pair = set(get_all_keys(key_value_pair))
key_value_pair_len = len(key_value_pair)

key_value_pair_for_x8 = list()

for key_value in key_value_pair:
    val = list(key_value.values())[0]
    if args.remove_value_containing and any(remove_value_containing in str(val) for remove_value_containing in args.remove_value_containing):
        continue
    
    key_value_pair_for_x8.append(key_value)

# with open(f'key_value_pair_for_x8.json', 'w') as key_value_pair_for_x8_file:
#     key_value_pair_for_x8_file.write(json.dumps(key_value_pair_for_x8))

# with open('wordlists_to_be_used.txt', 'w') as param_wordlist:
#     for param in params:
#         param_wordlist.write(param + "\n")

paths_output_count = 0
for f_or_d in os.listdir('./'):
    if f"param_miner_output" in f_or_d:
        paths_output_count += 1


requests_len = len(reqs)

grouped_reqs = group_reqs_by_hostname(reqs)

loop_count = 0
last_reqs_variations_for_context_count = sum(len(v) for v in reqs_variations_for_context.values())

for i in range(0, 3):
    loop_count = i

    if not (loop_count == 0 or sum(len(v) for v in reqs_variations_for_context.values()) != last_reqs_variations_for_context_count):
        break
    
    if loop_count == 0:

        with open("./contextualize_access_urls.txt", 'w') as all_urls:
            for req in reqs:

                url = f"https://{req['headers']['Host']['value'].strip()}{req['path'].strip()}"

                if req["queries"]:
                    queries = dict()
                    for key, value in req.get('queries', {}).items():
                        queries[key] = str(value).strip()

                    url = add_query_params(url, queries)


                all_urls.write(f"{url}\n")

        subprocess.run(f"python3 /home/deus/scripts/contextualize_access.py -u ./contextualize_access_urls.txt", shell=True, executable="/bin/bash")
    else:
        with open("./contextualize_access_urls_and_its_keys.jsonl", 'w') as all_urls:
            for req_key, variations in reqs_variations_for_context.items():
                for variation in variations:
                    url = f"https://{variation['permd_req']['headers']['Host']['value'].strip()}{variation['permd_req']['path'].strip()}"

                    if variation['permd_req']["queries"]:
                        queries = dict()
                        for key, value in variation['permd_req'].get('queries', {}).items():
                            queries[key] = str(value).strip()

                        url = add_query_params(url, queries)
                    
                    contextualize_access_urls_and_its_keys_output = dict()
                    contextualize_access_urls_and_its_keys_output["url"] = url
                    contextualize_access_urls_and_its_keys_output["keys"] = list(set(get_all_keys(convert_from_manager_obj(variation['resb']))))

                    all_urls.write(f"{json.dumps(contextualize_access_urls_and_its_keys_output)}\n")

        subprocess.run(f"python3 /home/deus/scripts/contextualize_access.py -j ./contextualize_access_urls_and_its_keys.jsonl", shell=True, executable="/bin/bash")
    
    last_reqs_variations_for_context_count = sum(len(v) for v in reqs_variations_for_context.values())

    for hostname, l_reqs in grouped_reqs.items():
        requests_len = len(l_reqs)


        used_user_agents = set()
        proxies = []
        if args.no_proxy:
            proxies.append("self")
        else:
            port, rota_proc = get_proxy_port(hostname, args.concurrency, used_user_agents)
            proxies.append(f"127.0.0.1:{port}")
        
        print(f"here 1. hostname: {hostname}")
        # if loop_count != 0:
        #     sets_of_params = split_list(params, 10000)
            
        #     for set_of_params in sets_of_params:
        #         print(f"here 2. set_of_params idx: {sets_of_params.index(set_of_params)}")
        #         with open(f'key_value_pair_for_x8.json', 'w') as key_value_pair_for_x8_file:
        #             set_of_key_value_pair_for_x8 = []
        #             with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        #                 for result in pool.imap(filter_params, set_of_params):
        #                     set_of_key_value_pair_for_x8.append(result)

        #             key_value_pair_for_x8_file.write(json.dumps(set_of_key_value_pair_for_x8))
                
        #         print(f"here 5. set_of_params idx: {sets_of_params.index(set_of_params)}")
        #         with open('wordlists_to_be_used.txt', 'w') as param_wordlist:
        #             for param in set_of_params:
        #                 param_wordlist.write(param + "\n")
                
        #         print(f"here 6. set_of_params idx: {sets_of_params.index(set_of_params)}")
        #         pool = multiprocessing.Pool(len(proxies) * divide_conc)
        #         pool.map(permutate_and_send_request, l_reqs, chunksize=1)
        #         print(f"here 3. set_of_params idx: {sets_of_params.index(set_of_params)}")
        # else:
        counter.value = 1
        pool = multiprocessing.Pool(len(proxies) * divide_conc)
        pool.map(permutate_and_send_request, l_reqs, chunksize=1)

        print(f"here 4. hostname: {hostname}")

        if not args.no_proxy:
            rota_exit_handler(rota_proc)
    
    print(f"here 5. loop_count: {loop_count}")

# requests_len = len(reqs)
# pool = multiprocessing.Pool(len(proxies))
# pool.map(permutate_and_send_request, reqs, chunksize=1)

# if args.allow_delete_operations:
#     requests_len = len(delete_reqs)
#     pool = multiprocessing.Pool(len(proxies))
#     pool.map(permutate_and_send_request, delete_reqs, chunksize=1)

stop_event.set()


# with open(f'param_miner_output_{paths_output_count}.json', 'w') as param_miner_output:
#     param_miner_output.write(json.dumps(list(list_of_reqs)))


# with open(f'param_miner_successful_output_{paths_output_count}.json', 'w') as param_miner_output:
#     req_l = list()
#     for k, v in reqs_variations_for_context.items():
#         t = list(v)
#         req_l.append(t[len(t) - 1])
    
#     param_miner_output.write(json.dumps(req_l))

# for filename in glob.glob('endpoint_*.txt') + glob.glob('body_*.txt'):
#     os.remove(filename)