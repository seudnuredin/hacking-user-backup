import os
import subprocess
import json
from http_parser.parser import HttpParser
import argparse
from urllib.parse import urlparse, parse_qs, parse_qsl, quote, unquote, urlencode, urlunparse
import re

parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument("-bp", "--burp-pair", required=True, help="what a key should contain, like id for example")
parser.add_argument("-l", "--limit", required=True, type=int ,help="limiting the number of values it returns for each type")
args = parser.parse_args()


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
        # if args.header != None and args.header[0] not in list(headers.keys()):
        #     headers[args.header[0]] = args.header[1]
        
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

# Example usage:
key_value_pair = []
unique_path = set()

if args.burp_pair:
    unpack_burp_output = list()
    # for burp_file in os.listdir('./input'):
    if os.path.exists("/home/deus/scripts") and not os.path.exists("/home/kali/Downloads"):
        subprocess.run(f"php /home/deus/scripts/unpack-burp/unpack-burp.php {args.burp_pair} all > unpack_burp_output.txt", shell=True)
    else:
        subprocess.run(f"php /home/kali/Downloads/unpack-burp/unpack-burp.php {args.burp_pair} all > unpack_burp_output.txt", shell=True)


    with open('unpack_burp_output.txt', 'r') as file:
        unpack_burp_output.extend(file.read().split("\n\n"))
    
    for request_and_response in unpack_burp_output:
        if request_and_response == '':
            continue
        
        request_and_response = json.loads(request_and_response)

        # if  args.avoid_path != None and any(avoid_path in request_and_response["reqp"] for avoid_path in args.avoid_path):
        #     continue

        req_text = request_and_response["reqp"].replace("HTTP/2","HTTP/1.1") + "\r\n" + request_and_response["reqh"] + "\r\n\r\n" + request_and_response["reqb"]

        

        parsed_request = parse_http(req_text)
        if not parsed_request:
            continue
        
        if parsed_request["path"] in unique_path:
            continue

        unique_path.add(parsed_request["path"])

        if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
            try:
                # parsed_request["resb"] = get_all_keys_with_their_value(json.loads(request_and_response["resb"]))
                # for pair in parsed_request["resb"]:
                #     if key_count_in_key_value_pair(list(pair.keys())[0]) < 4:
                #         key_value_pair.append(pair)
                
                key_value_pair.append(json.loads(request_and_response["resb"]))

                # if args.include_other_reqs_params:
                #     for param in get_all_keys(parsed_request["resb"]):
                #         if param not in params:
                #             params.append(param)
                
            except Exception as e:
                # print(f"An ignored error occurred while parsing resb: {e}")
                pass
            if parsed_request["body"]:
                # for param in get_all_keys(parsed_request["body"]):
                #     if param not in params:
                #         params.append(param)
                # for pair in get_all_keys_with_their_value(parsed_request["body"]):
                #     if key_count_in_key_value_pair(list(pair.keys())[0]) < 4:
                #         key_value_pair.append(pair)
                
                # key_value_pair.extend(get_all_keys_with_their_value(parsed_request["body"]))
                key_value_pair.append(parsed_request["body"])

            if parsed_request["queries"]:
                # for param in get_all_keys(parsed_request["queries"]):
                #     if param not in params:
                #         params.append(param)

                # for pair in get_all_keys_with_their_value(parsed_request["queries"]):
                #     if key_count_in_key_value_pair(list(pair.keys())[0]) < 4:
                #         key_value_pair.append(pair)

                # key_value_pair.extend(get_all_keys_with_their_value(parsed_request["queries"]))
                key_value_pair.append(parsed_request["queries"])

        else:
            print(req_text)
            # pass


# Get the top 2 keys for each type, with their associated value.
result = most_common_keys_values_by_type(key_value_pair, n=args.limit)
for t, entries in result.items():
    # print(f"For type {t}:")
    if entries:
        for key, value in entries:
            if type(value) is dict or type(value) is list:
                print(json.dumps(value).replace(" ",""))
            else:
                print(value)
            # print(f"  key '{key}' with value {value}")
    else:
        print("no entries found")
