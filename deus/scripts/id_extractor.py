import os
import subprocess
import json
from http_parser.parser import HttpParser
import argparse
from urllib.parse import urlparse, parse_qs, parse_qsl, quote, unquote
import re
from homoglyphs import Homoglyphs

parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument("-ik", "--interested-key", required=False, help="what a key should contain, like id for example")
args = parser.parse_args()


# Initialize the Homoglyphs object (using default settings)
hg = Homoglyphs()

def get_unicode_homoglyph(_string):
    
    for ch_idx in range(0, len(_string)):
        for combos in hg.get_combinations(_string[ch_idx]):
            for combo in combos:
                if combo != _string[ch_idx]:
                    _string = _string[:ch_idx] + combo  + _string[ch_idx + 1:]
                    
                    
                    return _string

    return _string

# 3. Get Escaped Unicode Representation
def get_escaped_unicode(_string):
    """
    Returns the Unicode escape sequence for the given character.
    For example, 'a' becomes '\\u0061'.
    """
    ch = _string[0]
    code = ord(ch)
    # For code points in the BMP, use 4-digit escape; for others, use 8-digit escape.
    if code <= 0xFFFF:
        new_char = f"\\u{code:04x}"
    else:
        new_char = f"\\U{code:08x}"
    
    _string = new_char + _string[1:]

    return _string

# 4. Get Opposite Character Case
def get_opposite_case(_string):
    """
    Returns the opposite case of the given character.
    If the character is lowercase, it is converted to uppercase, and vice versa.
    Non-alphabetical characters are returned unchanged.
    """
    
    for ch_idx in range(0, len(_string)):
        ch = _string[ch_idx]
        if ch.isdigit():
            continue

        if ch.islower():
            new_char =  ch.upper()

            _string = _string[0:ch_idx]  + new_char + _string[ch_idx + 1:]
            break
        elif ch.isupper():
            new_char = ch.lower()
            _string = _string[0:ch_idx]  + new_char + _string[ch_idx + 1:]
            break
    
    return _string


def get_permutations(_string):
    perms = set()
    if (type(_string) == str and not _string) or not (type(_string) == int or type(_string) == str):
        return perms

    _string = str(_string)
    
    perms.add(get_unicode_homoglyph(_string))
    perms.add(get_escaped_unicode(_string))
    perms.add(get_opposite_case(_string))

    perms.discard(_string)

    return perms


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
        print("An exception occurred:", e)

unpack_burp_output = list()
for burp_file in os.listdir('./input'):
    if os.path.exists("/home/deus/downloads"):
        subprocess.run(f"php /home/deus/downloads/unpack-burp/unpack-burp.php ./input/{burp_file} all > unpack_burp_output.txt", shell=True)
    else:
        subprocess.run(f"php /home/kali/Downloads/unpack-burp/unpack-burp.php ./input/{burp_file} all > unpack_burp_output.txt", shell=True)


    with open('unpack_burp_output.txt', 'r') as file:
        unpack_burp_output.extend(file.read().split("\n\n"))

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
keys_to_avoid = list()
def get_all_values(d, interested_key=""):
    global keys_to_avoid
    values = []
    if isinstance(d, dict):
        for k, v in d.items():
            if interested_key and any(ik.lower() in k.lower() for ik in interested_key.split(",")):
                if type(v) is int or (type(v) is str and " " not in v):
                    if keys_to_avoid.count(k) < 3:
                        values.append(v)
                        keys_to_avoid.append(k)
            # else:
            #     if type(v) is int or (type(v) is str and " " not in v):
            #         values.append(v)
            if isinstance(v, dict) or isinstance(v, list):
                values.extend(get_all_values(v, interested_key))
            else:
                json_obj, escaped_or_unescaped = process_and_load_json(v)
                if isinstance(json_obj, dict) or isinstance(json_obj, list):
                    values.extend(get_all_values(json_obj, interested_key))
    elif isinstance(d, list):
        for v in d:
            if isinstance(v, dict) or isinstance(v, list):
                values.extend(get_all_values(v, interested_key))
            else:
                json_obj, escaped_or_unescaped = process_and_load_json(v)
                if isinstance(json_obj, dict) or isinstance(json_obj, list):
                    values.extend(get_all_values(json_obj, interested_key))
    return values
# count = 0
ids = list()
for request_and_response in unpack_burp_output:
    if request_and_response == '':
        continue
    
    request_and_response = json.loads(request_and_response)
    
    # if  args.avoid_path != None and any(avoid_path in request_and_response["reqp"] for avoid_path in args.avoid_path):
    #     continue
    
    req_text = request_and_response["reqp"].replace("HTTP/2","HTTP/1.1") + "\r\n" + request_and_response["reqh"] + "\r\n\r\n" + request_and_response["reqb"]
    
    parsed_request = parse_http(req_text)
    if parsed_request and parsed_request['method'] and 'headers' in parsed_request.keys() and 'Host' in parsed_request['headers'].keys() and 'value' in parsed_request['headers']['Host'].keys():
        try:
            if args.interested_key:
                resb_values = get_all_values(json.loads(request_and_response["resb"]), args.interested_key)
            else:
                resb_values = get_all_values(json.loads(request_and_response["resb"]))
            
            # print(resb_values)
            # exit()
            ids.extend(resb_values)
            # print(resb_values)
            # print(payloads)
            # if count == 13:
            #     exit()
            # count += 1
            # print(payloads)
            # exit()
        except Exception as e:
            # print(f"An ignored error occurred while parsing resb: {e}")
            pass
        
    else:
        print(req_text)

ids = list(set(map(str, ids)))
print("\n".join(map(str, ids)))

for _id in ids:
    for perm in get_permutations(str(_id)):
        print(perm)


# exit()