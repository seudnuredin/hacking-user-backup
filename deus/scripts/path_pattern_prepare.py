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
import humps

def extract_path(url):
    parsed_url = urlparse(url)
    return parsed_url.path


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



def extract_headers(headers_str):
    headers = {}
    for subdomain in headers_str.split("\n"):
        if ': ' in subdomain:
            key, value = subdomain.split(': ', 1)
            headers[key] = value.strip()
    return headers


def paths_permutation(path):
    global paths
    global paths_permutation_list
    
    path_x = path
    path_x_subpath = re.split(r'[./~-]', path_x)
    for path_y in paths:
        if path_y == path_x:
            continue
        path_y_subpath = re.split(r'[./~-]', path_y)
        smallest_number_of_subpath_parts = min(len(path_x_subpath),len(path_y_subpath))
        path_x_subpath_reversed = path_x_subpath[::-1]
        path_y_subpath_reversed = path_y_subpath[::-1]
        not_match_idx_for_path_x = 0
        there_is_no_match = False
        for subpath_part_idx in range(0, smallest_number_of_subpath_parts):
            if path_x_subpath[subpath_part_idx] != path_y_subpath[subpath_part_idx]:
                there_is_no_match = True
                not_match_idx_for_path_x = subpath_part_idx
                not_match_idx_for_path_y = subpath_part_idx
                break
        
        payload_subpath = ""
        if there_is_no_match:
            for idx in range(0, len(path_x_subpath)):
                if idx == not_match_idx_for_path_x:
                    if path_x[-1] == '/':
                        payload_subpath += "PAYLOADDDD" + '/'
                    if path_x[-1] == '-':
                        payload_subpath += "PAYLOADDDD" + '-'
                    if path_x[-1] == '.':
                        payload_subpath += "PAYLOADDDD" + '.'
                    if path_x[-1] == '~':
                        payload_subpath += "PAYLOADDDD" + '~'
                    else:
                        payload_subpath += "PAYLOADDDD"
                if idx < not_match_idx_for_path_x:
                    if path_x_subpath[idx] + '/' in path_x:
                        payload_subpath += path_x_subpath[idx] + '/'
                    elif path_x_subpath[idx] + '-' in path_x:
                        payload_subpath += path_x_subpath[idx] + '-'
                    elif path_x_subpath[idx] + '.' in path_x:
                        payload_subpath += path_x_subpath[idx] + '.'
                    elif path_x_subpath[idx] + '~' in path_x:
                        payload_subpath += path_x_subpath[idx] + '~'
                    else:
                        payload_subpath += path_x_subpath[idx]
            continually_shared_parts_of_subpath_after_non_matching_part = ""
            smallest_number_of_not_match_idx_part = min(len(path_x_subpath),len(path_y_subpath))
            for idx in range(not_match_idx_for_path_x + 1, smallest_number_of_not_match_idx_part, 1):
                if path_x_subpath[idx] == path_y_subpath[idx]:
                    if '/' + path_x_subpath[idx] in path_x:
                        continually_shared_parts_of_subpath_after_non_matching_part += '/' + path_x_subpath[idx]
                    elif '-' + path_x_subpath[idx] in path_x:
                        continually_shared_parts_of_subpath_after_non_matching_part += '-' + path_x_subpath[idx]
                    elif '.' + path_x_subpath[idx] in path_x:
                        continually_shared_parts_of_subpath_after_non_matching_part += '.' + path_x_subpath[idx]
                    elif '~' + path_x_subpath[idx] in path_x:
                        continually_shared_parts_of_subpath_after_non_matching_part += '~' + path_x_subpath[idx]
                    else:
                        continually_shared_parts_of_subpath_after_non_matching_part += path_x_subpath[idx]
                else:
                    continually_shared_parts_of_subpath_after_non_matching_part = ""
            payload_subpath += continually_shared_parts_of_subpath_after_non_matching_part
            # if payload_subpath not in paths_permutation_list:
            paths_permutation_list.append(payload_subpath)
    # return payloads_list


    
    # log_file = open("chars_in_values_finder.log", "a")
    # log_file.write("Finished " + str(counter.value) + "/" + str(paths_len) + "\n")
    # log_file.close()
    
    # with counter.get_lock():
    #     counter.value += 1

parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument('-ah', '--all-hosts', action='store_true', help='curate paths pattern for all hosts')
parser.add_argument("-iv", "--in-value", required=False, help="the string(s) to look for in the value of request's host header. when supplying strings, separate them by ','")
parser.add_argument("-mv", "--match-value", required=False, help="the string(s) to look for that equal to value of request's host header. when supplying strings, separate them by ','")
parser.add_argument("-uf", "--urls-file", required=False, help="urls file to add in the search")
parser.add_argument("-kd", "--katana-directory", required=False, help="a directory that has the outputs of katana to parse as requests")
parser.add_argument("-kmhv", "--katana-match-host-value", required=False, help="test requests that are parsed from katana's output with matching host to this value")
parser.add_argument("-kihv", "--katana-in-host-value", required=False, help="test requests that are parsed from katana's output with host that contain this value")

args = parser.parse_args()

if args.in_value == None and args.match_value == None and args.all_hosts == False:
    print("you need to either specify -iv/--in-value or -mv/--match-value or -ah/--all-hosts")

manager = multiprocessing.Manager()
counter = multiprocessing.Value('i',1)
paths = manager.list()
paths_permutation_list = manager.list()

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

unique_reqs_check = dict()

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

                if (f"{parsed_request['method']}_{'_'.join(get_all_keys(parsed_request['queries']))}" not in unique_reqs_check[parsed_request["headers"]["Host"]["value"]]) or (type(parsed_request["body"]) is dict and len(list(parsed_request["body"].keys())) > 0 and f"{parsed_request['method']}_{'_'.join(get_all_keys(parsed_request['body']))}" not in unique_reqs_check[parsed_request["headers"]["Host"]["value"]]):
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

                            # unique_reqs_check[action_hostname].append(f"{form['method']}_{'_'.join(get_all_values(form['parameters']))}")
                    except:
                        print("error parsing:")
                        print(form)
                        # exit()

if args.urls_file:
    with open(args.urls_file, 'r', encoding='utf-8') as urls:
        for url in urls:
            url = url.strip()
            path = extract_path(url)
            queries = extract_query_parameters(url)

            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            headers = dict()
            headers["Host"] = dict()
            headers["Host"] = {'value': hostname}
            
            http_data = {
                'method': "GET",
                'path': path,
                'queries': queries,
                'headers': headers,
                'body': ""
            }

            reqs.append(http_data)

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

hosts_and_their_paths = dict()
if not args.all_hosts:
    if args.in_value:
        args.in_value = args.in_value.split(",")

        for host_value in args.in_value:
            for req in reqs:
                req_host = req["headers"]["Host"]["value"]
                if host_value in req_host:
                    req_path = req["path"]
                    if req_host not in hosts_and_their_paths.keys():
                        hosts_and_their_paths[req_host] = list()
                    if req_path not in hosts_and_their_paths[req_host]:
                        hosts_and_their_paths[req_host].append(req_path)

    if args.match_value:
        args.match_value = args.match_value.split(",")

        for host_value in args.match_value:
            for req in reqs:
                req_host = req["headers"]["Host"]["value"]
                if host_value == req_host:
                    req_path = req["path"]
                    if req_host not in hosts_and_their_paths.keys():
                        hosts_and_their_paths[req_host] = list()
                    if req_path not in hosts_and_their_paths[req_host]:
                        hosts_and_their_paths[req_host].append(req_path)
else:
    for req in reqs:
        req_host = req["headers"]["Host"]["value"]
        req_path = req["path"]
        if req_host not in hosts_and_their_paths.keys():
            hosts_and_their_paths[req_host] = list()
        if req_path not in hosts_and_their_paths[req_host]:
            hosts_and_their_paths[req_host].append(req_path)

for host, host_paths in copy.deepcopy(hosts_and_their_paths).items():
    new_paths = set(host_paths)
    for path in host_paths:
        subpaths = path.split("/")

        new_path = path
        for subpath in subpaths:
            new_path = new_path.replace(subpath, humps.kebabize(subpath).replace("-","~"))
        new_paths.add(new_path)

    hosts_and_their_paths[host] = list(new_paths)

for host,host_paths in hosts_and_their_paths.items():
    
    paths = manager.list()
    paths.extend(host_paths)
    paths_permutation_list = manager.list()

    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        pool.map(paths_permutation, paths, chunksize=1)
    
    # paths_permutation_list = list(set(paths_permutation_list))

    with open(f"pw_{host}.txt", "w") as output:
        for path in paths_permutation_list:
            output.write(f"{path}\n")



# requests_len = len(reqs)

# with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
#     pool.map(permutate_and_send_request, resps, chunksize=1)

#pw_api.example.com.txt

# resps_headers_keys = set(resps_headers_keys)
