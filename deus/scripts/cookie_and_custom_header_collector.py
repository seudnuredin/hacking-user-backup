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
from collections import Counter
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import socket
import shlex
import signal
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument("-r", "--request-file", required=False, help="Path to the request file containing headers.")
parser.add_argument("-rsl", "--requests-list", required=False, help="obtain requests out of a list of reqs json")
parser.add_argument("-mf", "--mau-file", required=False, help="a directory that has a method and url files in it or its subdirectories")
parser.add_argument("-a", "--avoid-path", required=False, help="Filter this path or a path that has the input path (deny list) (ex: -a /logout,/deleteuser )")
# parser.add_argument('-p', '--proxy', required=True, help='http proxy to send to')
parser.add_argument('-H', '--header', required=False, help='a header to add all requests like -H "X-Hackerone: seudxs"')
parser.add_argument('-d', '--delay', type=int, required=False, help='delay in seconds between --payloads-number requests')
parser.add_argument('-rl', '--rate-limit', required=True, type=int, help='Limit number of requests per second (per directory) (default: 1, i.e. 1 r/s)')
parser.add_argument("-rc", "--rate-config", required=True, help="Path to the rate config.")
parser.add_argument('-np', '--no-proxy', action='store_true', help='don\'t use proxies and instead use the server ip')
args = parser.parse_args()

if args.avoid_path != None:
    args.avoid_path = args.avoid_path.lower().split(",")


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

        if rate_config:
            return available_port, rota_proc, min(rate_limit, rate_config['rate'] * 10)
        else:
            return available_port, rota_proc, rate_limit

    except Exception as e:
        print("Error:", e)
        print("args:", hostname, rate_limit, used_user_agents)

def rota_exit_handler(rota_proc):
    os.killpg(os.getpgid(rota_proc.pid), signal.SIGKILL)

    try:
        rota_proc.wait(timeout=5)
    except Exception:
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
        print(traceback.format_exc())

def get_strings_with_unique_length(string_list):
    """
    Returns a list of strings where each string has a unique length
    compared to other strings in the returned list.
    """
    unique_lengths = list()
    result_strings = []

    for s in string_list:
        length = len(s)
        unique_lengths.append(length)
    for s in string_list:
        length = len(s)
        if unique_lengths.count(length) == 1:
            result_strings.append(s)
    return result_strings

def send_req(perm_req):
    # global cookies
    # global aca_headers
    # global manager
    # global header_lock
    
    try:

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

        url = f"https://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"

        # print(url)
        if args.delay != None:
            time.sleep(args.delay)

        # with req_lock:
        if args.request_file != None:
            # if args.payloads_number != None and args.token_expiration == None and args.token_script != None and idx_of_payload % args.payloads_number == 0:
            #     subprocess.run(f"python3 {args.token_script}", shell=True)
            headers = extract_headers(args.request_file)
            queries = extract_query_parameters(args.request_file)

            update_dict_with_matches(perm_req["queries"], queries)
            update_dict_with_matches(perm_req["headers"], headers)
        # Add queries
        queries = None
        if perm_req["queries"]:
            queries = dict()
            for key, value in perm_req.get('queries', {}).items():
                # cmd.append("-Q")
                # cmd.append(f"{key}={value}")
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

        # Set proxy
        proxies_for_request = {
            'http': f'{proxies[0]}',
            'https': f'{proxies[0]}'
        } if proxies[0] != "self" else None

        for method in [perm_req['method'], "OPTIONS"]:
            requests_count = 0
            successful_request = False
            while True:
                try:
                    response = requests.request(
                        method=method,
                        url=url,
                        headers=headers,
                        # params=queries,  # Add query parameters to the URL
                        data=body,  # For form or raw body
                        timeout=30,  # Set a reasonable timeout
                        proxies=proxies_for_request,  # Proxy configuration
                        verify=False,  # Disable SSL verification like `-k` in feroxbuster
                        allow_redirects=True,  # Follow redirects if needed
                        stream=True,  # Stream the response to read in chunks
                    )
                    allow_headers = response.headers.get("Access-Control-Allow-Headers")
                    if allow_headers:
                        for h in allow_headers.split(","):
                            header = h.strip()
                            if header and header != "*":
                                with header_lock:
                                    if header not in aca_headers:
                                        aca_headers.append(header)


                    _ = response.headers

                    # This gives a RequestsCookieJar object
                    res_cookies = response.cookies

                    # Convert to dictionary
                    cookies_dict = requests.utils.dict_from_cookiejar(res_cookies)
                    cookie_string = "; ".join(f"{k}={v}" for k, v in cookies_dict.items())

                    # cookie_dict = manager.dict()
                    cookie_dict = dict()

                    cookie_dict["cookie_string"] = cookie_string
                    cookie_dict["url"] = url
                    cookie_dict["method"] = method
                    with cookies_lock:
                        cookies.append(cookie_dict)

                    break
                except Exception as e:
                    log_file = open("fuzz.log", "a")
                    log_file.write(f"Error: {e} \n")
                    log_file.close()
                    # if requests_count % 2 == 0:
                    #     url = f"http://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"
                    # else:
                    #     url = f"https://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"
                # finally:
                    # fcntl.flock(binary_file, fcntl.LOCK_UN)
                requests_count += 1
                if requests_count == 3:
                    break
    
    except Exception as e:
        print("send_req error:", e)
    
unpack_burp_output = list()
# for burp_file in os.listdir('./input'):
#     if os.path.exists("/home/deus/downloads"):
#         subprocess.run(f"php /home/deus/downloads/unpack-burp/unpack-burp.php ./input/{burp_file} all > unpack_burp_output.txt", shell=True)
#     else:
#         subprocess.run(f"php /home/kali/Downloads/unpack-burp/unpack-burp.php ./input/{burp_file} all > unpack_burp_output.txt", shell=True)


#     with open('unpack_burp_output.txt', 'r') as file:
#         unpack_burp_output.extend(file.read().split("\n\n"))


reqs = list()

if args.requests_list:
    with open(args.requests_list, 'r') as json_file:
        args.requests_list = json.load(json_file)
    
    for req in args.requests_list:

        parsed_request = parse_http(req)

        if args.avoid_path != None and any(avoid_path in parsed_request["path"].lower() for avoid_path in args.avoid_path):
            continue
        
        # try:
        #     a = parsed_request['headers']["Host"]
        # except:
        #     print(f"req: {parsed_request}")
        #     exit()

        reqs.append(parsed_request)

if args.mau_file:
    # paths = glob.glob(args.mau_dir)
    # with open("method_and_urls_paths.txt", "w") as mau_file:
    #     subprocess.run(["find"] + paths + ["-type", "f"], stdout=mau_file)
    
    # with open("method_and_urls_paths.txt", "r") as mau_files:
    #     for mau_file_path in mau_files:
    #         mau_file_path = mau_file_path.strip()

    with open(args.mau_file, "r") as mau_file:
        for mau in mau_file:
            mau = mau.strip().split(" ")
            method = mau[0]
            url = mau[1]
            queries = extract_query_parameters(url)
            hostname = urlparse(url).hostname
            path = extract_path(url)
            headers = dict()
            headers["Host"] = {'value': hostname, 'params': {}}
            headers['User-Agent'] = {'value': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'params': {}}
            if args.header != None and args.header[0] not in list(headers.keys()):
                headers[args.header[0]] = {'value': args.header[1], 'params': {}}
            http_data = {
                'method': method,
                'path': path,
                'queries': queries,
                'headers': headers,
                'body': ""
            }
            if http_data not in reqs:
                reqs.append(http_data)


# print(len(reqs))
# exit()

for request_and_response in unpack_burp_output:
    if request_and_response == '':
        continue
    
    request_and_response = json.loads(request_and_response)
    
    if  args.avoid_path != None and any(avoid_path in request_and_response["reqp"].lower() for avoid_path in args.avoid_path):
        continue
    
    req_text = request_and_response["reqp"].replace("HTTP/2","HTTP/1.1") + "\r\n" + request_and_response["reqh"] + "\r\n\r\n" + request_and_response["reqb"]
    
    parsed_request = parse_http(req_text)
    if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
        # try:
        #     for param in get_all_keys_with_their_value(json.loads(request_and_response["resb"])):
        #         if param not in victim_params:
        #             victim_params.append(param)
            
        #     for param in get_all_keys_with_their_value(parsed_request["body"]):
        #         if param not in victim_params:
        #             victim_params.append(param)
        # except Exception as e:
        #     print(f"An ignored error occurred while parsing resb: {e}")
        
        reqs.append(parsed_request)
    else:
        print(req_text)

requests_len = len(reqs)

grouped_reqs = group_reqs_by_hostname(reqs)

manager = multiprocessing.Manager()
# aca_headers = manager.list()
# cookies = manager.list()
# header_lock = multiprocessing.Lock()
cookies_lock = threading.Lock()
header_lock = threading.Lock()
aca_headers = list()
cookies = list()

for hostname, reqs in grouped_reqs.items():

    used_user_agents = set()
    proxies = []
    if args.no_proxy:
        proxies.append("self")
    else:
        port, rota_proc, rate_limit = get_proxy_port(hostname, args.rate_limit, used_user_agents)
        proxies.append(f"127.0.0.1:{port}")
    
    # cookies = manager.list()
    cookies = list()
    with ThreadPoolExecutor(max_workers=rate_limit) as executor:
        for req in reqs:
            executor.submit(send_req, req)
    
    # pool = multiprocessing.Pool(len(proxies))
    # pool.map(send_req, reqs, chunksize=1)
    
    cookie_strings = []
    for cookie in cookies:
        cookie_strings.append(cookie["cookie_string"])
    
    cookie_strings = get_strings_with_unique_length(cookie_strings)
    for cookie in cookies:
        if cookie["cookie_string"] in cookie_strings:
            with open("cookies.txt", "a") as cookies_file:
                cookies_file.write(f"{cookie['cookie_string']} {cookie['url']} {cookie['method']}\n")

    if not args.no_proxy:
        rota_exit_handler(rota_proc)


with open("headers.txt", "a") as headers_file:
    for header in sorted(aca_headers):
        headers_file.write(header + "\n")



