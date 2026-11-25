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
import fcntl
import base64
import shlex
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load the SBERT model
# os.environ["TOKENIZERS_PARALLELISM"] = "false"


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


def is_it_param(s):
    return bool(
        re.match(r"[a-zA-Z0-9._-]+", s)
    )

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

    subprocess.run(f"cd {dir} && ~/scripts/encoded_part_of_name_remover.sh", shell=True)
    files = os.listdir(dir)
    for file in files:
        if os.path.isfile(f"{dir}/{file}"):

            # log_file = open("another_logfile.log", "a")
            # log_file.write(f"{dir}/{file}\n")
            # log_file.close()
            subprocess.run(f"js-beautify {dir}/{file} | perl -nle 'print $1 if /\\b([a-zA-Z_][a-zA-Z0-9_]*)\\b(?=\\s*:)/' | sort -u | anew params_output_{subdirectories.index(dir)}_{files.index(file)}.txt", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            command_for_single_quote_separator = "awk -F\"'\" '{for (i=2; i<=NF; i+=2) print $i}'"
            subprocess.run(f"{command_for_single_quote_separator} {dir}/{file} | sort -u | anew params_output_{subdirectories.index(dir)}_{files.index(file)}.txt", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            command_for_double_quote_separator = """awk -F'"' '{for (i=2; i<=NF; i+=2) print $i}'"""
            subprocess.run(f"{command_for_double_quote_separator} {dir}/{file} | sort -u | anew params_output_{subdirectories.index(dir)}_{files.index(file)}.txt", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            command_for_backtick_quote_separator = """awk -F'`' '{for (i=2; i<=NF; i+=2) print $i}'"""
            subprocess.run(f"{command_for_backtick_quote_separator} {dir}/{file} | sort -u | anew params_output_{subdirectories.index(dir)}_{files.index(file)}.txt", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # retry_count = 0
            # while True:
            #     subprocess.run(f"js-beautify {dir}/{file} | perl -nle 'print $1 if /\\b([a-zA-Z_][a-zA-Z0-9_]*)\\b(?=\\s*:)/' | sort -u | anew params_output_{subdirectories.index(dir)}_{files.index(file)}.txt", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #     proc = subprocess.Popen(f"~/scripts/codestrings {dir}/{file} | tr ',' '\n' | tr -d '\"' | anew params_output_{subdirectories.index(dir)}_{files.index(file)}.txt", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            #     try:
            #         proc.wait(timeout=30)
            #         break
            #     except subprocess.TimeoutExpired:
            #         # Print the exception
            #         # print("An exception occurred:", e)
            #         kill_process_and_children(proc.pid)
            #         log_file = open("logfile.log", "a")
            #         log_file.write(f"process that's about to be killed: {proc.pid}\n")
            #         log_file.close()
            #         # proc.kill()
            #         # os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            #         retry_count += 1
            #         if retry_count == 2:
            #             break
                    
            if os.path.exists(f"params_output_{subdirectories.index(dir)}_{files.index(file)}.txt"):
                with open(f"params_output_{subdirectories.index(dir)}_{files.index(file)}.txt", "r") as params_file:
                    for param in params_file:
                        param = param.strip()
                        if is_it_param(param):

                            # log_file = open("another_logfile.log", "a")
                            # log_file.write(f"{param}\n")
                            # log_file.close()
                            if param not in params:
                                params.append(param)


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



def permutate_and_send_request(req):
    global victim_params
    global attacker_params
    global args
    global used_proxies_across_processes
    global proxies
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
    global prepend_to_output
    global ids_for_bac_on_constructed_reqs
    global collect_ids_for_bac_on_constructed_reqs

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
    with proxy_setting_lock:
        counter1 = Counter(proxies)
        counter2 = Counter(used_proxies_across_processes)
        result_counter = counter1 - counter2
        result = list(result_counter.elements())
        proxy = result[0]
        used_proxies_across_processes.append(proxy)
        
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

    # def get_params_with_interested_value(main_param):
    #     # print()
    #     # print("reached here 1")
    #     # print()
    #     main_param_with_spaces_as_its_separator = split_param(main_param)
    #     similar_params = []
    #     # print()
    #     # print("reached here 3")
    #     # print()

    #     # for word1 in main_param_with_spaces_as_its_separator:
    #     try:
    #         embedding1 = model.encode(main_param_with_spaces_as_its_separator, convert_to_tensor=True)
    #     except Exception as e:
    #         print(f"This error occurred: {e} while loading up: main_param_with_spaces_as_its_separator's value {main_param_with_spaces_as_its_separator}")

    #     # print()
    #     # print("reached here 4")
    #     # print()
    #     for param in params:

    #         if type(param) is dict:
    #             if main_param == list(param.keys())[0]:
    #                 continue
    #             param_with_spaces_as_its_separator = split_param(list(param.keys())[0])
    #             # print(f"value of list(param.keys())[0]: {list(param.keys())[0]}")
    #             # print(f"value of list(param.keys())[0]: {list(param.keys())[0]}")
    #         else:
    #             if main_param == param:
    #                 continue
    #             param_with_spaces_as_its_separator = split_param(param)
    #             # print(f"value of param: {param}")
    #         # exit()

    #         # for word2 in param_with_spaces_as_its_separator:
    #             # # similarity_after_converted_to_singular = max(model.get_word_vector(word1).dot(model.get_word_vector(word2)),model.get_word_vector(plural_to_singular(word1)).dot(model.get_word_vector(plural_to_singular(word2))))


    #         try:
    #             embedding2 = model.encode(param_with_spaces_as_its_separator, convert_to_tensor=True)
    #         except Exception as e:
    #             print(f"This error occurred: {e} while loading up: param_with_spaces_as_its_separator's value {param_with_spaces_as_its_separator} and the value of param is {param}")

    #         # similarity = max(model.get_word_vector(main_param_with_spaces_as_its_separator).dot(model.get_word_vector(param_with_spaces_as_its_separator)),model.get_word_vector(main_param_with_spaces_as_its_separator).dot(model.get_word_vector(param_with_spaces_as_its_separator)))
    #         similarity = util.cos_sim(embedding1, embedding2)
    #         similarity_num = round(similarity.item(), 1)

    #         if similarity_num >= 0.4:
    #             if param not in similar_params:
    #                 similar_params.append(param)

    #     return similar_params
    

    # def get_params_with_interested_value(params, interested_value):
    #     params_with_interested_value = list()
    #     if isinstance(params, dict):
    #         for k, v in params.items():
    #             if interested_value == v:
    #                 params_with_interested_value.append({k:v})
    #             if isinstance(v, dict) or isinstance(v, list):
    #                 payload = get_params_with_interested_value(v, interested_value)
    #                 if payload:
    #                     params_with_interested_value.extend(payload)
    #             else:
    #                 json_obj, escaped_or_unescaped = process_and_load_json(v)
    #                 if isinstance(json_obj, dict) or isinstance(json_obj, list):
    #                     payload = get_params_with_interested_value(json_obj, interested_value)
    #                     if payload:
    #                         params_with_interested_value.extend(payload)
    #     elif isinstance(params, list):
    #         for v in params:
    #             if isinstance(v, dict) or isinstance(v, list):
    #                 payload = get_params_with_interested_value(v, interested_value)
    #                 if payload:
    #                     params_with_interested_value.extend(payload)
    #             else:
    #                 json_obj, escaped_or_unescaped = process_and_load_json(v)
    #                 if isinstance(json_obj, dict) or isinstance(json_obj, list):
    #                     payload = get_params_with_interested_value(json_obj, interested_value)
    #                     if payload:
    #                         params_with_interested_value.extend(payload)

    #     return params_with_interested_value

    # def get_params_with_interested_param(params, interested_param):
    #     params_with_interested_param = list()
    #     if isinstance(params, dict):
    #         for k, v in params.items():
    #             if interested_param == k:
    #                 params_with_interested_param.append({k:v})
    #             if isinstance(v, dict) or isinstance(v, list):
    #                 payload = get_params_with_interested_param(v, interested_param)
    #                 if payload:
    #                     params_with_interested_param.extend(payload)
    #             else:
    #                 json_obj, escaped_or_unescaped = process_and_load_json(v)
    #                 if isinstance(json_obj, dict) or isinstance(json_obj, list):
    #                     payload = get_params_with_interested_param(json_obj, interested_param)
    #                     if payload:
    #                         params_with_interested_param.extend(payload)
    #     elif isinstance(params, list):
    #         for v in params:
    #             if isinstance(v, dict) or isinstance(v, list):
    #                 payload = get_params_with_interested_param(v, interested_param)
    #                 if payload:
    #                     params_with_interested_param.extend(payload)
    #             else:
    #                 json_obj, escaped_or_unescaped = process_and_load_json(v)
    #                 if isinstance(json_obj, dict) or isinstance(json_obj, list):
    #                     payload = get_params_with_interested_param(json_obj, interested_param)
    #                     if payload:
    #                         params_with_interested_param.extend(payload)

    #     return params_with_interested_param
    
    def process_params_with_interested_value(params, interested_value):
        """Processes parameters for the interested value."""
        results = []

        if isinstance(params, dict):
            for k, v in params.items():
                if interested_value == v:
                    results.append({k: v})
                if isinstance(v, (dict, list)):
                    results.extend(process_params_with_interested_value(v, interested_value))
                else:
                    json_obj, _ = process_and_load_json(v)
                    if isinstance(json_obj, (dict, list)):
                        results.extend(process_params_with_interested_value(json_obj, interested_value))
        elif isinstance(params, list):
            for v in params:
                if isinstance(v, (dict, list)):
                    results.extend(process_params_with_interested_value(v, interested_value))
                else:
                    json_obj, _ = process_and_load_json(v)
                    if isinstance(json_obj, (dict, list)):
                        results.extend(process_params_with_interested_value(json_obj, interested_value))

        return results

    def process_params_with_interested_param(params, interested_param):
        """Processes parameters for the interested parameter."""
        results = []

        if isinstance(params, dict):
            for k, v in params.items():
                if interested_param == k:
                    results.append({k: v})
                if isinstance(v, (dict, list)):
                    results.extend(process_params_with_interested_param(v, interested_param))
                else:
                    json_obj, _ = process_and_load_json(v)
                    if isinstance(json_obj, (dict, list)):
                        results.extend(process_params_with_interested_param(json_obj, interested_param))
        elif isinstance(params, list):
            for v in params:
                if isinstance(v, (dict, list)):
                    results.extend(process_params_with_interested_param(v, interested_param))
                else:
                    json_obj, _ = process_and_load_json(v)
                    if isinstance(json_obj, (dict, list)):
                        results.extend(process_params_with_interested_param(json_obj, interested_param))
        
        return results

    
    def get_attacker_values(victim_value):
        """Retrieves attacker values based on victim value using threading."""
        attacker_values = []

        # Step 1: Find interested victim parameters
        with ThreadPoolExecutor() as executor:
            future_to_victim = {
                executor.submit(process_params_with_interested_value, victim_params, victim_value): victim_value
            }
            for future in as_completed(future_to_victim):
                interested_victim_params = future.result()

        # Step 2: Extract victim keys and process attacker parameters
        victim_keys = get_all_keys(interested_victim_params)
        victim_keys = list(set(victim_keys))
        
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(process_params_with_interested_param, attacker_params, victim_key)
                for victim_key in victim_keys
            ]
            for future in as_completed(futures):
                attacker_param_group = future.result()
                for attacker_param in attacker_param_group:
                    if list(attacker_param.values())[0] not in attacker_values:
                        attacker_values.append(list(attacker_param.values())[0])

        # attacker_values = list(set(attacker_values))
        return attacker_values

    def generate_value_variations(dict_or_list):
        dict_or_list = copy.deepcopy(dict_or_list)
        nonlocal num_of_discovered_ids

        # two is the new one
        if len(switched_injection_points) == num_of_discovered_ids:
            return
            
        if type(dict_or_list) is dict:
            for key, value in dict_or_list.items():
                if type(value) is dict or type(value) is list:
                    
                    for variation in generate_value_variations(value):
                        permd_dict_or_list = copy.deepcopy(dict_or_list)
                        permd_dict_or_list[key] = variation
                        yield permd_dict_or_list
                elif type(value) is not str or (type(value) is str and " " not in value):
                    attacker_values = get_attacker_values(value)
                    for attacker_value in attacker_values:
                    # for attacker_value in get_attacker_values(value):

                        try:
                            attacker_value = type(value)(attacker_value)
                        except:
                            pass
                        
                        if attacker_value == value:
                            continue

                        permd_dict_or_list = copy.deepcopy(dict_or_list)

                        permd_dict_or_list[key] = attacker_value
                        yield permd_dict_or_list
        elif type(dict_or_list) is list:
            for key in range(0, len(dict_or_list)):
                value = dict_or_list[key]
                if type(value) is dict or type(value) is list:
                    
                    for variation in generate_value_variations(value):
                        permd_dict_or_list = copy.deepcopy(dict_or_list)
                        permd_dict_or_list[key] = variation
                        yield permd_dict_or_list
                elif type(value) is not str or (type(value) is str and " " not in value):
                    attacker_values = get_attacker_values(value)
                    for attacker_value in attacker_values:
                    # for attacker_value in get_attacker_values(value):

                        try:
                            attacker_value = type(value)(attacker_value)
                        except:
                            pass

                        if attacker_value == value:
                            continue
                        
                        permd_dict_or_list = copy.deepcopy(dict_or_list)

                        permd_dict_or_list[key] = attacker_value
                        yield permd_dict_or_list

    def generate_req_variations(perm_req, switched_injection_points):
        # status_codes_and_variation = []
        nonlocal num_of_discovered_ids
        stack = [(perm_req, switched_injection_points)]
        
        max_workers = 1
        if args.rate_limit:
            max_workers = args.rate_limit
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # Adjust workers as needed
            future_to_request = {}

            while stack:
                current_req, current_switched_points = stack.pop()

                if len(current_switched_points) >= (num_of_discovered_ids - 1):
                    continue

                # Fuzzing path
                subpaths = current_req["path"].split("/")
                for i, subpath in enumerate(subpaths):
                    if not subpath:
                        continue

                    attacker_values = get_attacker_values(subpath)
                    for attacker_value in attacker_values:
                        if attacker_value == subpath:
                            continue

                        permd_req = copy.deepcopy(current_req)
                        permd_req["path"] = permd_req["path"].replace(subpath, str(attacker_value))
                        new_switched_points = current_switched_points + [f"{i+1}_subpath_{attacker_values.index(attacker_value)+1}_value"]
                        executor.submit(run_feroxbuster, permd_req, new_switched_points)
                        
                        stack.append((permd_req, new_switched_points))

                # Fuzzing queries
                for key, value in (current_req.get("queries") or {}).items():
                    # if isinstance(value, str) and " " in value:
                    #     continue
                    attacker_values = get_attacker_values(subpath)
                    for attacker_value in attacker_values:
                        preserved_attacker_value = attacker_value
                        try:
                            attacker_value = type(value)(attacker_value)
                        except:
                            pass

                        if attacker_value == value:
                            continue

                        permd_req = copy.deepcopy(current_req)
                        permd_req["queries"][key] = attacker_value
                        new_switched_points = current_switched_points + [f"{key}_{attacker_values.index(preserved_attacker_value)+1}_value"]
                        executor.submit(run_feroxbuster, permd_req, new_switched_points)
                        
                        stack.append((permd_req, new_switched_points))

                    json_obj, escaped_or_unescaped = process_and_load_json(value)
                    if json_obj != None:
                        for index, variation in enumerate(generate_value_variations(json_obj)):
                            key_for_output = "_".join(list_different_values(json_obj, variation))
                            if escaped_or_unescaped == 0:
                                json_string = json.dumps(variation)
                            elif escaped_or_unescaped == 1:
                                json_string = escape_json(variation)
                            elif escaped_or_unescaped == 2:
                                json_string = encode_json_with_url_encoding(variation)
                            elif escaped_or_unescaped == 3:
                                json_string = encode_base64(variation)
                            new_switched_points = current_switched_points + [f"{key_for_output}_{index}_value"]
                            permd_req = copy.deepcopy(perm_req)
                            permd_req["queries"][key] = json_string
                            executor.submit(run_feroxbuster, permd_req, new_switched_points)
                            
                            stack.append((permd_req, new_switched_points))

                # Fuzzing body
                if current_req["body"]:
                    for index, variation in enumerate(generate_value_variations(current_req["body"])):
                        permd_req = copy.deepcopy(current_req)
                        permd_req["body"] = variation
                        key_for_output = "_".join(list_different_values(current_req["body"], variation))

                        new_switched_points = current_switched_points + [f"{key_for_output}_{index}_value"]
                        executor.submit(run_feroxbuster, permd_req, new_switched_points)

                        stack.append((permd_req, new_switched_points))

                    if type(perm_req["body"]) is dict:
                        for key,value in perm_req["body"].items():
                            json_obj, escaped_or_unescaped = process_and_load_json(value)
                            if json_obj != None:
                                for index, variation in enumerate(generate_value_variations(json_obj)):
                                    key_for_output = "_".join(list_different_values(json_obj, variation))
                                    if escaped_or_unescaped == 0:
                                       json_string = json.dumps(variation)
                                    elif escaped_or_unescaped == 1:
                                        json_string = escape_json(variation)
                                    elif escaped_or_unescaped == 2:
                                        json_string = encode_json_with_url_encoding(variation)
                                    elif escaped_or_unescaped == 3:
                                        json_string = encode_base64(variation)

                                    new_switched_points = current_switched_points + [f"{key_for_output}_{index}_value"]
                                    permd_req = copy.deepcopy(perm_req)
                                    permd_req["body"][key] = json_string
                                    executor.submit(run_feroxbuster, permd_req, new_switched_points)
                                    # status_codes_and_variation.append({"status_code": status_code, "permd_req": permd_req})
                                    # if status_code and 200 <= status_code < 300:
                                    #     return status_codes_and_variation
                                    # status_codes_and_variation.append({"status_code": status_code, "permd_req": permd_req})
                                    stack.append((permd_req, new_switched_points))
                    elif type(perm_req["body"]) is list:
                        for key in range(0, len(perm_req["body"])):
                            value = perm_req["body"][key]
                            json_obj, escaped_or_unescaped = process_and_load_json(value)
                            if json_obj != None:
                            
                                for index, variation in enumerate(generate_value_variations(json_obj)):
                                
                                    key_for_output = "_".join(list_different_values(json_obj, variation))
                                    if escaped_or_unescaped == 0:
                                       json_string = json.dumps(variation)
                                    elif escaped_or_unescaped == 1:
                                        json_string = escape_json(variation)
                                    elif escaped_or_unescaped == 2:
                                        json_string = encode_json_with_url_encoding(variation)
                                    elif escaped_or_unescaped == 3:
                                        json_string = encode_base64(variation)

                                    new_switched_points = current_switched_points + [f"{key_for_output}_{index}_value"]
                                    permd_req = copy.deepcopy(perm_req)
                                    permd_req["body"][key] = json_string
                                    executor.submit(run_feroxbuster, permd_req, new_switched_points)
                                    
                                    stack.append((permd_req, new_switched_points))
    
    
    # def generate_req_variations(perm_req, switched_injection_points):
    #     nonlocal num_of_discovered_ids

    #     # two is the new one
    #     if len(switched_injection_points) == num_of_discovered_ids:
    #         return

    #     # fuzzing path
    #     subpaths = perm_req["path"].split("/")
    #     for subpath in subpaths:

    #         if not subpath:
    #             continue
            
    #         attacker_values = get_attacker_values(subpath)
    #         for attacker_value in attacker_values:
    #             if attacker_value == subpath:
    #                 continue
                
    #             permd_req = copy.deepcopy(perm_req)
    #             permd_req["path"] = permd_req["path"].replace(subpath, str(attacker_value))

    #             switched_injection_points_for_this_instance = list(switched_injection_points)
    #             switched_injection_points_for_this_instance.append(f"{subpaths.index(subpath) + 1}_subpath")
    #             switched_injection_points_for_this_instance.append(f"{attacker_values.index(attacker_value) + 1}_value")

    #             run_feroxbuster(permd_req, switched_injection_points_for_this_instance)
                
    #             generate_req_variations(permd_req, switched_injection_points_for_this_instance)
        
    #     # fuzzing queries
    #     if perm_req["queries"]:
    #         for key,value in perm_req["queries"].items():
    #             if type(value) is not str or (type(value) is str and " " not in value):
    #                 attacker_values = get_attacker_values(value)
    #                 for attacker_value in attacker_values:
    #                 # for attacker_value in get_attacker_values(value):
    #                     preserved_attacker_value = attacker_value
    #                     try:
    #                         attacker_value = type(value)(attacker_value)
    #                     except:
    #                         pass
                        
    #                     if attacker_value == value:
    #                         continue

    #                     permd_req = copy.deepcopy(perm_req)
    #                     permd_req["queries"][key] = attacker_value

    #                     switched_injection_points_for_this_instance = list(switched_injection_points)
    #                     switched_injection_points_for_this_instance.append(key)
    #                     switched_injection_points_for_this_instance.append(f"{attacker_values.index(preserved_attacker_value) + 1}_value")

    #                     run_feroxbuster(permd_req, switched_injection_points_for_this_instance)
    #                     generate_req_variations(permd_req, switched_injection_points_for_this_instance)
                
    #             json_obj, escaped_or_unescaped = process_and_load_json(value)
    #             if json_obj != None:
                    
    #                 for index, variation in enumerate(generate_value_variations(json_obj)):
    #                     key_for_output = "_".join(list_different_values(json_obj, variation))
    #                     if escaped_or_unescaped == 0:
    #                         json_string = json.dumps(variation)
    #                     elif escaped_or_unescaped == 1:
    #                         json_string = escape_json(variation)
    #                     elif escaped_or_unescaped == 2:
    #                         json_string = encode_json_with_url_encoding(variation)
    #                     elif escaped_or_unescaped == 3:
    #                         json_string = encode_base64(variation)
                        
    #                     switched_injection_points_for_this_instance = list(switched_injection_points)
    #                     switched_injection_points_for_this_instance.append(key_for_output)
    #                     switched_injection_points_for_this_instance.append(f"{index}_value")

    #                     permd_req = copy.deepcopy(perm_req)
    #                     permd_req["queries"][key] = json_string

    #                     run_feroxbuster(permd_req, switched_injection_points_for_this_instance)

    #                     generate_req_variations(permd_req, switched_injection_points_for_this_instance)
        
    #     # fuzzing body
    #     if perm_req["body"]:
            
    #         for index, variation in enumerate(generate_value_variations(perm_req["body"])):
    #             permd_req = copy.deepcopy(perm_req)
    #             permd_req["body"] = variation
    #             key_for_output = "_".join(list_different_values(perm_req["body"], permd_req["body"]))
    #             # idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)
                
    #             switched_injection_points_for_this_instance = list(switched_injection_points)
    #             switched_injection_points_for_this_instance.append(key_for_output)
    #             switched_injection_points_for_this_instance.append(f"{index}_value")

    #             run_feroxbuster(permd_req, switched_injection_points_for_this_instance)

    #             generate_req_variations(permd_req, switched_injection_points_for_this_instance)
                
    #         if type(perm_req["body"]) is dict:
    #             for key,value in perm_req["body"].items():
    #                 json_obj, escaped_or_unescaped = process_and_load_json(value)
    #                 if json_obj != None:
                        
    #                     for index, variation in enumerate(generate_value_variations(json_obj)):
                            
    #                         key_for_output = "_".join(list_different_values(json_obj, variation))
    #                         if escaped_or_unescaped == 0:
    #                            json_string = json.dumps(variation)
    #                         elif escaped_or_unescaped == 1:
    #                             json_string = escape_json(variation)
    #                         elif escaped_or_unescaped == 2:
    #                             json_string = encode_json_with_url_encoding(variation)
    #                         elif escaped_or_unescaped == 3:
    #                             json_string = encode_base64(variation)
                            
    #                         permd_req = copy.deepcopy(perm_req)
    #                         permd_req["body"][key] = json_string
                            
    #                         # idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)

    #                         switched_injection_points_for_this_instance = list(switched_injection_points)
    #                         switched_injection_points_for_this_instance.append(key_for_output)
    #                         switched_injection_points_for_this_instance.append(f"{index}_value")
                            
    #                         run_feroxbuster(permd_req, switched_injection_points_for_this_instance)

    #                         generate_req_variations(permd_req, switched_injection_points_for_this_instance)
                            
    #         elif type(perm_req["body"]) is list:
    #             for key in range(0, len(perm_req["body"])):
    #                 value = perm_req["body"][key]
    #                 json_obj, escaped_or_unescaped = process_and_load_json(value)
    #                 if json_obj != None:
                        
    #                     for index, variation in enumerate(generate_value_variations(json_obj)):
                            
    #                         key_for_output = "_".join(list_different_values(json_obj, variation))
    #                         if escaped_or_unescaped == 0:
    #                            json_string = json.dumps(variation)
    #                         elif escaped_or_unescaped == 1:
    #                             json_string = escape_json(variation)
    #                         elif escaped_or_unescaped == 2:
    #                             json_string = encode_json_with_url_encoding(variation)
    #                         elif escaped_or_unescaped == 3:
    #                             json_string = encode_base64(variation)
                            
    #                         permd_req = copy.deepcopy(perm_req)
    #                         permd_req["body"][key] = json_string
                            
    #                         # idx_of_payload = (index + 1) % (len(payloads) + len(payloads) + 1)

    #                         switched_injection_points_for_this_instance = list(switched_injection_points)
    #                         switched_injection_points_for_this_instance.append(key_for_output)
    #                         switched_injection_points_for_this_instance.append(f"{index}_value")

    #                         run_feroxbuster(permd_req, switched_injection_points_for_this_instance)

    #                         generate_req_variations(permd_req, switched_injection_points_for_this_instance)

                    
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

    all_switched_injection_points = list()
    def run_feroxbuster(perm_req, switched_injection_points):
        switched_injection_points.sort()

        # print(switched_injection_points)

        if switched_injection_points not in all_switched_injection_points:
            all_switched_injection_points.append(switched_injection_points)
        else:
            return

        nonlocal req_signature
        # if last3c:
        #     return
        # cmd = list()

        # log_file = open("logfile.log", "a")
        # log_file.write(f"{perm_req}\n")
        # log_file.close()

        # if proxy == "self":
        #     cmd.extend("feroxbuster -k -n -r --dont-extract-links --no-state --dont-filter --scan-limit 1 --rate-limit 1 -T 10".split(" "))
        # else:
        #     cmd.extend(f"feroxbuster -k -n -r --dont-extract-links --no-state --dont-filter --scan-limit 1 --rate-limit 1 -T 10 --proxy socks5h://{proxy}".split(" "))

        # Add method and URL
        # cmd.append("-m")
        # cmd.append(perm_req['method'])
        
        # with open(f"./endpoint_{req_signature}.txt", "w") as endpoint:
        #     endpoint.write(perm_req['path'])
        # cmd.append("-u")
        # cmd.extend(f"{perm_req['headers']['Host']['value']} -w ./endpoint_{req_signature}.txt".split(" "))
        
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

        def does_the_parameter_exist(method, url, headers=None, query_params=None, data=None, output_file="http_request_log.txt"):
            nonlocal req_signature
            
            # Parse URL
            parsed_url = urlparse(url)
            path = parsed_url.path or "/"
            query_string = parsed_url.query
            
            query_param_new_or_updated_key = dict()
            if query_params:
                query_param_new_or_updated_key = get_the_new_or_updated_key_and_its_value(query_params)
                if query_param_new_or_updated_key:
                    query_param_new_or_updated_key = safe_urlencode(query_param_new_or_updated_key)
                    query_string = safe_urlencode(query_params).replace(query_param_new_or_updated_key, "%s")

                    query_param_new_or_updated_key = get_the_new_or_updated_key_and_its_value(query_params)
                    query_param_new_or_updated_key[list(query_param_new_or_updated_key.keys())[0]] = list(query_param_new_or_updated_key.values())[0]
                    # query_param_new_or_updated_key.pop(list(query_param_new_or_updated_key.keys())[0])
                else:
                    query_string = safe_urlencode(query_params)

            # Build the request line
            request_line = f"{method.upper()} {path}"
            if query_string:
                request_line += f"?{query_string}"
            request_line += f" HTTP/1.1\n"

            # Build headers
            host_header = f"Host: {parsed_url.netloc}\n"
            headers_block = ""
            if headers:
                headers_block = "".join(f"{key}: {value}\n" for key, value in headers.items())

            def kill_process_and_children(pid):
                try:
                    parent = psutil.Process(pid)
                    for child in parent.children(recursive=True):  # or parent.children() for non-recursive
                        child.kill()
                    parent.kill()
                except psutil.NoSuchProcess:
                    pass

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

            # Build body
            body_block = ""

            body_new_or_updated_key = dict()
            if data:
                
                body_block = data
                
                content_type = str(headers.get("Content-Type"))
                if "json" in content_type.lower():
                    # log_file = open("logfile.log", "a")
                    # log_file.write(f"was in here\n")
                    # log_file.close()

                    data = json.loads(data)
                    body_new_or_updated_key = get_the_new_or_updated_key_and_its_value(data)

                    # log_file = open("logfile.log", "a")
                    # log_file.write(f"first: {body_new_or_updated_key}\n")
                    # log_file.close()
                    if body_new_or_updated_key:
                        body_new_or_updated_key = json.dumps(body_new_or_updated_key)[1:-1]
                        body_block = json.dumps(data).replace(body_new_or_updated_key, "%s")
                        body_new_or_updated_key = get_the_new_or_updated_key_and_its_value(data)

                        # log_file = open("logfile.log", "a")
                        # log_file.write(f"second: {body_new_or_updated_key}\n")
                        # log_file.close()

                        body_new_or_updated_key[list(body_new_or_updated_key.keys())[0]] = list(body_new_or_updated_key.values())[0]
                        # body_new_or_updated_key.pop(list(body_new_or_updated_key.keys())[0])
    
                elif "x-www-form-urlencoded" in content_type.lower():
                    # data = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(data).items()}
                    data = {k: v if len(v) == 1 else v for k, v in custom_parse_qsl(data).items()}
                    body_new_or_updated_key = get_the_new_or_updated_key_and_its_value(data)
                    if body_new_or_updated_key:
                        body_new_or_updated_key = safe_urlencode(body_new_or_updated_key)
                        body_block = safe_urlencode(data).replace(body_new_or_updated_key, "%s")
                        body_new_or_updated_key = get_the_new_or_updated_key_and_its_value(data)
                        body_new_or_updated_key[list(body_new_or_updated_key.keys())[0]] = list(body_new_or_updated_key.values())[0]
                        # body_new_or_updated_key.pop(list(body_new_or_updated_key.keys())[0])
                
                elif "multipart/form-data" in content_type.lower():
                    data = parse_multipart_form_data(content_type, data)


            # Combine all parts
            http_request = f"{request_line}{host_header}{headers_block}\n{body_block}"

            # Write to a file
            with open(req_signature, "w") as file:
                file.write(http_request)

            log_file = open("logfile.log", "a")
            log_file.write(f"\n")
            log_file.write(f"\n")
            log_file.write(f"{http_request}\n")
            log_file.write(f"\n")
            log_file.write(f"\n")
            log_file.close()
            return

            cmd = ["x8"]
            cmd.append("-r")
            cmd.append(req_signature)
            cmd.append("-o")
            cmd.append(f"./{req_signature}_x8_output.json")
            cmd.append("-O")
            cmd.append("json")
            cmd.append("-L")

            if args.x8_concurrency:
                cmd.append("-c")
                cmd.append(f"{args.x8_concurrency}")
            
            if proxy != "self":
                cmd.append("--proxy")
                cmd.append(f"http://{proxy}")
            
            cmd.append("--custom-parameters")
            if params:
                cmd.extend(list(set(list(set(get_all_keys(perm_req["resb"]))).extend(params))))
            elif "resb" in list(perm_req.keys()):
                cmd.extend(list(set(list(set(get_all_keys(perm_req["resb"]))))))
            else:
                os.remove(req_signature)
                return False
            
            if type(body_new_or_updated_key) is dict and len(list(body_new_or_updated_key.keys())) > 0:
                # cmd.append("--custom-parameters")
                # cmd.append(f'{list(body_new_or_updated_key.keys())[0]}')
                # cmd.extend(params)
                cmd.append("--custom-values")
                cmd.append(f'{list(body_new_or_updated_key.values())[0]}')
                if str(list(body_new_or_updated_key.values())[0]).strip() == '':
                    os.remove(req_signature)
                    return False
            elif type(query_param_new_or_updated_key) is dict and len(list(query_param_new_or_updated_key.keys())) > 0:
                # cmd.append("--custom-parameters")
                # cmd.append(f'{list(query_param_new_or_updated_key.keys())[0]}')
                # cmd.extend(params)
                cmd.append("--custom-values")
                cmd.append(f'{list(query_param_new_or_updated_key.values())[0]}')
                if str(list(query_param_new_or_updated_key.values())[0]).strip() == '':
                    os.remove(req_signature)
                    return False
            # else:
            # body_new_or_updated_key = get_the_new_or_updated_key_and_its_value(data)
            # body_new_or_updated_key = json.dumps(body_new_or_updated_key)[1:-1]
            # body_block = json.dumps(data).replace(body_new_or_updated_key, "%s")

            # log_file = open("logfile.log", "a")
            # log_file.write("replacement error:\n")
            # log_file.write(f"the replacer: {body_new_or_updated_key}\n")
            # log_file.write(f"the replaced: {json.dumps(data)}\n")
            # log_file.write(f"after replaced: {json.dumps(data).replace(body_new_or_updated_key, '%s')}:\n")
            # log_file.close()

                # print("error: wtf")

            cmd = [x for x in cmd if x]
            cmd = list(map(str, cmd))

            timecount = 60
            rate_limit = 1

            if args.token_expiration:
                x8_timeout = min(args.token_expiration,timecount/rate_limit)
            else:
                x8_timeout = timecount/rate_limit
            
            # with x8_lock:
                # subprocess.run(cmd, preexec_fn=os.setsid, timeout=x8_timeout)
            # subprocess.run(cmd, preexec_fn=os.setsid)

            
            # try:
            #     if args.token_expiration:
            #         proc.wait(timeout=min(args.token_expiration,timecount/rate_limit))
            #     else:
            #         proc.wait(timeout=timecount/rate_limit)
            # except subprocess.TimeoutExpired:
            #     print(f"Timeout expired. Killing process {proc.pid} and its children...")
            #     kill_process_and_children(proc.pid)
            
            # stdout, stderr = proc.communicate()

            # # Decode the output and error from bytes to string
            # stdout = stdout.decode('utf-8')
            # stderr = stderr.decode('utf-8')

            # # Print the stdout and stderr

            # log_file = open("x8.log", "a")
            # log_file.write(f"{cmd} exited with the below stdout and stderr\n")
            # log_file.write(f"\n")
            # log_file.write("STDOUT:\n")
            # log_file.write(f"{stdout}\n")
            # log_file.close()

            # log_file = open("x8.log", "a")
            # log_file.write("\n")
            # log_file.write("STDERR:\n")
            # log_file.write(f"{stderr}\n")
            # log_file.close()

            # print("STDERR:")
            # print(stderr)

            found_parameters = False
            x8_retry_count = 0
            while True:
                try:
                    subprocess.run(cmd, preexec_fn=os.setsid)
                    with open(f"./{req_signature}_x8_output.json", 'r') as x8_output_file:
                        x8_output = json.load(x8_output_file)
                        if len(x8_output[0]["found_params"]) > 0:
                            found_parameters = x8_output[0]["found_params"]

                    # os.remove(f"./{req_signature}_x8_output.json")
                    break
                except Exception as e:
                    log_file = open("logfile.log", "a")
                    log_file.write(f"ignored Error: {e} \n")
                    log_file.write("Traceback:\n")
                    log_file.write(traceback.format_exc())
                    log_file.close()
                    
                    x8_retry_count += 1
                    if x8_retry_count == 3:
                        break
                    
            if os.path.exists(f"./{req_signature}_x8_output.json"):
                os.remove(f"./{req_signature}_x8_output.json")
            
            os.remove(req_signature)
            return found_parameters

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
        
        output_path = f"./output/{req_signature}_{prepend_to_output}_{'ANDDDD'.join(switched_injection_points)}"
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
        proxies_for_request = {
            'http': f'socks5h://{proxy}',
            'https': f'socks5h://{proxy}'
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
                    # verify=False,  # Disable SSL verification like `-k` in feroxbuster
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
    
    # req_signature = str(reqs.index(req)) + str(generate_md5(req_unhashed_signature))
    
    # if args.normal_directory == None or "./output/normal" in args.normal_directory:
    # previous_status_code = subprocess.run(f"cat ./output/normal/{req_signature}.json | jq -r .status | grep -v null", shell=True, capture_output=True, text=True).stdout.split("\n")[0]
    # doesnt_exist = not previous_status_code.isdigit()
    # run_feroxbuster(req, 'normal_checkup')
    # current_status_code = subprocess.run(f"cat ./output/normal/{req_signature}_checkup.json | jq -r .status | grep -v null", shell=True, capture_output=True, text=True).stdout.split("\n")[0]
    
    with signatures_and_their_data_lock:
        with open(f"./signatures_and_their_data.txt", "a") as signatures_and_their_data:
            signatures_and_their_data.write(f'{req_signature} is {req["headers"]["Host"]["value"]}_{req["method"]}_{req["method"]}_{req["path"]}_{clean_filename(req["path"])}_{"_".join(get_all_keys(req))}' + "\n")
    
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

    perm_req = copy.deepcopy(req)

    id_count = 0
    discovered_ids = list()
    
    # fuzzing path
    subpaths = perm_req["path"].split("/")
    for subpath in subpaths:
        attacker_values = get_attacker_values(subpath)
        for attacker_value in attacker_values:
            if attacker_value == subpath:
                continue
            
            if subpath not in discovered_ids:
                discovered_ids.append(subpath)
    
    # fuzzing queries
    if perm_req["queries"]:
        for key,value in perm_req["queries"].items():
            if type(value) is not str or (type(value) is str and " " not in value):
                attacker_values = get_attacker_values(value)
                for attacker_value in attacker_values:
                # for attacker_value in get_attacker_values(value):
                    preserved_attacker_value = attacker_value
                    try:
                        attacker_value = type(value)(attacker_value)
                    except:
                        pass
                    
                    if attacker_value == value:
                        continue
                    
                    if value not in discovered_ids:
                        discovered_ids.append(subpath)
                    # print(value)
    
    # fuzzing body
    if perm_req["body"]:
        for value in get_all_values(perm_req["body"]):
            if type(value) is not str or (type(value) is str and " " not in value):
                attacker_values = get_attacker_values(value)
                for attacker_value in attacker_values:
                    
                    if attacker_value not in discovered_ids:
                        discovered_ids.append(attacker_value)
                    # print(value)
    
    num_of_discovered_ids = len(discovered_ids)
    if num_of_discovered_ids > 1:
        generate_req_variations(req, [])
    
    # if collect_ids_for_bac_on_constructed_reqs:
    #     for discovered_id in discovered_ids:
    #         if discovered_id not in ids_for_bac_on_constructed_reqs:
    #             ids_for_bac_on_constructed_reqs.append(discovered_id)

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
parser.add_argument("-a", "--avoid-path", required=False, help="Filter this path or a path that has the input path (deny list) (ex: -a /logout,/deleteuser )")
parser.add_argument('-rl', '--rate-limit', required=False, type=int, help='Limit number of instances to create for handling a request')
parser.add_argument('-xc', '--x8-concurrency', required=False, type=int, help='Limit number of requests per url for x8')
parser.add_argument('-np', '--no-proxy', action='store_true', help='don\'t use proxies and instead use the server ip')
parser.add_argument('-pn', '--params-number', type=int, required=False, help='number of params supplied per updating req.txt for like new authorization keys')
parser.add_argument('-ts', '--token-script', required=False, help='a python script to execute to generate new authorization keys')
parser.add_argument('-H', '--header', required=False, help='a header to add all requests like -H "X-Hackerone: seudxs"')
parser.add_argument('-w', '--wordlist', required=False, help='wordlist to include in parameter check')
parser.add_argument('-d', '--delay', type=int, required=False, help='delay in seconds between --params-number requests')
parser.add_argument("-nd", "--normal-directory", required=False, help="other account's normal output directory to check against the main output directory for shared injection point value")
parser.add_argument('-te', '--token-expiration', type=int, required=False, help='executes token script everytime token expiration time in minutes is reached')
parser.add_argument("-ck", "--consider-key", required=False, help="a key to consider in request identifying through hashing like body.operationName")
parser.add_argument('-ump', '--use-more-param', action='store_true', help='use common param wordlists')
parser.add_argument('-iorp', '--include-other-reqs-params', action='store_true', help='use common param wordlists')
parser.add_argument('-ew', '--extract-wordlist', help='extract params from files in the given directory and its subdirectory')
args = parser.parse_args()



proxies = []
if args.no_proxy:
    proxies.append("self")
else:
    # if not args.rate_limit:
    with open('/home/deus/documents/proxies.txt') as proxy_file:
        for proxy in proxy_file:
            proxy = proxy.strip()
            if proxy != "":
                proxy = proxy.split(':')
                proxies.append(f"isp.smartproxy.com:{proxy[1]}")
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
ids_for_bac_on_constructed_reqs = manager.list()
collect_ids_for_bac_on_constructed_reqs = True
req_lock = multiprocessing.Lock()
signatures_and_their_data_lock = multiprocessing.Lock()
requests_with_special_needs_lock = multiprocessing.Lock()
proxy_setting_lock = multiprocessing.Lock()
x8_lock = multiprocessing.Lock()
counter = multiprocessing.Value('i',1)
req_number = multiprocessing.Value('i',1)
victim_params = list()
attacker_params = list()
subdirectories = []

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

if args.avoid_path != None:
    args.avoid_path = args.avoid_path.lower().split(",")

if args.header != None:
    args.header = args.header.split(":")

if args.token_expiration != None:
    args.token_expiration = args.token_expiration * 60
    # token_loop()
    threading.Thread(target=token_loop, daemon=True).start()

unpack_burp_output_user1 = list()
for burp_file in os.listdir('./user1_input'):
    if os.path.exists("/home/deus/downloads"):
        subprocess.run(f"php /home/deus/downloads/unpack-burp/unpack-burp.php ./user1_input/{burp_file} all > unpack_burp_output_user1.txt", shell=True)
    else:
        subprocess.run(f"php /home/kali/Downloads/unpack-burp/unpack-burp.php ./user1_input/{burp_file} all > unpack_burp_output_user1.txt", shell=True)


    with open('unpack_burp_output_user1.txt', 'r') as file:
        unpack_burp_output_user1.extend(file.read().split("\n\n"))


unpack_burp_output_user2 = list()
for burp_file in os.listdir('./user2_input'):
    if os.path.exists("/home/deus/downloads"):
        subprocess.run(f"php /home/deus/downloads/unpack-burp/unpack-burp.php ./user2_input/{burp_file} all > unpack_burp_output_user2.txt", shell=True)
    else:
        subprocess.run(f"php /home/kali/Downloads/unpack-burp/unpack-burp.php ./user2_input/{burp_file} all > unpack_burp_output_user2.txt", shell=True)


    with open('unpack_burp_output_user2.txt', 'r') as file:
        unpack_burp_output_user2.extend(file.read().split("\n\n"))

# if args.extract_wordlist:
#     for dire in list_subdirectories_recursive(args.extract_wordlist):
#         subdirectories.append(dire)

#     pool = multiprocessing.Pool(3)
#     pool.map(extract_params, subdirectories, chunksize=1)

#     with open('extracted_param_wordlist', 'w') as outfile:
#         for filename in glob.glob('params_output_*.txt'):
#             with open(filename, 'r') as infile:
#                 outfile.write(infile.read())
#             os.remove(filename)


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
    
reqs = list()
victim_params_keys = list()

for request_and_response in unpack_burp_output_user1:
    if request_and_response == '':
        continue

    request_and_response = json.loads(request_and_response)

    if args.avoid_path != None and any(avoid_path in request_and_response["reqp"] for avoid_path in args.avoid_path):
        continue

    req_text = request_and_response["reqp"].replace("HTTP/2","HTTP/1.1") + "\r\n" + request_and_response["reqh"] + "\r\n\r\n" + request_and_response["reqb"]

    parsed_request = parse_http(req_text)
    if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
        try:
            for param in get_all_keys_with_their_value(json.loads(request_and_response["resb"])):
                if victim_params_keys.count(list(param.keys())[0]) < 5 and type(list(param.values())[0]) is not None and ((type(list(param.values())[0]) is str and " " not in list(param.values())[0]) or (type(list(param.values())[0]) is list and 0 != len(list(param.values())[0])) or (type(list(param.values())[0]) is dict and 0 != len(list(param.values())[0].keys())) or type(list(param.values())[0]) is int or type(list(param.values())[0]) is float):
                    victim_params_keys.append(list(param.keys())[0])
                    victim_params.append(param)
            
            for param in get_all_keys_with_their_value(parsed_request["body"]):
                if victim_params_keys.count(list(param.keys())[0]) < 5 and type(list(param.values())[0]) is not None and ((type(list(param.values())[0]) is str and " " not in list(param.values())[0]) or (type(list(param.values())[0]) is list and 0 != len(list(param.values())[0])) or (type(list(param.values())[0]) is dict and 0 != len(list(param.values())[0].keys())) or type(list(param.values())[0]) is int or type(list(param.values())[0]) is float):
                    victim_params_keys.append(list(param.keys())[0])
                    victim_params.append(param)
        except Exception as e:
            print(f"An ignored error occurred while parsing resb: {e}")
        
        reqs.append(parsed_request)
    else:
        print(req_text)

attacker_params_keys = list()

for request_and_response in unpack_burp_output_user2:
    if request_and_response == '':
        continue

    request_and_response = json.loads(request_and_response)

    if  args.avoid_path != None and any(avoid_path in request_and_response["reqp"] for avoid_path in args.avoid_path):
        continue

    req_text = request_and_response["reqp"].replace("HTTP/2","HTTP/1.1") + "\r\n" + request_and_response["reqh"] + "\r\n\r\n" + request_and_response["reqb"]

    parsed_request = parse_http(req_text)
    if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
        try:
            for param in get_all_keys_with_their_value(json.loads(request_and_response["resb"])):
                if attacker_params_keys.count(list(param.keys())[0]) < 5 and type(list(param.values())[0]) is not None and ((type(list(param.values())[0]) is str and " " not in list(param.values())[0]) or (type(list(param.values())[0]) is list and 0 != len(list(param.values())[0])) or (type(list(param.values())[0]) is dict and 0 != len(list(param.values())[0].keys())) or type(list(param.values())[0]) is int or type(list(param.values())[0]) is float):
                    attacker_params_keys.append(list(param.keys())[0])
                    attacker_params.append(param)
            
            for param in get_all_keys_with_their_value(parsed_request["body"]):
                if attacker_params_keys.count(list(param.keys())[0]) < 5 and type(list(param.values())[0]) is not None and ((type(list(param.values())[0]) is str and " " not in list(param.values())[0]) or (type(list(param.values())[0]) is list and 0 != len(list(param.values())[0])) or (type(list(param.values())[0]) is dict and 0 != len(list(param.values())[0].keys())) or type(list(param.values())[0]) is int or type(list(param.values())[0]) is float):
                    attacker_params_keys.append(list(param.keys())[0])
                    attacker_params.append(param)
        except Exception as e:
            print(f"An ignored error occurred while parsing resb: {e}")
        
    else:
        print(req_text)

requests_len = len(reqs)


# def process_params_with_interested_value(params, interested_value):
#     """Processes parameters for the interested value."""
#     results = []

#     if isinstance(params, dict):
#         for k, v in params.items():
#             if interested_value == v:
#                 results.append({k: v})
#             if isinstance(v, (dict, list)):
#                 results.extend(process_params_with_interested_value(v, interested_value))
#             else:
#                 json_obj, _ = process_and_load_json(v)
#                 if isinstance(json_obj, (dict, list)):
#                     results.extend(process_params_with_interested_value(json_obj, interested_value))
#     elif isinstance(params, list):
#         for v in params:
#             if isinstance(v, (dict, list)):
#                 results.extend(process_params_with_interested_value(v, interested_value))
#             else:
#                 json_obj, _ = process_and_load_json(v)
#                 if isinstance(json_obj, (dict, list)):
#                     results.extend(process_params_with_interested_value(json_obj, interested_value))

#     return results

# def process_params_with_interested_param(params, interested_param):
#     """Processes parameters for the interested parameter."""
#     results = []

#     if isinstance(params, dict):
#         for k, v in params.items():
#             if interested_param == k:
#                 results.append({k: v})
#             if isinstance(v, (dict, list)):
#                 results.extend(process_params_with_interested_param(v, interested_param))
#             else:
#                 json_obj, _ = process_and_load_json(v)
#                 if isinstance(json_obj, (dict, list)):
#                     results.extend(process_params_with_interested_param(json_obj, interested_param))
#     elif isinstance(params, list):
#         for v in params:
#             if isinstance(v, (dict, list)):
#                 results.extend(process_params_with_interested_param(v, interested_param))
#             else:
#                 json_obj, _ = process_and_load_json(v)
#                 if isinstance(json_obj, (dict, list)):
#                     results.extend(process_params_with_interested_param(json_obj, interested_param))

#     return results

# def get_attacker_values(victim_value):
#     """Retrieves attacker values based on victim value using threading."""
#     attacker_values = []

#     # Step 1: Find interested victim parameters
#     with ThreadPoolExecutor() as executor:
#         future_to_victim = {
#             executor.submit(process_params_with_interested_value, victim_params, victim_value): victim_value
#         }
#         for future in as_completed(future_to_victim):
#             interested_victim_params = future.result()

#     # Step 2: Extract victim keys and process attacker parameters
#     victim_keys = get_all_keys(interested_victim_params)
#     with ThreadPoolExecutor() as executor:
#         futures = [
#             executor.submit(process_params_with_interested_param, attacker_params, victim_key)
#             for victim_key in victim_keys
#         ]
#         for future in as_completed(futures):
#             attacker_param_group = future.result()
#             for attacker_param in attacker_param_group:
#                 attacker_values.append(list(attacker_param.values())[0])

#     return attacker_values

# # Example usage
# print(get_attacker_values(list(victim_params)[2]["document_id"]))




# print(json.dumps(list(victim_params)))
# print()
# print(json.dumps(list(attacker_params)))
# print()
# print()

# interested_victim_params = list()

# for interested_victim_params in get_params_with_interested_value(victim_params, list(victim_params)[2]["document_id"]):
#     for victim_param in get_all_keys(interested_victim_params):
#         for attacker_param in get_params_with_interested_param(attacker_params, victim_param):
#             print(list(attacker_param.values())[0])



# print(get_attacker_values(list(victim_params)[2]["document_id"]))

# print(interested_victim_params)

# for param in interested_victim_params:
    # print(param)
    # print(get_params_with_interested_param(attacker_params, param))

# attacker_params_non_dict_count = 0
# victim_params_non_dict_count = 0

# for attacker_param in attacker_params:
    # print(type(list(attacker_param.values())[0]))
    # if type(list(attacker_param.values())[0]) is not None and ((type(list(attacker_param.values())[0]) is str and " " not in list(attacker_param.values())[0]) or (type(list(attacker_param.values())[0]) is list and 0 != len(list(attacker_param.values())[0])) or (type(list(attacker_param.values())[0]) is dict and 0 != len(list(attacker_param.values())[0].keys())) or type(list(attacker_param.values())[0]) is int or type(list(attacker_param.values())[0]) is float):
    # print(attacker_param)
    
    # exit()

# print(len(victim_params))
# print(len(attacker_params))
# exit()

prepend_to_output = "user1"

pool = multiprocessing.Pool(len(proxies))
pool.map(permutate_and_send_request, reqs, chunksize=1)

collect_ids_for_bac_on_constructed_reqs = False

reqs = list()
victim_params_keys = list()

for request_and_response in unpack_burp_output_user2:
    if request_and_response == '':
        continue

    request_and_response = json.loads(request_and_response)

    if args.avoid_path != None and any(avoid_path in request_and_response["reqp"] for avoid_path in args.avoid_path):
        continue

    req_text = request_and_response["reqp"].replace("HTTP/2","HTTP/1.1") + "\r\n" + request_and_response["reqh"] + "\r\n\r\n" + request_and_response["reqb"]

    parsed_request = parse_http(req_text)
    if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
        try:
            for param in get_all_keys_with_their_value(json.loads(request_and_response["resb"])):
                if victim_params_keys.count(list(param.keys())[0]) < 5 and type(list(param.values())[0]) is not None and ((type(list(param.values())[0]) is str and " " not in list(param.values())[0]) or (type(list(param.values())[0]) is list and 0 != len(list(param.values())[0])) or (type(list(param.values())[0]) is dict and 0 != len(list(param.values())[0].keys())) or type(list(param.values())[0]) is int or type(list(param.values())[0]) is float):
                    victim_params_keys.append(list(param.keys())[0])
                    victim_params.append(param)
            
            for param in get_all_keys_with_their_value(parsed_request["body"]):
                if victim_params_keys.count(list(param.keys())[0]) < 5 and type(list(param.values())[0]) is not None and ((type(list(param.values())[0]) is str and " " not in list(param.values())[0]) or (type(list(param.values())[0]) is list and 0 != len(list(param.values())[0])) or (type(list(param.values())[0]) is dict and 0 != len(list(param.values())[0].keys())) or type(list(param.values())[0]) is int or type(list(param.values())[0]) is float):
                    victim_params_keys.append(list(param.keys())[0])
                    victim_params.append(param)
        except Exception as e:
            print(f"An ignored error occurred while parsing resb: {e}")
        
        reqs.append(parsed_request)
    else:
        print(req_text)

attacker_params_keys = list()

for request_and_response in unpack_burp_output_user1:
    if request_and_response == '':
        continue

    request_and_response = json.loads(request_and_response)

    if  args.avoid_path != None and any(avoid_path in request_and_response["reqp"] for avoid_path in args.avoid_path):
        continue

    req_text = request_and_response["reqp"].replace("HTTP/2","HTTP/1.1") + "\r\n" + request_and_response["reqh"] + "\r\n\r\n" + request_and_response["reqb"]

    parsed_request = parse_http(req_text)
    if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
        try:
            for param in get_all_keys_with_their_value(json.loads(request_and_response["resb"])):
                if attacker_params_keys.count(list(param.keys())[0]) < 5 and type(list(param.values())[0]) is not None and ((type(list(param.values())[0]) is str and " " not in list(param.values())[0]) or (type(list(param.values())[0]) is list and 0 != len(list(param.values())[0])) or (type(list(param.values())[0]) is dict and 0 != len(list(param.values())[0].keys())) or type(list(param.values())[0]) is int or type(list(param.values())[0]) is float):
                    attacker_params_keys.append(list(param.keys())[0])
                    attacker_params.append(param)
            
            for param in get_all_keys_with_their_value(parsed_request["body"]):
                if attacker_params_keys.count(list(param.keys())[0]) < 5 and type(list(param.values())[0]) is not None and ((type(list(param.values())[0]) is str and " " not in list(param.values())[0]) or (type(list(param.values())[0]) is list and 0 != len(list(param.values())[0])) or (type(list(param.values())[0]) is dict and 0 != len(list(param.values())[0].keys())) or type(list(param.values())[0]) is int or type(list(param.values())[0]) is float):
                    attacker_params_keys.append(list(param.keys())[0])
                    attacker_params.append(param)
        except Exception as e:
            print(f"An ignored error occurred while parsing resb: {e}")
        
    else:
        print(req_text)

requests_len = len(reqs)

prepend_to_output = "user2"

pool = multiprocessing.Pool(len(proxies))
pool.map(permutate_and_send_request, reqs, chunksize=1)

stop_event.set()


# with open('ids_for_bac_on_constructed_reqs.txt', 'w') as outfile:
#     for discovered_id in ids_for_bac_on_constructed_reqs:
#         outfile.write(discovered_id + '\n')

