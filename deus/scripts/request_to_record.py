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

parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument("-r", "--request-file", required=True, help="Path to the request file containing headers.")
parser.add_argument("-rsl", "--requests-list", required=False, help="obtain requests out of a list of reqs json")
parser.add_argument("-a", "--avoid-path", required=False, help="Filter this path or a path that has the input path (deny list) (ex: -a /logout,/deleteuser )")
parser.add_argument('-p', '--proxy', required=True, help='http proxy to send to')
parser.add_argument('-H', '--header', required=False, help='a header to add all requests like -H "X-Hackerone: seudxs"')
parser.add_argument('-d', '--delay', type=int, required=False, help='delay in seconds between --payloads-number requests')
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



def send_req(perm_req):

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
        'http': f'{args.proxy}',
        'https': f'{args.proxy}'
    } if args.proxy != "self" else None
    requests_count = 0
    successful_request = False
    while True:
        try:
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
                stream=True,  # Stream the response to read in chunks
                verify=False
            )
            break
        except Exception as e:
            log_file = open("fuzz.log", "a")
            log_file.write(f"Error: {e} \n")
            log_file.close()
            if requests_count % 2 == 0:
                url = f"http://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"
            else:
                url = f"https://{perm_req['headers']['Host']['value'].strip()}{perm_req['path'].strip()}"
        # finally:
            # fcntl.flock(binary_file, fcntl.LOCK_UN)
        requests_count += 1
        if requests_count == 3:
            break
unpack_burp_output = list()
for burp_file in os.listdir('./input'):
    if os.path.exists("/home/deus/downloads"):
        subprocess.run(f"php /home/deus/downloads/unpack-burp/unpack-burp.php ./input/{burp_file} all > unpack_burp_output.txt", shell=True)
    else:
        subprocess.run(f"php /home/kali/Downloads/unpack-burp/unpack-burp.php ./input/{burp_file} all > unpack_burp_output.txt", shell=True)


    with open('unpack_burp_output.txt', 'r') as file:
        unpack_burp_output.extend(file.read().split("\n\n"))


reqs = list()

# if args.requests_list:
#     with open(args.requests_list, 'r') as json_file:
#         args.requests_list = json.load(json_file)
    
#     for req in args.requests_list:

#         parsed_request = parse_http(req)

#         if args.avoid_path != None and any(avoid_path in parsed_request["path"].lower() for avoid_path in args.avoid_path):
#             continue
        
#         # try:
#         #     a = parsed_request['headers']["Host"]
#         # except:
#         #     print(f"req: {parsed_request}")
#         #     exit()

#         reqs.append(parsed_request)


if args.requests_list:
    with open(args.requests_list, 'r') as requests_list_file:
        for req in requests_list_file:
            reqs.append(req)


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

for req in reqs:
    send_req(req)

