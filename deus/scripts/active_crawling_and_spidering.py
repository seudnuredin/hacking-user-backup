import multiprocessing
try:
   multiprocessing.set_start_method('fork', force=True)
   print("forked")
except RuntimeError:
    print("unable to fork!")
    exit()
import requests
import subprocess
import argparse
from urllib.parse import urlparse, parse_qs, parse_qsl, quote, unquote, urlencode, urlunparse
from collections import Counter
import os
import copy
from http_parser.parser import HttpParser
import glob
import threading
import json
import re
import shlex
import sys
import tldextract
import signal
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from collections import defaultdict
from ipwhois import IPWhois
from ipwhois.exceptions import IPDefinedError
import socket
import random

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



def group_urls_by_hostname(urls):
    grouped = defaultdict(list)
    for url in urls:
        hostname = urlparse(url).hostname
        if hostname:
            grouped[hostname].append(url)
    return grouped

def extract_domain_tld_from_file(file_path):
    result = set()
    with open(file_path, 'r') as f:
        for line in f:
            url = line.strip()
            if not url:
                continue
            ext = tldextract.extract(url)
            if ext.domain and ext.suffix:
                result.add(f"{ext.domain}.{ext.suffix}")
    return result

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

def has_query_params(url):
    parsed_url = urlparse(url)
    return bool(parsed_url.query)

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
        # pass

def check_url(url):
    global proxy_setting_lock
    global used_proxies_across_processes
    global proxies
    global field_scope_domains

    # proxy = ""
    with proxy_setting_lock:
        # proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
        counter1 = Counter(proxies)
        counter2 = Counter(used_proxies_across_processes)
        result_counter = counter1 - counter2
        result = list(result_counter.elements())
        proxy = result[0]

        used_proxies_across_processes.append(proxy)
    
    headers = {}
    with req_lock:
        if args.request_file != None:
                
            headers = extract_headers(args.request_file)
            queries = extract_query_parameters_from_file(args.request_file)

            if headers:
                with open(header_file_name, "w") as file:
                    for key, value in headers.items():
                        file.write(f"{key}: {value}\n")
                
                # katana_headers = f"-H {header_file_name}"
            
            if queries:
                url = add_query_params(url, queries)
    
    # Set proxy
    proxies_for_request = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}'
    } if proxy != "self" else None

    """Check if the URL returns a 200 status code."""
    working_url = False
    try:
        response = requests.get(url, headers=headers, timeout=10, proxies=proxies_for_request, verify=False)

        if response.status_code == 200:
            working_url = True
        elif 10 <= response.status_code < 400:
            redirect_url = response.headers.get('Location')
            if bool(re.search(field_scope_domains, redirect_url)):
                working_url = True
        
    except Exception as e:
        # Print the exception
        print("An exception occurred:", e)
    
    with proxy_setting_lock:
        used_proxies_across_processes.remove(proxy)
    

    if working_url:
        return url
    else:
        return None

def process_urls(url_list):
    """Process a list of URLs to check their status codes."""
    # with multiprocessing.Manager() as manager:
    resolved_urls = manager.list()  # Shared list for storing resolved URLs
    # with multiprocessing.Pool(processes=4) as pool:  # Adjust the number of processes as needed
    pool = multiprocessing.Pool(len(proxies))
    results = pool.map(check_url, url_list, chunksize=1)
        
    # Add non-None results to resolved_urls
    for url in results:
        if url:
            resolved_urls.append(url)
    
    return list(resolved_urls)


def split_list(lst, n):
    """
    Splits a list into a list of lists, with each sublist containing `n` elements.

    :param lst: The original list to be split.
    :param n: The number of elements per sublist.
    :return: A list of sublists.
    """
    return [lst[i:i+n] for i in range(0, len(lst), n)]

stop_event = threading.Event()
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

parser = argparse.ArgumentParser(description="Run feroxbuster with specified URL, request file, and methods.")
parser.add_argument("-u", "--url", required=False, help="url of target page")
parser.add_argument("-ul", "--url-list", required=False, help="file of target page URLS")
parser.add_argument("-rsl", "--requests-list", required=False, help="obtain requests out of a list of reqs json")
parser.add_argument("-rc", "--rate-config", required=False, help="Path to the rate config.")
parser.add_argument('-rl', '--rate-limit', type=int, help='Limit number of katana to instantiate')
parser.add_argument('-krl', '--katana-rate-limit', default=1, type=int, help='Limit number of requests per second for katana')
parser.add_argument('-kp', '--katana-parallel', default=1, type=int, help='number of urls to processes at once for katana')
parser.add_argument('-p', '--parallel', type=int, help='number of urls to supply to katana per executing it. useful for updating sessions tokens')
parser.add_argument('-np', '--no-proxy', action='store_true', help='don\'t use proxies and instead use the server ip')
parser.add_argument('-os', '--only-sub', action='store_true', help='only crawl subpages')
parser.add_argument('-oh', '--only-home', action='store_true', help='only crawl homepages')
parser.add_argument('-ns', '--no-scope', action='store_true', help='no host based scope')
parser.add_argument('-njo', '--no-json-output', action='store_true', help='no json output from katana')
parser.add_argument('-nhl', '--no-headless', action='store_true', help='dont supply headless to katana')
parser.add_argument('-sd', '--sub-depth', default=2, type=int, help='depth for subpages')
parser.add_argument('-cd', '--crawl-duration', required=True, help='supplied to katana\'s crawl duration arg')
parser.add_argument('-d', '--delay', type=int, required=False, help='delay between requests')
# parser.add_argument('-H', '--headers', required=False, help='file that has headers to include in katana requests to the target')
parser.add_argument('-H', '--header', required=False, help='a header to add all requests like -H "X-Hackerone: seudxs"')
parser.add_argument("-r", "--request-file", required=False, help="Path to the request file containing headers.")
parser.add_argument('-ts', '--token-script', required=False, help='a python script to execute to generate new authorization keys')
parser.add_argument('-te', '--token-expiration', type=int, required=False, help='executes token script everytime token expiration time in minutes is reached')
parser.add_argument('-cos', '--crawl-out-scope', required=False, help='crawl out of scope for katana')
parser.add_argument('-cs', '--crawl-scope', required=False, help='crawl scope for katana')
parser.add_argument('-fs', '--field-scope', required=False, help='field scope file of urls to extract apex domains from for katana')
args = parser.parse_args()



default_out_of_scope = ["/logout",
"/signout",
"/sign-out",
"/log-out",
"/sign_out",
"/log_out",
"/deleteuser",
"/blog",
"/wp-content"]



with open("/home/deus/documents/katana_out_of_scope.txt", "w") as katana_out_of_scope_file:
    for dos in default_out_of_scope:
        katana_out_of_scope_file.write(f"{dos}\n")
    
    if args.crawl_out_scope:
        for cos in args.crawl_out_scope.split(","):
            katana_out_of_scope_file.write(f"{cos}\n")

if args.crawl_scope:
    with open("/home/deus/documents/katana_in_scope.txt", "w") as katana_out_of_scope_file:
        # if args.crawl_scope:
        for cs in args.crawl_scope.split(","):
            katana_out_of_scope_file.write(f"{cs}\n")

if args.field_scope:
    apex_domains = extract_domain_tld_from_file(args.field_scope)
    field_scope_domains = "(" + "|".join(sorted(apex_domains)) + ")"

if args.token_expiration != None and args.token_script == None:
    print("token script argument not supplied")
    exit(1)

if args.token_expiration == None and args.token_script != None:
    print("token script argument not supplied")
    exit(1)

if args.url_list == None and args.requests_list == None and args.url == None:
    print("you must supply either url, urls or requests list")
    exit(1)

if args.header != None:
    args.header = args.header.split(":")



urls = []
home_of_urls = []
manager = multiprocessing.Manager()
used_proxies_across_processes = manager.list()
proxy_setting_lock = multiprocessing.Lock()
req_lock = multiprocessing.Lock()

if args.token_expiration != None:
    args.token_expiration = args.token_expiration * 60
    # token_loop()
    threading.Thread(target=token_loop, daemon=True).start()

page_urls = list()

if args.url:
    page_urls.append(args.url)

if args.url_list:
    with open(args.url_list, 'r') as page_urls_file:
        for page_url in page_urls_file:
            page_url = page_url.strip()
            page_urls.append(page_url)

if len(page_urls) == 0:
    print("no url was given!")
    exit()

if args.requests_list:
    with open(args.requests_list, 'r') as json_file:
        args.requests_list = json.load(json_file)
    
    for req in args.requests_list:
        parsed_request = parse_http(req)
        if not parsed_request or parsed_request["method"] != "GET":
            continue
        
        url = f"https://{parsed_request['headers']['Host']['value'].strip()}{parsed_request['path'].strip()}"
        
        query_string = ""
        if parsed_request['queries']:
            query_string = safe_urlencode(parsed_request['queries'])
        if query_string:
            url = url + f"?{query_string}"
        
        page_urls.append(url)

        # reqs.append(parsed_request)

# print(page_urls)
# exit()

for page_url in page_urls:   
    if page_url not in urls:
        urls.append(page_url)
    
    parsed_url = urlparse(page_url)
    url_port = ""
    if parsed_url.port:
        url_port = ":" + str(parsed_url.port)
    
    parsed_page_url_netloc = parsed_url.scheme + '://' + parsed_url.netloc.split(":")[0] + url_port
    if parsed_page_url_netloc not in home_of_urls:
        home_of_urls.append(parsed_page_url_netloc)



if args.no_scope:
    args.no_scope = "-ns"
else:
    args.no_scope = ""
    
if args.field_scope:
    args.field_scope = f"-fs {field_scope_domains}"
else:
    args.field_scope = ""
    
args.crawl_out_scope = "-cos /home/deus/documents/katana_out_of_scope.txt"

if args.crawl_scope:
    args.crawl_scope = "-cs /home/deus/documents/katana_in_scope.txt"
else:
    args.crawl_scope = ""

if args.crawl_duration:
    args.crawl_duration = f"-ct {args.crawl_duration}"
else:
    args.crawl_duration = ""

if args.no_headless:
    args.no_headless = ""
else:
    args.no_headless = "-hl"

# proxies = []
# if args.no_proxy:
#     proxies.append("self")
# else:
#     proxies.append("127.0.0.1:8080")
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

# set up working urls
# urls = list(set(process_urls(urls)))
# home_of_urls = list(set(process_urls(home_of_urls)))

urls = list(set(urls))
home_of_urls = list(set(home_of_urls))




def extract_query_parameters_from_file(file_path):
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

def count_lines(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f)

def cookie_handler(cookie_value, urls):
    service = Service(executable_path="/home/deus/scripts/chromedriver")
    parts = [v.strip() for v in cookie_value.split(';')]
    params = {}
    for param in parts:
        key, val = param.split('=', 1)
        params[key.strip()] = val.strip()
    

    profile_dir = os.path.abspath("chrome_profile")
    os.makedirs(profile_dir, exist_ok=True)

    options = Options()
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--headless")  # Optional
    options.binary_location = "/home/deus/.cache/rod/browser/chromium-1131003/chrome"

    driver = webdriver.Chrome(service=service,options=options)

    seen_hostnames = set()
    unique_urls = []
    for url in urls:
        hostname = urlparse(url).hostname
        if hostname not in seen_hostnames:
            seen_hostnames.add(hostname)
            unique_urls.append(url)
    
    for url in unique_urls: 
        # You must visit the domain first before setting cookies
        hostname = urlparse(url).hostname
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.url_contains(hostname))

        for key, value in params.items():
            driver.delete_cookie(key)  # optional, but safer

            driver.add_cookie({'name':key, 'value': value, 'domain': hostname, 'path': '/','secure': True, 'httpOnly': True, 'sameSite': 'None', 'expiry': int(time.time()) + 86400})

        driver.refresh()

    driver.quit()

    return profile_dir



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
        


# def get_proxy_port(hostname, rate_limit):

#     available_port = ""
#     available_user_agent = ""

#     ports = list(range(8000, 9000))
#     random.shuffle(ports)

#     for port in ports:
#         if is_port_available(port):
#             available_port = port
#             break
        
    
    
#     mimick_users = response_has_cookies(hostname)

#     if mimick_users:

#         domain_arg = f"--domain {hostname}"


        

#         if rate_limit < 190:
#             rate_limit += 5
        
#         user_count_arg = f"-u {rate_limit}"


#         for user_agent in user_agents:
#             if user_agent not in used_user_agents:
#                 used_user_agents.add(user_agent)
#                 user_agent_arg = f"-g {user_agent}"

#     else:
#         domain_arg = ""
#         user_count_arg = ""
#         user_agent_arg = ""
    
#     rota_proc = subprocess.Popen(
#         ["rota", "--config", "/home/deus/documents/rota_config.yml",*shlex.split(domain_arg),*shlex.split(user_count_arg),*shlex.split(user_agent_arg), "-p", f"{available_port}"],
#         stdout=subprocess.DEVNULL,
#         stderr=subprocess.DEVNULL,
#         preexec_fn=os.setsid
#     )


#     if user_count_arg:
#         user_count_arg_time = (int(user_count_arg.split(" ")[1]) / 10) * 5
#         time_slept = 0
    
#     while is_port_available(available_port):
#         time.sleep(5)
        
#         if user_count_arg:
#             time_slept += 5
#             if user_count_arg_time + 60 < time_slept:
#                 domain_arg = ""
#                 user_count_arg = ""
#                 user_agent_arg = ""
#                 rota_exit_handler(rota_proc)
#                 rota_proc = subprocess.Popen(
#                     ["rota", "--config", "/home/deus/documents/rota_config.yml",*shlex.split(domain_arg),*shlex.split(user_count_arg),*shlex.split(user_agent_arg), "-p", f"{available_port}"],
#                     stdout=subprocess.DEVNULL,
#                     stderr=subprocess.DEVNULL,
#                     preexec_fn=os.setsid
#                 )


#                 while is_port_available(available_port):
#                     time.sleep(5)
                
#                 break


#     # while is_port_available(available_port):
#     #     time.sleep(5)
    
#     return available_port, rota_proc      

def execute_with_log_watch(command, log_path, timeout_minutes=2):
    # Start the subprocess
    process = subprocess.Popen(
        command,
        preexec_fn=os.setsid,  # Allows killing the whole process group
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    with open("log.txt", "a") as file:
        file.write(f"Started process with PID {process.pid} {command}\n")

    try:
        last_size = os.path.getsize(log_path) if os.path.exists(log_path) else 0
        last_change = time.time()

        # with open("log.txt", "a") as file:
        #     file.write(f"log 2\n")

        while True:
            time.sleep(10)  # Check every 10 seconds
            if not os.path.exists(log_path):
                continue

            # with open("log.txt", "a") as file:
            #     file.write(f"log 3\n")

            current_size = os.path.getsize(log_path)
            if current_size != last_size:
                last_size = current_size
                last_change = time.time()

            # with open("log.txt", "a") as file:
            #     file.write(f"log 4\n")

            # If no change in file for more than timeout
            if time.time() - last_change > timeout_minutes * 60:
                with open("log.txt", "a") as file:
                    file.write(f"No change in log for {timeout_minutes} minutes. Terminating process...\n")

                process.kill()
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                break

            # If process has already exited
            if process.poll() is not None:
                with open("log.txt", "a") as file:
                    file.write("Process completed on its own.\n")
                break

    except Exception as e:
        with open("log.txt", "a") as file:
            file.write(f"errrror {e}\n")
        
        process.kill()
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)

    process.wait(timeout=10)
    with open("log.txt", "a") as file:
        file.write("Process finished.\n")

def katana_for_main(home_of_url):
    global proxy_setting_lock
    global used_proxies_across_processes
    global proxies
    global home_of_urls
    global args
    global previous_output_count
    global req_lock
    global instance_count

    default_crawl_scope = copy.copy(args.crawl_scope)

    
    # rota_proc = subprocess.Popen(
    #     ["rota", "--config", "/home/deus/documents/rota_config.yml"],
        
    #     preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    # )
    # time.sleep(5)

    current_output_count = instance_count + previous_output_count
    header_file_name = f"headers.txt"
    katana_headers = ""

    with proxy_setting_lock:
        # proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
        counter1 = Counter(proxies)
        counter2 = Counter(used_proxies_across_processes)
        result_counter = counter1 - counter2
        result = list(result_counter.elements())
        proxy = result[0]
        
        used_proxies_across_processes.append(proxy)

    chrome_data_dir = ""
    def fill_input(home_of_url):
        nonlocal katana_headers
        with req_lock:
            if args.request_file != None:
                
                headers = extract_headers(args.request_file)
                queries = extract_query_parameters_from_file(args.request_file)
    
                if headers:
                    with open(header_file_name, "w") as file:
                        for key, value in headers.items():
                            if key == "Cookie" and args.no_headless:
                                chrome_data_dir = f"-noi -cdd {cookie_handler(value, [home_of_url])}"
                            else:
                                file.write(f"{key}: {value}\n")
                    
                    katana_headers = f"-H {header_file_name}"
                
                with open("home_of_urls.txt", "w") as file:
                    # for home_of_url in splitted_urls:
                    if queries:
                        home_of_url = add_query_params(home_of_url, queries)
    
                    file.write(f"{home_of_url}\n")
    
                    
                # update_dict_with_matches(perm_req["queries"], queries)
                # update_dict_with_matches(perm_req["headers"], headers)
    fill_input(home_of_url)
    if proxy != "self":
        proxy_for_katana = f"-proxy http://{proxy}"
    else:
        proxy_for_katana = ""
    
    

    previous_non_ok_urls_count = count_lines("home_of_urls.txt")
    it_count = 0
    
    while True:
    #     subprocess.run([
    #     "katana", *shlex.split(args.no_headless), "-list", "home_of_urls.txt", *shlex.split(proxy_for_katana), *shlex.split(chrome_data_dir), *shlex.split(args.no_scope), *shlex.split(args.field_scope),
    #     *shlex.split(args.crawl_out_scope), *shlex.split(args.crawl_duration), "-p", str(args.katana_parallel), "-rl", str(args.katana_rate_limit), "-c", str(args.katana_rate_limit),
    #     *shlex.split(katana_headers), "-rd", "0", "-d", "4",
    #     "-sr", "-srd", f"./main_{current_output_count}_traffic_{it_count}", "-timeout", "10", "-s" , "breadth-first"
    # ], preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


        rate_config = get_url_rate_config(home_of_url)
        rate_limit = str(min(args.katana_rate_limit, rate_config["rate"] * 10))
    
        execute_with_log_watch([
        "katana", *shlex.split(args.no_headless), "-list", "home_of_urls.txt", *shlex.split(proxy_for_katana), *shlex.split(chrome_data_dir), *shlex.split(args.no_scope), *shlex.split(args.field_scope),
        *shlex.split(args.crawl_out_scope), *shlex.split(args.crawl_duration), "-p", str(args.katana_parallel), "-rl", rate_limit, "-c", rate_limit,
        *shlex.split(katana_headers), "-rd", "0", "-d", "4",
        "-sr", "-srd", f"./main_{current_output_count}_traffic_{it_count}", "-timeout", "10", "-s" , "breadth-first"
    ], f"./main_{current_output_count}_traffic_{it_count}/index.txt", timeout_minutes=2)

        subprocess.run(f"cat ./main_{current_output_count}_traffic_{it_count}/index.txt | awk '$3 != \"(200\" && $3 != \"(OK)\" && $4 != \"OK)\" {{ print $2 }}' | grep -Fx -f home_of_urls.txt | sort -u > home_of_urls_new.txt", shell=True, executable="/bin/bash")
        subprocess.run(f"mv home_of_urls_new.txt home_of_urls.txt", shell=True)

        new_non_ok_urls_count = count_lines("home_of_urls.txt")

        if args.parallel != len(home_of_urls):
            subprocess.run(f"tar -czf ./main_{current_output_count}_traffic_{it_count}.tar.gz ./main_{current_output_count}_traffic_{it_count}", shell=True)
            subprocess.run(f"rm -rf ./main_{current_output_count}_traffic_{it_count}", shell=True)
        
        it_count += 1
        
        if it_count == 3:
            break
        
        if new_non_ok_urls_count <= previous_non_ok_urls_count and new_non_ok_urls_count != 0:
            previous_non_ok_urls_count = new_non_ok_urls_count
        else:
            break

    
    with open("home_of_urls.txt", "w") as file:
        file.write(f"{home_of_url}\n")

    default_scopes = []
    crawled = []

    if args.crawl_scope:
        with open('/home/deus/documents/katana_in_scope.txt', 'r') as file:
            default_scopes = [line.strip() for line in file]
    
    fill_input(home_of_url)
    for depth in range(1, 5):

        if depth != 1: 
            discovered_new_directory = False
            with open("/home/deus/documents/katana_in_scope.txt", "w") as katana_out_of_scope_file:
                for cs in default_scopes:
                    katana_out_of_scope_file.write(f"{cs}\n")
                
                subprocess.run(f"cat ./main_{current_output_count}_traffic_*_{depth - 1}/index.txt | awk '{{ print $2 }}' | grep -F -f <(cat home_of_urls.txt | unfurl domains | sed -e 's/$/\//g'  -e 's/^/\//g') | unfurl paths | awk -F/ -v N={depth} '{{{{segs = NF; if (segs >= N) {{out = \"\"; for (i = 2; i <= N; i++) {{out = out \"/\" $i}} if (segs > N) out = out \"/\"; print out}}}}}}' | grep -v -e // -e ^/$ | sort -u > crawl_scopes.txt", shell=True, executable="/bin/bash")
                subprocess.run(f"cat ./main_{current_output_count}_traffic_*_{depth - 1}/index.txt | awk '{{ print $2 }}' | grep -F -f <(cat home_of_urls.txt | unfurl domains | sed -e 's/$/\//g'  -e 's/^/\//g') | grep -f crawl_scopes.txt | sort -u > home_of_urls_new.txt", shell=True, executable="/bin/bash")
                subprocess.run(f"mv home_of_urls_new.txt home_of_urls.txt", shell=True)

                with open('crawl_scopes.txt', 'r') as file:
                    crawl_scopes = [line.strip() for line in file]
                    for cs in crawl_scopes:
                        if cs not in crawled:
                            katana_out_of_scope_file.write(f"{cs}\n")
                            crawled.append(cs)
                            discovered_new_directory = True
            
            for i in range(0, it_count):
                subprocess.run(f"tar -czf ./main_{current_output_count}_traffic_{i}_{depth - 1}.tar.gz ./main_{current_output_count}_traffic_{i}_{depth - 1}", shell=True)
                subprocess.run(f"rm -rf ./main_{current_output_count}_traffic_{i}_{depth - 1}", shell=True)

            if discovered_new_directory:
                args.crawl_scope = "-cs /home/deus/documents/katana_in_scope.txt"
            else:
                break

        previous_non_ok_urls_count = count_lines("home_of_urls.txt")
        it_count = 0
        while True:
            
        #     subprocess.run([
        #     "katana", *shlex.split(args.no_headless), "-list", "home_of_urls.txt", *shlex.split(proxy_for_katana), *shlex.split(chrome_data_dir), *shlex.split(args.no_scope), *shlex.split(args.field_scope),
        #     *shlex.split(args.crawl_out_scope), "-p", str(args.katana_parallel), "-rl", str(args.katana_rate_limit), "-c", str(args.katana_rate_limit),
        #     *shlex.split(katana_headers), "-rd", "0", "-d", "1",
        #     "-sr", "-srd", f"./main_{current_output_count}_traffic_{it_count}_{depth}", "-timeout", "10"
        # ], preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            rate_config = get_url_rate_config(home_of_url)
            rate_limit = str(min(args.katana_rate_limit, rate_config["rate"] * 10))

            execute_with_log_watch([
            "katana", *shlex.split(args.no_headless), "-list", "home_of_urls.txt", *shlex.split(proxy_for_katana), *shlex.split(chrome_data_dir), *shlex.split(args.no_scope), *shlex.split(args.field_scope),
            *shlex.split(args.crawl_out_scope), "-p", str(args.katana_parallel), "-rl", rate_limit, "-c", rate_limit,
            *shlex.split(katana_headers), "-rd", "0", "-d", "1",
            "-sr", "-srd", f"./main_{current_output_count}_traffic_{it_count}_{depth}", "-timeout", "10"], f"./main_{current_output_count}_traffic_{it_count}_{depth}/index.txt", timeout_minutes=2)

        
    
    
            subprocess.run(f"cat ./main_{current_output_count}_traffic_{it_count}_{depth}/index.txt | awk '$3 != \"(200\" && $3 != \"(OK)\" && $4 != \"OK)\" {{ print $2 }}' | grep -Fx -f home_of_urls.txt | sort -u > home_of_urls_new.txt", shell=True, executable="/bin/bash")
            subprocess.run(f"mv home_of_urls_new.txt home_of_urls.txt", shell=True)
    
            new_non_ok_urls_count = count_lines("home_of_urls.txt")
            
            it_count += 1
            
            if it_count == 3:
                break
            
            if new_non_ok_urls_count <= previous_non_ok_urls_count and new_non_ok_urls_count != 0:
                previous_non_ok_urls_count = new_non_ok_urls_count
            else:
                break
        
        if depth == 4:
            for i in range(0, it_count):
                subprocess.run(f"tar -czf ./main_{current_output_count}_traffic_{i}_{depth}.tar.gz ./main_{current_output_count}_traffic_{i}_{depth}", shell=True)
                subprocess.run(f"rm -rf ./main_{current_output_count}_traffic_{i}_{depth}", shell=True)
            
        
        
        
        # subprocess.run(f"rsync -a --remove-source-files ./main_*_traffic/ merged_output/", shell=True)

    # if args.no_json_output:
    #     subprocess.run(f"rm ./main_{current_output_count}.json", shell=True)

    with open("/home/deus/documents/katana_in_scope.txt", "w") as katana_out_of_scope_file:
        for cs in default_scopes:
            katana_out_of_scope_file.write(f"{cs}\n")

    args.crawl_scope = default_crawl_scope

    with proxy_setting_lock:
        used_proxies_across_processes.remove(proxy)
    
    # rota_exit_handler(rota_proc)

def katana_for_sub(splitted_urls):
    global proxy_setting_lock
    global used_proxies_across_processes
    global proxies
    global urls
    global args
    global previous_output_count
    global req_lock
    global instance_count

    
    default_crawl_scope = copy.copy(args.crawl_scope)

    # rota_proc = subprocess.Popen(
    #     ["rota", "--config", "/home/deus/documents/rota_config.yml"],
        
    #     preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    # )
    # time.sleep(5)
    
    # with open("home_of_url.txt", "w") as file:
    #     for home_of_url in home_of_urls:
    #         file.write(f"{home_of_url}\n")
    
    # current_output_count = urls.index(url) + previous_output_count
    current_output_count = instance_count + previous_output_count
    header_file_name = f"headers.txt"
    katana_headers = ""

    with proxy_setting_lock:
        # proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
        counter1 = Counter(proxies)
        counter2 = Counter(used_proxies_across_processes)
        result_counter = counter1 - counter2
        result = list(result_counter.elements())
        proxy = result[0]

        used_proxies_across_processes.append(proxy)
    
    chrome_data_dir = ""
    def fill_input(splitted_urls):
        nonlocal katana_headers
        with req_lock:
            if args.request_file != None:

                headers = extract_headers(args.request_file)
                queries = extract_query_parameters_from_file(args.request_file)

                if headers:
                    with open(header_file_name, "w") as file:
                        for key, value in headers.items():
                            if key == "Cookie" and args.no_headless:
                                chrome_data_dir = f"-noi -cdd {cookie_handler(value, splitted_urls)}"
                            else:
                                file.write(f"{key}: {value}\n")

                    katana_headers = f"-H {header_file_name}"

                with open("sub_of_urls.txt", "w") as file:
                    for url in splitted_urls:
                        if queries:
                            url = add_query_params(url, queries)

                        file.write(f"{url}\n")

            # if queries:
            #     url = add_query_params(url, queries)
            
            # update_dict_with_matches(perm_req["queries"], queries)
            # update_dict_with_matches(perm_req["headers"], headers)
    
    fill_input(splitted_urls)
    if proxy != "self":
        proxy_for_katana = f"-proxy http://{proxy}"
    else:
        proxy_for_katana = ""
    
   
    
    # print("reached here")

    # if args.no_json_output:
    #     args.no_json_output = ""
    # else:
    #     args.no_json_output = f"-ob -o ./sub_{current_output_count}.json"

    previous_non_ok_urls_count = count_lines("sub_of_urls.txt")
    it_count = 0

    while True:
    #     subprocess.run([
    #     "katana", *shlex.split(args.no_headless), "-list", "sub_of_urls.txt", *shlex.split(proxy_for_katana), *shlex.split(chrome_data_dir), *shlex.split(args.no_scope), *shlex.split(args.field_scope),
    #     *shlex.split(args.crawl_out_scope), *shlex.split(args.crawl_duration), "-p", str(args.katana_parallel), "-rl", str(args.katana_rate_limit), "-c", str(args.katana_rate_limit),
    #     *shlex.split(katana_headers), "-rd", "0", "-d", str(args.sub_depth),
    #     "-sr", "-srd", f"./sub_{current_output_count}_traffic_{it_count}", "-timeout", "10", "-s" , "breadth-first"
    # ], preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        rate_config = get_url_rate_config(splitted_urls[0])
        rate_limit = str(min(args.katana_rate_limit, rate_config["rate"] * 10))

        execute_with_log_watch([
        "katana", *shlex.split(args.no_headless), "-list", "sub_of_urls.txt", *shlex.split(proxy_for_katana), *shlex.split(chrome_data_dir), *shlex.split(args.no_scope), *shlex.split(args.field_scope),
        *shlex.split(args.crawl_out_scope), *shlex.split(args.crawl_duration), "-p", str(args.katana_parallel), "-rl", rate_limit, "-c", rate_limit,
        *shlex.split(katana_headers), "-rd", "0", "-d", str(args.sub_depth),
        "-sr", "-srd", f"./sub_{current_output_count}_traffic_{it_count}", "-timeout", "10", "-s" , "breadth-first"
    ], f"./sub_{current_output_count}_traffic_{it_count}/index.txt", timeout_minutes=2)

        
        subprocess.run(f"cat ./sub_{current_output_count}_traffic_{it_count}/index.txt | awk '$3 != \"(200\" && $3 != \"(OK)\" && $4 != \"OK)\" {{ print $2 }}' | grep -xF -f sub_of_urls.txt | sort -u > sub_of_urls_new.txt", shell=True, executable="/bin/bash")
        subprocess.run(f"mv sub_of_urls_new.txt sub_of_urls.txt", shell=True)

        new_non_ok_urls_count = count_lines("sub_of_urls.txt")

        if args.parallel != len(urls):
            subprocess.run(f"tar -czf ./sub_{current_output_count}_traffic_{it_count}.tar.gz ./sub_{current_output_count}_traffic_{it_count}", shell=True)
            subprocess.run(f"rm -rf ./sub_{current_output_count}_traffic_{it_count}", shell=True)
        
        it_count += 1

        if it_count == 3:
            break
        
        if new_non_ok_urls_count <= previous_non_ok_urls_count and new_non_ok_urls_count != 0:
            previous_non_ok_urls_count = new_non_ok_urls_count
        else:
            break

    default_scopes = []
    crawled = []

    if args.crawl_scope:
        with open('/home/deus/documents/katana_in_scope.txt', 'r') as file:
            default_scopes = [line.strip() for line in file]
    
    fill_input(splitted_urls)
    if args.sub_depth > 1:
        for depth in range(1, args.sub_depth + 1):

            if depth != 1: 

                discovered_new_directory = False
                with open("/home/deus/documents/katana_in_scope.txt", "w") as katana_out_of_scope_file:
                    for cs in default_scopes:
                        katana_out_of_scope_file.write(f"{cs}\n")

                    subprocess.run(f"cat ./sub_{current_output_count}_traffic_*_{depth - 1}/index.txt | awk '{{ print $2 }}' | grep -F -f <(cat sub_of_urls.txt | unfurl domains | sed -e 's/$/\//g'  -e 's/^/\//g') | unfurl paths | awk -F/ -v N={depth} '{{{{segs = NF; if (segs >= N) {{out = \"\"; for (i = 2; i <= N; i++) {{out = out \"/\" $i}} if (segs > N) out = out \"/\"; print out}}}}}}' | grep -v -e // -e ^/$ | sort -u > crawl_scopes.txt", shell=True, executable="/bin/bash")
                    subprocess.run(f"cat ./sub_{current_output_count}_traffic_*_{depth - 1}/index.txt | awk '{{ print $2 }}' | grep -F -f <(cat sub_of_urls.txt | unfurl domains | sed -e 's/$/\//g'  -e 's/^/\//g') | grep -f crawl_scopes.txt | sort -u > sub_of_urls_new.txt", shell=True, executable="/bin/bash")
                    subprocess.run(f"mv sub_of_urls_new.txt sub_of_urls.txt", shell=True)

                    with open('crawl_scopes.txt', 'r') as file:
                        crawl_scopes = [line.strip() for line in file]
                        for cs in crawl_scopes:
                            if cs not in crawled:
                                katana_out_of_scope_file.write(f"{cs}\n")
                                crawled.append(cs)
                                discovered_new_directory = True

                for i in range(0, it_count):
                    subprocess.run(f"tar -czf ./sub_{current_output_count}_traffic_{i}_{depth - 1}.tar.gz ./sub_{current_output_count}_traffic_{i}_{depth - 1}", shell=True)
                    subprocess.run(f"rm -rf ./sub_{current_output_count}_traffic_{i}_{depth - 1}", shell=True)

                if discovered_new_directory:
                    args.crawl_scope = "-cs /home/deus/documents/katana_in_scope.txt"
                else:
                    break

            previous_non_ok_urls_count = count_lines("sub_of_urls.txt")
            it_count = 0
            while True:

            #     subprocess.run([
            #     "katana", *shlex.split(args.no_headless), "-list", "sub_of_urls.txt", *shlex.split(proxy_for_katana), *shlex.split(chrome_data_dir), *shlex.split(args.no_scope), *shlex.split(args.field_scope),
            #     *shlex.split(args.crawl_out_scope), "-p", str(args.katana_parallel), "-rl", str(args.katana_rate_limit), "-c", str(args.katana_rate_limit),
            #     *shlex.split(katana_headers), "-rd", "0", "-d", "1",
            #     "-sr", "-srd", f"./sub_{current_output_count}_traffic_{it_count}_{depth}", "-timeout", "10"
            # ], preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                rate_config = get_url_rate_config(splitted_urls[0])
                rate_limit = str(min(args.katana_rate_limit, rate_config["rate"] * 10))

                execute_with_log_watch([
                "katana", *shlex.split(args.no_headless), "-list", "sub_of_urls.txt", *shlex.split(proxy_for_katana), *shlex.split(chrome_data_dir), *shlex.split(args.no_scope), *shlex.split(args.field_scope),
                *shlex.split(args.crawl_out_scope), "-p", str(args.katana_parallel), "-rl", rate_limit, "-c", rate_limit,
                *shlex.split(katana_headers), "-rd", "0", "-d", "1",
                "-sr", "-srd", f"./sub_{current_output_count}_traffic_{it_count}_{depth}", "-timeout", "10"
            ], f"./sub_{current_output_count}_traffic_{it_count}_{depth}/index.txt", timeout_minutes=2)

                subprocess.run(f"cat ./sub_{current_output_count}_traffic_{it_count}_{depth}/index.txt | awk '$3 != \"(200\" && $3 != \"(OK)\" && $4 != \"OK)\" {{ print $2 }}' | grep -Fx -f sub_of_urls.txt | sort -u > sub_of_urls_new.txt", shell=True, executable="/bin/bash")
                subprocess.run(f"mv sub_of_urls_new.txt sub_of_urls.txt", shell=True)

                new_non_ok_urls_count = count_lines("sub_of_urls.txt")

                it_count += 1

                if it_count == 3:
                    break

                if new_non_ok_urls_count <= previous_non_ok_urls_count and new_non_ok_urls_count != 0:
                    previous_non_ok_urls_count = new_non_ok_urls_count
                else:
                    break
            
            if depth == 4:
                for i in range(0, it_count):
                    subprocess.run(f"tar -czf ./sub_{current_output_count}_traffic_{i}_{depth}.tar.gz ./sub_{current_output_count}_traffic_{i}_{depth}", shell=True)
                    subprocess.run(f"rm -rf ./sub_{current_output_count}_traffic_{i}_{depth}", shell=True)
        
        
    # old form extraction and json output included

#     subprocess.run([
#     "katana", *shlex.split(args.no_headless), "-list", "sub_of_urls.txt", *shlex.split(proxy_for_katana), *shlex.split(chrome_data_dir), *shlex.split(args.no_scope), *shlex.split(args.field_scope),
#     *shlex.split(args.crawl_out_scope), "-p", str(args.katana_parallel), "-rl", str(args.katana_rate_limit), "-c", str(args.katana_rate_limit),
#     *shlex.split(katana_headers), "-rd", "0", "-d", str(args.sub_depth), "-aff", "-j", "-fx", "-xhr", *shlex.split(f"-ob -o ./sub_{current_output_count}.json"),
#     "-sr", "-srd", f"./sub_{current_output_count}_traffic_{it_count}", "-timeout", "10"
# ], preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)



    # if args.no_json_output:
    #     subprocess.run(f"rm ./sub_{current_output_count}.json", shell=True)
    
    with open("/home/deus/documents/katana_in_scope.txt", "w") as katana_out_of_scope_file:
        for cs in default_scopes:
            katana_out_of_scope_file.write(f"{cs}\n")

    args.crawl_scope = default_crawl_scope
    
    with proxy_setting_lock:
        used_proxies_across_processes.remove(proxy)
    



previous_output_count = 0
for f_or_d in os.listdir('./'):
    if f"_traffic" in f_or_d:
        previous_output_count += 1

def rota_exit_handler(rota_proc):
    os.killpg(os.getpgid(rota_proc.pid), signal.SIGKILL)

    try:
        rota_proc.wait(timeout=5)
    except Exception:
        pass


if not args.only_sub:
    instance_count = 0
    # for splitted_urls in split_list(home_of_urls, args.parallel):
    for home_of_url in home_of_urls:

        if "http://" in home_of_url or "https://" in home_of_url:
            hostname = urlparse(home_of_url).hostname
        elif ":" in home_of_url:
            hostname = home_of_url.split(":")[0]
        else:
            hostname = home_of_url

        used_user_agents = set()
        proxies = []
        if args.no_proxy:
            proxies.append("self")
        else:
            port, rota_proc = get_proxy_port(hostname, args.katana_rate_limit, used_user_agents)
            proxies.append(f"127.0.0.1:{port}")

        instance_count += 1
        katana_for_main(home_of_url)
            
        if not args.no_proxy:
            rota_exit_handler(rota_proc)

    # pool = multiprocessing.Pool(len(proxies))
    # pool.map(katana_for_main, home_of_urls, chunksize=1)


if not args.only_home:
    if not args.parallel:
        args.parallel = len(urls)

    grouped_urls = group_urls_by_hostname(urls)

    instance_count = 0
    for hostname, urls in grouped_urls.items():


        used_user_agents = set()
        proxies = []
        if args.no_proxy:
            proxies.append("self")
        else:
            port, rota_proc = get_proxy_port(hostname, args.katana_rate_limit, used_user_agents)
            proxies.append(f"127.0.0.1:{port}")

        for splitted_urls in split_list(urls, args.parallel):
            instance_count += 1
            katana_for_sub(splitted_urls)

        if not args.no_proxy:
            rota_exit_handler(rota_proc)


# pool = multiprocessing.Pool(len(proxies))
# pool.map(katana_for_sub, urls, chunksize=1)

stop_event.set()
# rota_exit_handler()

for filename in glob.glob("headers_*.txt"):
    os.remove(filename)