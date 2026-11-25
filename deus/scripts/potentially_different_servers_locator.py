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

def extract_headers(headers_str):
    headers = {}
    for subdomain in headers_str.split("\n"):
        if ': ' in subdomain:
            key, value = subdomain.split(': ', 1)
            headers[key] = value.strip()
    return headers


def permutate_and_send_request(res_headers):
    global counter
    global responses_headers_len
    global resps
    global resps_headers_keys
    
    
    
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
    
    res_headers_keys = get_all_keys(res_headers)
    for header_key in res_headers_keys:
        
        if header_key not in resps_headers_keys:
            resps_headers_keys.append(header_key)

    
    log_file = open("chars_in_values_finder.log", "a")
    log_file.write("Finished " + str(counter.value) + "/" + str(responses_headers_len) + "\n")
    log_file.close()
    
    with counter.get_lock():
        counter.value += 1

manager = multiprocessing.Manager()
counter = multiprocessing.Value('i',1)
resps_headers_keys = manager.list()

unpack_burp_output = list()
for burp_file in os.listdir('./input'):
    if os.path.exists("/home/deus/downloads"):
        subprocess.run(f"php /home/deus/downloads/unpack-burp/unpack-burp.php ./input/{burp_file} jsonres > unpack_burp_output.txt", shell=True)
    else:
        subprocess.run(f"php /home/kali/Downloads/unpack-burp/unpack-burp.php ./input/{burp_file} jsonres > unpack_burp_output.txt", shell=True)


    with open('unpack_burp_output.txt', 'r') as file:
        unpack_burp_output.extend(file.read().split("\n\n"))

resps = list()

for request_and_response in unpack_burp_output:
    if request_and_response == '':
        continue
    request_and_response = json.loads(request_and_response)
    response_headers = extract_headers(request_and_response["resh"])

    # print(response_headers)
    # print()
    # print()
    # print()
    # print(type(response_headers))
    # exit()

    resps.append(response_headers)
    

responses_headers_len = len(resps)

with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
    pool.map(permutate_and_send_request, resps, chunksize=1)


resps_headers_keys = set(resps_headers_keys)

with open("potentially_different_servers_locator_output.txt", "a") as output:
    for header_key in resps_headers_keys:
        output.write(f"{header_key} \n")