import multiprocessing
try:
   multiprocessing.set_start_method('fork', force=True)
   print("forked")
except RuntimeError:
    print("unable to fork!")
    exit()
import re
import subprocess
import tldextract
import sys
from urllib.parse import urlparse, parse_qs
import pytz
import subprocess
import argparse
import json
import os
from collections import defaultdict
import string
import shlex
import time
import psutil
import glob
import signal
import urllib.parse
import threading
from collections import Counter
import humps
import asyncio
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket
from ipwhois import IPWhois
from ipwhois.exceptions import IPDefinedError
import random
import requests

ua = UserAgent()


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

# def response_has_cookies(url: str) -> bool:
    
#     try:
#         proxies = {
#             "http": "http://isp.decodo.com:10000",
#             "https": "https://isp.decodo.com:10000"
#         }
    
#         response = requests.get(f'http://{url}', proxies=proxies, timeout=30)
#         return bool(response.cookies)
#     except requests.RequestException as e:
#         print(f"Request failed: {e}")
#         return False


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

def append_payload_if_trailing_slash(input_string):
    if input_string.endswith('/'):
        return input_string + "payload"
    return input_string

def is_binary_content(path):
    """Check if the path contains non-printable or non-ASCII characters."""
    # Define printable characters (ASCII printable characters)
    printable_chars = set(string.printable)

    # Check for non-printable or non-ASCII characters
    return any(char not in printable_chars for char in path)

def the_path_i_like(path):
    """Check if the path meets specific criteria."""
    # Define sets of excluded patterns
    excluded_if_its_in_path = {".dex", ".ts", ".svg", ".jpg", ".png", ".js", ".css", ".jpeg", ".gif", ".mp4", ".flv", ".ogv", ".webm", ".webp", ".mov", ".mp3", ".m4a", ".m4p", ".scss", ".tif", ".tiff", ".ttf", ".otf", ".txt", ".woff", ".woff2", ".bmp", ".ico", ".eot", ".htc", ".rtf", ".swf"}
    excluded_paths = {"|", "application/asp", "protobuf-ts/message-type", "application/font-otf", "application/font-sfnt", "application/font-ttf", "application/font-woff", "application/font-woff2", "application/jsp", "application/octet-stream", "application/pdf", "application/php", "application/vnd.android.package-archive", "application/vnd.ms-fontobject", "application/vnd.wap.xhtml+xml", "application/x-asp", "application/x-font-opentype", "application/x-font-otf", "application/x-font-ttf", "application/x-font-woff", "application/x-font-woff2", "application/xhtml+xml", "application/x-httpd-php", "application/x-jsp", "application/xml", "application/x-ms-application", "application/x-msdownload", "application/x-php", "application/x-woff", "audio/aac", "audio/aiff text/css", "audio/aiff text/html", "audio/aiff unk", "audio/basic", "audio/mp3", "audio/mpeg", "audio/ogg", "audio/wav", "audio/webm", "audio/x-wav", "binary/octet-stream", "font/opentype", "font/otf", "font/ttf", "font/woff", "font/woff2", "font/x-woff", "font/x-woff2", "image/bmp", "image/gif", "image/jpeg", "image/jpg", "image/pjpeg", "image/png", "image/svg+xml", "image/tiff", "image/vnd", "image/vnd.microsoft.icon", "image/webp", "image/x-icon", "image/x-ms-bmp", "image/x-png", "text/asp", "text/css", "text/htm", "text/html", "text/jsp", "text/php", "text/plain", "text/x-asp", "text/x-jsp", "text/x-jsp ", "text/xml", "text/x-php", "unk", "video/3gpp", "video/mp2t", "video/mp4", "video/mpeg", "video/ogg", "video/quicktime", "video/webm", "video/x-flv", "video/x-msvideo", "video/x-ms-wmv", "warc/metadata", ""}

    # Check if the path meets all criteria
    if (
        './' not in path and
        path not in pytz.all_timezones and
        len(path) < 2000 and
        all(pattern.lower() != path.lower() for pattern in excluded_paths) and
        not is_binary_content(path) and
        not any(path.lower().endswith(ext.lower()) for ext in excluded_if_its_in_path) and
        not any(ext.lower() + "?" in path.lower() for ext in excluded_if_its_in_path) and
        "web.archive.org" not in path
    ):
        return True
    return False


# def read_json_objects_of_feroxbuster(file_path):
#     with open(file_path, 'r') as file:
#         for subdomain in file:
#             yield json.loads(subdomain)

def read_json_objects(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        # Regular expression to find JSON objects
        json_objects = re.findall(r'\{(?:[^{}]|(?R))*\}', content)
        for json_object in json_objects:
            yield json.loads(json_object)

def extract_base_domain(url):
    ext = tldextract.extract(url)
    return ext.domain

def extract_domain(url):
    extracted = tldextract.extract(url)
    domain = extracted.domain
    tld = extracted.suffix
    base_domain = f"{domain}.{tld}"
    return base_domain

def extract_path(url):
    parsed_url = urlparse(url)
    return parsed_url.path

def extract_path_with_queries(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    queries = parsed_url.query
    if queries:
        return f"{path}?{queries}"
    return path

def extract_query_parameters(url):
    # Parse the URL
    parsed_url = urlparse(url)
    query_string = parsed_url.query
    
    # Parse query string without decoding the values
    query_params = parse_qsl(query_string, keep_blank_values=True)
    
    # Re-encode each query parameter value to preserve the original encoding
    flat_query_params = {key: quote(value, safe='') for key, value in query_params}

    return flat_query_params

# def count_string_occurrences(directories, strings):
#     # Dictionary to hold counts of each string
#     string_counts = defaultdict(int)

#     # Walk through the directory and its subdirectories
#     for directory in directories:
#         for root, dirs, files in os.walk(directory):
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 try:
#                     with open(file_path, 'r', encoding='utf-8') as f:
#                         for path in f:
#                             path = path.strip()

#                             for string in strings:
#                                 if directory == "./":
#                                     if string + "/" in path or "/" + string in path:
#                                         string_counts[string] += 1
#                                 else:
#                                     if path == string:
#                                         string_counts[string] += 1
#                 except Exception as e:
#                     print(f"Error reading {file_path}: {e}")

#     return string_counts

def count_strings_in_file(args):
    file_path, strings, root_dir = args
    string_counts = defaultdict(int)
    # if not ('/apk/' in file_path and '.smali' not in file_path and '.js' not in file_path and '.htm' not in file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for path in f:
                path = path.strip()
                for string in strings:
                    if root_dir == "./":
                        if string + "/" in path or "/" + string in path:
                            string_counts[string] += 1
                    else:
                        if path == string:
                            string_counts[string] += 1
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return string_counts

def merge_dicts(dicts):
    merged = defaultdict(int)
    for d in dicts:
        for key, value in d.items():
            merged[key] += value
    return merged

def count_string_occurrences(directories, strings):
    # List to hold all file paths
    file_paths = []
    for directory in directories:
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_paths.append((file_path, strings, directory))

    # Use multiprocessing to process files in parallel
    with multiprocessing.Pool() as pool:
        results = pool.map(count_strings_in_file, file_paths)

    # Merge the results from all processes
    return merge_dicts(results)

def sort_strings_by_occurrence(strings, string_counts):
    return sorted(strings, key=lambda s: string_counts[s])

def extract_subdomain(url):
    extracted = tldextract.extract(url)
    subdomain = extracted.subdomain
    return subdomain

def process_part(part):
    paths = [f'/{part}']
    if part.isdigit():
        paths.append(f'/v{part}')
    return paths

def process_subdomain(subdomain):
    parts = re.split(r'[.-]', subdomain)

    paths = set()
    combined_path = ""
    for part in parts:
        for subpath in process_part(part):
            paths.add(subpath)
        if combined_path:
            combined_path += f'/{part}'
        else:
            combined_path = f'/{part}'
        paths.add(combined_path)
        if part.isdigit():
            paths.add(combined_path.replace(f'/{part}', f'/v{part}'))

    paths.add(f'/{subdomain}')

    return list(paths)

def permutations_on_number(path):
    # Split the subdomain while preserving separators
    parts_of_path = path.split('/')

    outputs = []

    def generate_permutations(num):
        permutations = []
        for delta in [-2, -1, 1, 2]:
            new_number = num + delta
            if new_number >= 0:  # Ensure no negative numbers
                permutations.append(new_number)
        return permutations

    # Process numeric parts_of_path
    for i, part in enumerate(parts_of_path):
        if part.isdigit():
            number = int(part)
            permutations = generate_permutations(number)
            for perm in permutations:
                # Replace the numeric part with the new permutation
                new_parts_of_path = parts_of_path[:i] + [str(perm)] + parts_of_path[i+1:]
                new_path = '/'.join(new_parts_of_path)
                outputs.append(new_path)
        else:
            for c_idx in range(0, len(part)):
                if part[c_idx].isdigit():
                    number = int(part[c_idx])
                    permutations = generate_permutations(number)
                    for perm in permutations:
                        # Replace the numeric part with the new permutation
                        new_parts_of_path = parts_of_path[:i] + [part.replace(part[c_idx],str(perm))] + parts_of_path[i+1:]
                        new_path = '/'.join(new_parts_of_path)
                        outputs.append(new_path)

    return outputs

def paths_permutation(path):
    global paths
    global paths_permutation_list
    # payloads_list = set()
    # for path_x in paths:
    # path_x_subpath = path_x.split('/')
    path_x = path
    path_x_subpath = re.split(r'[./-]', path_x)
    for path_y in paths:
        if path_y == path_x:
            continue
        path_y_subpath = re.split(r'[./-]', path_y)
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
                    else:
                        payload_subpath += "PAYLOADDDD"
                if idx < not_match_idx_for_path_x:
                    if path_x_subpath[idx] + '/' in path_x:
                        payload_subpath += path_x_subpath[idx] + '/'
                    elif path_x_subpath[idx] + '-' in path_x:
                        payload_subpath += path_x_subpath[idx] + '-'
                    elif path_x_subpath[idx] + '.' in path_x:
                        payload_subpath += path_x_subpath[idx] + '.'
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
                    else:
                        continually_shared_parts_of_subpath_after_non_matching_part += path_x_subpath[idx]
                else:
                    continually_shared_parts_of_subpath_after_non_matching_part = ""
            payload_subpath += continually_shared_parts_of_subpath_after_non_matching_part
            if payload_subpath not in paths_permutation_list:
                paths_permutation_list.append(payload_subpath)
    # return payloads_list

def split_file_into_n_parts(input_file,n_parts, url):
    file_names = []
    # Read all lines from the input file
    with open(input_file, 'r') as file:
        lines = file.readlines()

    # Calculate the number of lines each part should have
    total_lines = len(lines)
    lines_per_part = total_lines // n_parts
    extra_lines = total_lines % n_parts

    start = 0
    for i in range(n_parts):
        # Calculate the end index for this part
        end = start + lines_per_part + (1 if i < extra_lines else 0)
        output_file = f"paths_part_{i+1}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','').replace(':','PORT')}.txt"
        # Write the lines to the new file
        with open(output_file, 'w') as part_file:
            part_file.writelines(lines[start:end])
        file_names.append(output_file)
        # Update the start index for the next part
        start = end
    return file_names

def split_file(input_file, lines_per_file, url):
    with open(input_file, 'r') as infile:
        lines = infile.readlines()
        
    total_lines = len(lines)
    file_count = (total_lines + lines_per_file - 1) // lines_per_file  # Calculate the number of output files needed

    output_files = []

    for i in range(file_count):
        output_file = f"paths_part_{i+1}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"
        with open(output_file, 'w') as outfile:
            start = i * lines_per_file
            end = start + lines_per_file
            outfile.writelines(lines[start:end])
        output_files.append(output_file)
    
    return output_files

def split_list(lst, n):
    """
    Splits a list into a list of lists, with each sublist containing `n` elements.

    :param lst: The original list to be split.
    :param n: The number of elements per sublist.
    :return: A list of sublists.
    """
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def process_feroxbuster_output():
    for path in subprocess.run(f"cat paths_part_*.json | jq .path", shell=True, capture_output=True, text=True).stdout.split("\n"):
        if path[1:len(path) - 1] not in working_paths and '/' in path: # aka not null
            working_paths.append(path[1:len(path) - 1])
    # for i in range(25):
    #     if os.path.exists(f"paths_part_{i+1}.txt.json"):
    #         for entry in read_json_objects(f"paths_part_{i+1}.txt.json"):
    #             if 'path' in entry:
                    # working_paths.append(entry['path'])

def kill_process_and_children(pid):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):  # or parent.children() for non-recursive
            child.kill()
        parent.kill()
    except psutil.NoSuchProcess:
        pass


def run_ffuf(args_for_run_ffuf):
    # global url_for_ferox
    global methods
    # global extensions
    global filter_regex
    global filter_status
    global filter_lines
    user_agent = []
    # global headers
    # global queries
    global rate_limit
    global no_proxy
    # global used_proxies_across_processes
    # global proxies
    global args
    global lock
    global proxy_setting_lock
    global ua


    paths_part, url, proxies, used_proxies_across_processes, method = args_for_run_ffuf

    url = f"https://{url}"

    with proxy_setting_lock:
        counter1 = Counter(proxies)
        counter2 = Counter(used_proxies_across_processes)
        result_counter = counter1 - counter2
        result = list(result_counter.elements())
        proxy = result[0]
        
        used_proxies_across_processes.append(proxy)
    

    def matches_n_times(path, probed_paths, n):
        probed_paths = [re.sub(r'[^a-zA-Z0-9]', '', urllib.parse.unquote(probed_path).split('?')[0]) for probed_path in probed_paths]
        path = re.sub(r'[^a-zA-Z0-9]', '', urllib.parse.unquote(path).split('?')[0])
        count = sum(1 for probed_path in probed_paths if path.replace('/', '') == probed_path.replace('/', ''))
        return count >= n


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
        query_params = parse_qs(query_string)

        # Flatten the dictionary (parse_qs returns a list for each key)
        flat_query_params = {key: value[0] for key, value in query_params.items()}

        return flat_query_params

    def extract_headers(file_path):
        nonlocal user_agent
        user_agent = []
        headers = {}

        with open(file_path, 'r') as file:
            req_lines = file.readlines()
            for subdomain in req_lines[1:]:
                if ': ' in subdomain:
                    key, value = subdomain.split(': ', 1)
                    if key.lower() != 'host' and key.lower() != 'user-agent' and key.lower() != 'accept' and key.lower() != 'content-length':
                        headers[key] = value.strip()
                    if key.lower() == 'user-agent':
                        user_agent.append('-H') 
                        user_agent.append(f"User-Agent: {value.strip()}")
        return headers

    # paths_part_content_preserved = []
    # with open(f"./{paths_part}", "r") as paths_file:
    #     for path in paths_file:
    #         path = path.strip()
    #         paths_part_content_preserved.append(path)

    subprocess.run(f"cp {paths_part} preserved_{paths_part} ", shell=True)

    # for method in methods:
    # if method != "GET_DIRECTORY":
    output_file_name = f"./endpoint_{method}_{url.replace('http://', '').replace('https://', '').replace('/','')}_{paths_part}.json"
    # else:
    #     output_file_name = f"./directory_{url.replace('http://', '').replace('https://', '').replace('/','')}_{paths_part}.json"
    subprocess.run(f"cp preserved_{paths_part} {paths_part}", shell=True)
    
    # consecutively_unchanged_count = 0
    # last_written_to_path_count = 0
    # paths_part_content = []
    # timecount = 60
    # with open(f"./{paths_part}", "w") as paths_file:
    #     for path in paths_part_content_preserved:
    #         paths_file.write(path + "\n")
        # paths_part_content.append(path)
        # timecount += 2
    # while True:
    # is_single_line_comment = lambda file_path: open(file_path).readline().startswith('#') if len(open(file_path).readlines()) == 1 else False
    # if not any(char.isalnum() for char in open(f"./{paths_part}").read()) or is_single_line_comment(paths_part):
    #     break
    
    
    # if method != "GET_DIRECTORY":
    #     output_exists = os.path.exists(f"./endpoint_{method}_{url.replace('http://', '').replace('https://', '').replace('/','')}_{paths_part}.json")
    # else:
    # output_exists = os.path.exists(output_file_name)
    def five02_exists_in_output():
        grep_502 = subprocess.run(
            ['grep', '"status":502,', output_file_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        # grep_suffix = subprocess.run(
        #     ['grep', f'{suffix}"'],
        #     stdin=grep_502.stdout,
        #     stdout=subprocess.DEVNULL,
        #     stderr=subprocess.DEVNULL
        # )
        # grep_502.stdout.close()  # Allow grep_502 to receive a SIGPIPE if grep_suffix exits early
        # return grep_suffix.returncode == 0
        return grep_502.returncode == 0
    
    def timed_out_path():
        # escaped_suffix = re.escape(suffix).replace('\\', r'\\').replace('&', r'\&')
        # subprocess.run(f"~/scripts/filter <(jq -r '.url' {output_file_name} | sed -E 's|^[^:]+://[^/]+||' | sed 's/^\///g' | sed 's/\/$//g') <(cat {paths_part} | sed 's|$|{escaped_suffix}|g' | sed -E 's|^[^:]+://[^/]+||' | sed 's/^\///g' | sed 's/\/$//g') > timed_out_paths_{paths_part}", shell=True, executable='/bin/bash')
        
        subprocess.run(f"~/scripts/filter <(jq -r '.url' {output_file_name} | sed -E 's|^[^:]+://[^/]+||' | sed 's/^\///g' | sed 's/\/$//g') <(cat {paths_part} | sed -E 's|^[^:]+://[^/]+||' | sed 's/^\///g' | sed 's/\/$//g') > timed_out_paths_{paths_part}", shell=True, executable='/bin/bash')
        
        with open(f"timed_out_paths_{paths_part}", 'r') as f:
            return bool(any(f))
    
    def modify_wordlist_with_unprobed_paths(failure_count):
        # escaped_suffix = re.escape(suffix).replace('\\', r'\\').replace('&', r'\&')
        # if suffix.endswith("/"):
        #     dir_command = f"| sed 's|$|{escaped_suffix}|g'"
        # else:
        #     dir_command = ""
        
        subprocess.run(f"jq -r 'select(.status != 502) | .url' {output_file_name} | sed -E 's|^[^:]+://[^/]+||' | sed 's/^\///g' > tested_{paths_part}", shell=True)
        # if failure_count == 0:
        #     subprocess.run(f"cat {paths_part} | sed 's|$|{escaped_suffix}|g' | sed 's/^\///g' | sed 's/\/$//g' {dir_command} > rectified_{paths_part}", shell=True)
        # else:
        subprocess.run(f"cat {paths_part} | sed 's/^\///g' > rectified_{paths_part}", shell=True)
        subprocess.run(f"cat <(jq -r 'select(.status >= 300 and .status < 400) | .redirectlocation' {output_file_name} | grep -Fi {url} ) | sed -E 's|^[^:]+://[^/]+||' | sed 's/^\///g' | anew -q rectified_{paths_part}", shell=True, executable='/bin/bash')
        
        subprocess.run(f"/home/deus/scripts/filter tested_{paths_part} rectified_{paths_part} > untested_{paths_part}", shell=True)
        # subprocess.run(f"cat timed_out_paths_{paths_part} | anew -q untested_{paths_part} ", shell=True)
        subprocess.run(f"mv untested_{paths_part} {paths_part} ", shell=True)
        subprocess.run(f"rm tested_{paths_part} rectified_{paths_part}", shell=True)
        
        # unprobed_paths_count = subprocess.run(f"cat {paths_part} | wc -l", shell=True, capture_output=True, text=True).stdout.split("\n")[0].strip()
        # if int(unprobed_paths_count) > 0 and consecutively_unchanged_count < 2:
            
        #     if int(unprobed_paths_count) != last_written_to_path_count:
        #         last_written_to_path_count = len(unprobed_paths_count)
        #         consecutively_unchanged_count = 0
        #     else:
        #         consecutively_unchanged_count += 1
        # else:
        #     break
    
    if not user_agent:
        header_string = ["-H",f"User-Agent: {ua.chrome}"]
        # header_string = ["-H","User-Agent: Mozilla/5.0 Windows NT 10.0 Win64 AppleWebKit/537.36 Chrome/69.0.3497.100"]
    else:
        header_string = user_agent
    query_string = []
    with lock:
        if args.request_file != None:
            if args.token_script != None and args.paths_number != None and args.token_expiration == None:
                subprocess.run(f"python3 {args.token_script}", shell=True)
            headers = extract_headers(args.request_file)
            queries = extract_query_parameters(args.request_file)
            for key, value in headers.items():
                header_string.append("-H")
                header_string.append(f'{key}: {value}')
                # header_string += f'-H \"{key}: {value}\" '
            for key, value in queries.items():
                query_string.append("-Q")
                query_string.append(f'{key}={value}')
                # query_string += f'-Q {key}={value} '
    
    # if args.paths_number != None and args.delay != None and args.token_script != None and args.token_expiration == None:
    #     time.sleep(args.delay)
    
    # commented coz of ffuf replacement
    # cmd = ["feroxbuster"]
    # cmd.append("-u")
    # cmd.append(url)
    # cmd.extend("-k -n --dont-extract-links --no-state --silent --dont-filter --scan-limit 1".split(" "))
    # cmd.append("--rate-limit")
    # cmd.append(rate_limit)
    # cmd.extend("-T 10".split(" "))
    # if proxy != "self":
    #     cmd.append("--proxy")
    #     cmd.append(f"socks5h://{proxy}")
    # cmd.extend(user_agent)
    # cmd.append("-w")
    # cmd.append(f"./{paths_part}")
    # cmd.append("-m")
    # if method == "GET_DIRECTORY":
    #     cmd.append("GET")
    #     cmd.append("-f")
    # else:
    #     cmd.append(method)
    
    # cmd.append("-o")
    # cmd.append(output_file_name)
    # cmd.extend(filter_regex)
    # cmd.extend(filter_status)
    # cmd.extend(filter_lines)
    # cmd.extend(header_string)
    # cmd.extend(query_string)
    # cmd.extend(extensions)
    # cmd.append("--json")
    # ffuf -u 'https://www.pandora.com:443/services/ajax/?method=FUZZ' -w ./../extracted_paths_and_params/extracted_param_wordlist.txt -mc all -o ./services_ajax_method_fuzz.json -rate 200 -H "X-Bug-Bounty: HackerOne-seudxs" -noninteractive -x socks5://isp.smartproxy.com:10001
    
    # log_file = open("logfile.log", "a")
    # log_file.write("reached here 1\n")
    # log_file.close()
    
    rate_config = get_url_rate_config(url)
    cmd = ["ffuf"]
    cmd.append("-u")
    cmd.append(url + "/FUZZ")
    cmd.extend("-timeout 10 -mc all -s -json -noninteractive".split(" "))
    cmd.append("-rate")
    if rate_config:
        cmd.append(str(min(rate_limit, rate_config["rate"] * 10)))
    else:
        cmd.append(rate_limit)
    cmd.append("-t")
    if rate_config:
        cmd.append(str(min(rate_limit, rate_config["rate"] * 10)))
    else:
        cmd.append(rate_limit)
    if proxy != "self":
        cmd.append("-x")
        cmd.append(f"http://{proxy}")
    cmd.append("-w")
    cmd.append(f"./{paths_part}")
    cmd.append("-X")
    # if method != "GET_DIRECTORY":
    cmd.append(method)
    # else:
    #     cmd.append("GET")
    
    if rate_config:
        cmd.append("-p")
        cmd.append(str(rate_config["delay"]))
    elif args.ffuf_delay:
        cmd.append("-p")
        cmd.append(f"{args.ffuf_delay}")
    
    cmd.extend(header_string)
    cmd = [x for x in cmd if x]
    cmd = list(map(str, cmd))
    
    def subprocess_call_ffuf():
        if args.delay != None:
            time.sleep(args.delay)
        # cmd[2] = ffuf_url + suffix
        with open(output_file_name, "a") as output_file:
            # subprocess.run(cmd, preexec_fn=os.setsid, stdout=output_file)
            failure_count = 0
            previous_line_count = 0
            while True:
                # if failure_count != 0:
                #     cmd[2] = ffuf_url
                with open(f"./{paths_part}", 'r') as f:
                    line_count = sum(1 for _ in f)
                    if previous_line_count != 0 and line_count > (previous_line_count - 50):
                        break
                    
                    previous_line_count = line_count
                result = subprocess.run(cmd, preexec_fn=os.setsid, stdout=output_file)
                if (result.returncode == 0 and not five02_exists_in_output() and not timed_out_path()) or failure_count == 2:
                    break  # Command succeeded, exit the loop
                print(f"ffuf failed with return code {result.returncode} while running {url}, retrying...")
                modify_wordlist_with_unprobed_paths(failure_count)
                failure_count += 1
    
    # if url[-1] == "/":
    #     ffuf_url = url + "FUZZ"
    # else:
    #     ffuf_url = url + "/FUZZ"
    # suffix = ""
    # if method == "GET_DIRECTORY":
    #     suffix = "/"
        # ffuf_url += suffix
    
    subprocess_call_ffuf()
    # subprocess.run(f"cp preserved_{paths_part} {paths_part}", shell=True)
    # if method != "GET_DIRECTORY":
    #     for extension in extensions:
    #         suffix = extension
    #         # if url[-1] == "/":
    #         #     ffuf_url = url + "FUZZ" + suffix
    #         # else:
    #         #     ffuf_url = url + "/FUZZ" + suffix
    #         subprocess_call_ffuf(ffuf_url, suffix)
    #         subprocess.run(f"cp preserved_{paths_part} {paths_part}", shell=True)
            
    #     if args.subpath_id:
    #         suffix = f"/{args.subpath_id}"
    #         # if url[-1] == "/":
    #         #     ffuf_url = url + "FUZZ" 
    #         # else:
    #         #     ffuf_url = url + "/FUZZ"
    #         # ffuf_url += suffix
    #         # ffuf_url += "/payloaddd"
    #         subprocess_call_ffuf(ffuf_url, suffix)
    #         subprocess.run(f"cp preserved_{paths_part} {paths_part}", shell=True)
    with proxy_setting_lock:
        used_proxies_across_processes.remove(proxy)
    
    subprocess.run(f'/bin/bash -c \'rm {paths_part} \' ', shell=True)

stop_event = threading.Event()
# def token_loop():
#     if stop_event.is_set():
#         return
#     with lock:
#         if args.delay != None:
#             time.sleep(args.delay)
#         subprocess.run(f"python3 {args.token_script}", shell=True)
    
#     threading.Timer(args.token_expiration, token_loop).start()
def token_loop():
    while not stop_event.is_set():
        with lock:
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

def get_rest_of_url(url):
    parsed_url = urlparse(url)
    rest_of_url = parsed_url.path or "/"
    if parsed_url.query:
        rest_of_url += f"?{parsed_url.query}"
    if parsed_url.fragment:
        rest_of_url += f"#{parsed_url.fragment}"
    return rest_of_url

parser = argparse.ArgumentParser(description="Run feroxbuster with specified URL, request file, and methods.")
parser.add_argument("-u", "--url", required=False, help="The target URL. or file of target URLS")
parser.add_argument("-r", "--request-file", required=False, help="Path to the request file containing headers.")
parser.add_argument("-rc", "--rate-config", required=False, help="Path to the rate config.")
parser.add_argument("-m", "--methods", required=False, help="HTTP methods to use.")
parser.add_argument("-s", "--suffixes", required=False, help="suffix(es) to apply, comma separated")
parser.add_argument("-X", "--filter-regex", required=False, help="Filter out messages via regular expression matching on the response's body (ex: -X '^ignore me$')")
parser.add_argument("-C", "--filter-status", required=False, help="Filter out status codes (deny list) (ex: -C 200,401)")
parser.add_argument("-N", "--filter-lines", required=False, help="Filter out by lines (deny list) (ex: -N 20,4)")
parser.add_argument("-a", "--avoid-path", required=False, help="Filter this path or a path that has the input path (deny list) (ex: -a /logout,/deleteuser )")
parser.add_argument("-w", "--wordlist", required=False, help="wordlist to use instead of extracting them from files in the current directory and its subdirectories")
parser.add_argument('-p', '--permutate-wordlist', required=False, help='generates permutations on the given wordlist or wordlists separated by space and brute force them')
parser.add_argument('-rl', '--rate-limit', type=int, help='Limit number of requests per second (per directory) (default: 1, i.e. 1 r/s)')
parser.add_argument('-np', '--no-proxy', action='store_true', help='don\'t use proxies and instead use the server ip')
# parser.add_argument('-nd', '--no-directory', action='store_true', help='don\'t brute force for directories')
parser.add_argument('-pn', '--paths-number', type=int, required=False, help='number of paths supplied per starting of ferox, useful for updating req.txt with new authorization keys')
parser.add_argument('-ps', '--pattern-split', type=int, default=100, required=False, help='patterns to brute force per ffuf session')
parser.add_argument('-ts', '--token-script', required=False, help='a python script to execute to generate new authorization keys')
parser.add_argument('-d', '--delay', type=int, required=False, help='delay in seconds between --paths-number requests')
parser.add_argument('-fd', '--ffuf-delay', default="0", required=False, help='delay in seconds between --paths-number requests')
parser.add_argument('-nh', '--nhosts', type=int, default=1, required=False, help='number of hosts to brute-force at a time')
# parser.add_argument('-umw', '--use-more-wordlist', action='store_true', help='adds more wordlist')
parser.add_argument('-te', '--token-expiration', type=int, required=False, help='executes token script everytime token expiration time in minutes is reached')
parser.add_argument('-ucw', '--use-common-wordlists', action='store_true', help='use common wordlists like common.txt')
parser.add_argument('-urdw', '--use-raft-directory-wordlist', action='store_true', help='use raft directory wordlist')
parser.add_argument('-sbp', '--slash-before-payload', action='store_true', help='only apply slash before payloadddd')
parser.add_argument('-urww', '--use-raft-word-wordlist', action='store_true', help='use raft word wordlist')
parser.add_argument('-umw', '--use-meta-wordlist', action='store_true', help='use meta wordlist')
parser.add_argument('-ubmw', '--use-big-meta-wordlist', action='store_true', help='use big meta wordlist')
parser.add_argument('-mu', '--mimic-user', action='store_true', help='mimic users on lan when setting up proxy')
parser.add_argument('-sap', '--subdomain-as-pattern', action='store_true', help='use subdomain of the domain as one of its patterns')
parser.add_argument('-uapw', '--use-assetnotes-apiroutes-wordlist', action='store_true', help='use big meta wordlist')
parser.add_argument('-ucapw', '--use-customized-assetnotes-apiroutes-wordlist', action='store_true', help='use big meta wordlist')
parser.add_argument('-fp', '--filter-patterns', action='store_true', help='use all the patterns for a host, skipping host and pattern co-existing check')
parser.add_argument("-wew", "--wordlist-ends-with", required=False, help="Filter out lines that don't end with the supplied string")
# parser.add_argument('-ufw', '--use-file-wordlist', action='store_true', help='use common file wordlists like quickhits')
parser.add_argument('-ew', '--extract-wordlist', help='extract paths from files in the given directory and its subdirectory')
# parser.add_argument('-si', '--subpath-id', help='subpath id to be used for brute forcing like /users/<supplied subpath id>')
parser.add_argument('-ee', '--extract-exit', action='store_true', help='extract paths and exit')
parser.add_argument('-nc','--naming-convention', type=comma_separated_naming_conventions, required=False, help="Choose one or more naming conventions from: snake_case, camelCase, PascalCase, kebab-case (comma-separated)")
parser.add_argument('-cc','--character-case', choices=["lower", "upper"], required=False, help="lowercase or uppercase")
args = parser.parse_args()

if (args.paths_number == None and args.token_expiration == None) and args.token_script != None:
    print("paths number or token expiration argument not supplied")
    exit()

# if args.paths_number == None and args.delay != None:
#     print("paths number argument not supplied")
#     exit()

if args.paths_number != None and ((args.token_script == None and args.token_expiration == None) and args.delay == None):
    print("token script or delay argument not supplied")
    exit()

if args.token_expiration != None and args.token_script == None:
    print("token script argument not supplied")
    exit()

if args.request_file == None and args.token_script != None:
    print("request file argument not supplied")
    exit()

# if args.naming_convention == None and args.permutate_wordlist != None:
#     print("you gotta supply naming convention when using permutate wordlist")
#     exit()


urls = dict()
url_for_ferox = ""
methods = []
# extensions = ""
# filter_regex = ""
# filter_status = ""
# filter_lines = ""
user_agent = ""
headers = dict()
queries = dict()
rate_limit = "1"
no_proxy = args.no_proxy

# proxies = []
# if args.no_proxy:
#     proxies.append("self")
# else:
#     with open('/home/deus/documents/proxies.txt') as proxy_file:
#         for proxy in proxy_file:
#             proxy = proxy.strip()
#             if proxy != "":
#                 proxy = proxy.split(':')
#                 proxies.append(f"isp.smartproxy.com:{proxy[1]}")

manager = multiprocessing.Manager()
subpaths_count = manager.dict()
lock = multiprocessing.Lock()
proxy_setting_lock = multiprocessing.Lock()
# counter = multiprocessing.Value('i',1)
pattern = r"^(\/[a-zA-Z0-9-_~.!$&'()*+,;=:@]+|[a-zA-Z0-9-_~.!$&'()*+,;=:@]+\/|\/[a-zA-Z0-9-_~.!$&'()*+,;=:@]+\/)$"

if args.url:
    if args.url.startswith(('http://', 'https://')):
        # urls.append(args.url)
        parsed_url = urlparse(args.url)
        url_hostname = parsed_url.hostname
        url_port = ""
        try:
            if parsed_url.port:
                url_port = ":" + str(parsed_url.port)
        except:
            print(f"jumping over: {url}")
            # continue

        url_key = f"{url_hostname}{url_port}"
        # else:
        #     if url.startswith("https://"):
        #         url_port = "443"
        #     else:
        #         url_port = "80"

        if url_key not in urls.keys():
            urls[url_key] = list()

        rest_of_url = get_rest_of_url(args.url) 
        if rest_of_url != '/':
            urls[url_key].append(rest_of_url)
    else:
        with open(args.url) as urls_file:
            for url in urls_file:
                url = url.strip()
                parsed_url = urlparse(url)

                # urls.append(url)
                if url.startswith(('http://', 'https://')):
                    url_hostname = parsed_url.hostname
                    url_port = ""

                    try:
                        if parsed_url.port:
                            url_port = ":" + str(parsed_url.port)
                    except:
                        print(f"jumping over: {url}")
                        continue

                    url_key = f"{url_hostname}{url_port}"

                    if url_key not in urls.keys():
                        urls[url_key] = list()

                    rest_of_url = get_rest_of_url(url) 
                    if rest_of_url != '/':
                        urls[url_key].append(rest_of_url)
                else:
                    urls[url] = list()

if args.methods:
    methods = args.methods.split(",")

if args.avoid_path != None:
    args.avoid_path = args.avoid_path.lower().split(",")
if args.rate_limit != None:
    rate_limit = args.rate_limit

if args.rate_limit != None and args.rate_limit < 1:
    print("lmao enter rate limit properly")
    exit()

if args.token_expiration != None:
    args.token_expiration = args.token_expiration * 60
    # token_loop()

    threading.Thread(target=token_loop, daemon=True).start()

suffixes = []
if args.suffixes != None:
    if os.path.isfile(args.suffixes):
        with open(args.suffixes, 'r') as f:
            for suffix in f:
                suffix = suffix.strip()
    
                suffixes.append(suffix)
    else:
        for suffix in args.suffixes.split(","):

            suffixes.append(suffix)

args.suffixes = suffixes

delete_patterns = ["pattern_*", "endpoint*paths_part_1", "path*.txt"]

for pattern in delete_patterns:
    for file_path in glob.glob(pattern):
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def list_subdirectories_recursive(directory):
    """
    Recursively list all subdirectories in the given directory.

    :param directory: The path of the directory to search.
    :return: A list of subdirectory paths.
    """
    subdirectories = []
    for root, dirs, files in os.walk(directory):
        for subdir in dirs:
            subdirectories.append(os.path.join(root, subdir))
    return subdirectories

def extract_paths(dir):
    global paths
    global subdirectories
    global subpaths_count
    global pattern

    subprocess.run(["/home/deus/scripts/encoded_part_of_name_remover.sh"], cwd=dir)
    # subprocess.run(f"python3 ~/downloads/LinkFinder/linkfinder.py -i '{shlex.quote(dir)}/*' -o cli > linkfinder_output_{subdirectories.index(dir)}.txt", shell=True)
    # subprocess.run(f"find {shlex.quote(dir)} -maxdepth 1 -type f -name '*' | jsluice urls | jq -r .url | anew linkfinder_output_{subdirectories.index(dir)}.txt", shell=True)
    
    files = os.listdir(dir)
    for file in files:
        if not os.path.isfile(f"{dir}/{file}"):
            continue
        
        with open(f"linkfinder_output_{subdirectories.index(dir)}.txt", "a") as outfile:
            subprocess.run(["python3", "/home/deus/downloads/LinkFinder/linkfinder.py", "-i", f"{dir}/{file}", "-o", "cli"],stdout=outfile,stderr=subprocess.PIPE,text=True)
    
            # subprocess.run(["xnLinkFinder","-i", f"{dir}/{file}", "-o", "cli"],
            #     stdout=outfile,
            #     stderr=subprocess.PIPE,
            #     text=True
            # )
            # subprocess.run(
            #     ["jsluice", "urls"],
            #     stdout=outfile,
            #     stderr=subprocess.PIPE,
            #     text=True
            # )

    # Find files and process them with jsluice, jq, and anew
    # find = subprocess.run(
    #     ["find", dir, "-maxdepth", "1", "-type", "f", "-name", "*"],
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     text=True
    # )

    # jsluice = subprocess.run(
    #     ["jsluice", "urls"],
    #     input=find.stdout,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     text=True
    # )

    # jq = subprocess.run(
    #     ["jq", "-r", ".url"],
    #     input=jsluice.stdout,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     text=True
    # )

    # with open(f"linkfinder_output_{subdirectories.index(dir)}.txt", "a") as outfile:
    #     subprocess.run(
    #         ["anew"],
    #         input=jq.stdout,
    #         stdout=outfile,
    #         stderr=subprocess.PIPE,
    #         text=True
    #     )
    
    # with open(f"linkfinder_output_{subdirectories.index(dir)}.txt", "r") as paths_file:
    #     for path in paths_file:
    #         path = path.replace("\n","")
    #         path = path.strip()
    #         path = path.replace("\\","")
    #         if the_path_i_like(path):
    #             if path.startswith(('http://', 'https://')):
    #                 try:
    #                     path = extract_path(path)
    #                     if path not in paths and path != "/":
    #                         paths.append(path)
    #                 except:
    #                     pass
    #             else:
    #                 if path not in paths:
    #                     paths.append(path)
    #                     if path.endswith('/'):
    #                         path_with_payload = append_payload_if_trailing_slash(path)
    #                         paths.append(path_with_payload)

def lowercase_or_uppercase(c_path):

    if args.character_case == "upper":
        c_path = c_path.upper()
    elif args.character_case == "lower":
        c_path = c_path.lower()

    return c_path


def process_permutated_path(permutated_path, extracted_paths, tried_paths):
    # global tried_paths
    global paths
    global args

    result = []
    potentially_directory = permutated_path.split('/PAYLOADDDD')[0]
    if potentially_directory:
        result.append(potentially_directory)
    
    unique_paths = list(set(list(paths) + extracted_paths))
    
    for path in unique_paths:
        if not path:
            continue
        
        if path[0] == "/":
            path_to_be_written = permutated_path.replace("/PAYLOADDDD", path)
        else:
            path_to_be_written = permutated_path.replace("PAYLOADDDD", path)
        
        if not any(path_to_be_written == tried_path for tried_path in tried_paths) and ( args.avoid_path == None or not any(avoid_path in path_to_be_written.lower() for avoid_path in args.avoid_path)):
            result.append(path_to_be_written)
        
        if path_to_be_written.endswith('/'):
            path_with_payload = append_payload_if_trailing_slash(path_to_be_written)
            if not any(path_with_payload == tried_path for tried_path in tried_paths) and ( args.avoid_path == None or not any(avoid_path in path_with_payload.lower() for avoid_path in args.avoid_path) ):
                result.append(path_with_payload)
    
    return result


def process_generic_path(path, tried_paths):
    global args

    result = []
    
    if not path:
        return result
    
    if not any(path == tried_path for tried_path in tried_paths) and ( args.avoid_path == None or not any(avoid_path in path.lower() for avoid_path in args.avoid_path) ):
        result.append(path)
    
    if path.endswith('/'):
        path_with_payload = append_payload_if_trailing_slash(path)
        if not any(path_with_payload == tried_path for tried_path in tried_paths) and ( args.avoid_path == None or not any(avoid_path in path_with_payload.lower() for avoid_path in args.avoid_path) ):
            result.append(path_with_payload)
    
    return result


linkfinder_outputs = manager.list()
paths = manager.list()
paths_permutation_list = manager.list()
subdirectories = []
working_paths = []
tried_paths = []
subpaths = []
# proc_num = len(proxies)



# os.remove(f"xnlinkfinder_output.txt")
# output_command = subprocess.run(f"cat xnlinkfinder_output.txt linkfinder_output_*.txt > extracted_wordlist", shell=True)
# output_command = subprocess.run(f"rm xnlinkfinder_output.txt linkfinder_output_*.txt", shell=True)

# for url in urls:
#     if os.path.exists(f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"):
#         with open(f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "r") as paths_file:
#             for path in paths_file:
#                 path = path.replace("\n","")
#                 tried_paths.append(path)

# if os.path.exists(f"working_paths_for_{args.url.replace('http://', '').replace('https://', '').replace('/','')}.txt"):
#     with open(f"working_paths_for_{args.url.replace('http://', '').replace('https://', '').replace('/','')}.txt", "r") as paths_file:
#         for path in paths_file:
#             path = path.replace("\n","")
#             working_paths.append(path)

# for linkfinder_output in linkfinder_outputs:
#     for path in linkfinder_output.split("\n"):
#         path = path.replace("\n","")
#         path = path.strip()
#         path = path.replace("\\","")
#         if the_path_i_like(path):
#             if path.startswith(('http://', 'https://')):
#                 try:
#                     if extract_base_domain(args.url) == extract_base_domain(path):
#                         path = extract_path(path)
#                         if path not in paths and path != "/":
#                             paths.append(path)
#                 except:
#                     pass
#             else:
#                 if path not in paths:
#                     paths.append(path)

# for path in xnlinkfinder_output.split("\n"):
#     path = path.replace("\n","")
#     path = path.strip()
#     path = path.replace("\\","")
#     if the_path_i_like(path):
#         if path.startswith(('http://', 'https://')):
#             try:
#                 # if extract_base_domain(args.url) == extract_base_domain(path):
#                 path = extract_path(path)
#                 if path not in paths and path != "/":
#                     paths.append(path)
#             except:
#                 pass
#         else:
#             if path not in paths:
#                 paths.append(path)

# paths = list(set(paths))


def filter_path(path):
    paths = set()
    path = path.strip()
    
    path = path.replace("\n","")
    path = path.strip()
    path = path.replace("\\","")
    if the_path_i_like(path):
        if path.startswith(('http://', 'https://')):
            try:
                path = extract_path(path)
                if path not in paths and path != "/":
                    paths.append(path)
            except:
                pass
        else:
            if path not in paths:
                paths.add(path)
                if path.endswith('/'):
                    path_with_payload = append_payload_if_trailing_slash(path)
                    paths.add(path_with_payload)
    
    return paths


if args.extract_wordlist:
    for dire in list_subdirectories_recursive(args.extract_wordlist):
        subdirectories.append(dire)
    pool = multiprocessing.Pool(4)
    pool.map(extract_paths, subdirectories, chunksize=1)

    subprocess.run(
        ["/home/deus/scripts/path_extractor", args.extract_wordlist],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


    with open('extracted_path_wordlist.txt', 'a') as outfile:

        for filename in glob.glob('linkfinder_output_*.txt'):
            with open(filename, 'r') as infile:
                outfile.write(infile.read())
            os.remove(filename)

    if args.extract_exit:
        exit()

    # subprocess.run(
    #     ["sort", "-u", "-o", "extracted_path_wordlist.txt"],
    #     stdin=open("extracted_path_wordlist.txt", "r")
    #                 )
    

        # outfile.write("\n".join(paths))
    
    paths = set(paths)
    
    with open("extracted_path_wordlist.txt", "r") as paths_file, multiprocessing.Pool() as pool:
        results = pool.imap_unordered(filter_path, paths_file, chunksize=100)
        
        for result in results:
            if result:
                paths.update(result)  # Avoid None values and keep only valid paths
    
    paths = list(paths)
    
    # with open(f"extracted_path_wordlist.txt", "r") as paths_file:
    #     for path in paths_file:
    #         path = path.replace("\n","")
    #         path = path.strip()
    #         path = path.replace("\\","")
    #         if the_path_i_like(path):
    #             if path.startswith(('http://', 'https://')):
    #                 try:
    #                     path = extract_path(path)
    #                     if path not in paths and path != "/":
    #                         paths.append(path)
    #                 except:
    #                     pass
    #             else:
    #                 if path not in paths:
    #                     paths.append(path)
    #                     if path.endswith('/'):
    #                         path_with_payload = append_payload_if_trailing_slash(path)
    #                         paths.append(path_with_payload)
    
    # subprocess.run(f"xnLinkFinder -i ./ -o cli > xnlinkfinder_output.txt", shell=True)
    # with open(f"xnlinkfinder_output.txt", "r") as paths_file:
    #         for path in paths_file:
    #             path = path.replace("\n","")
    #             path = path.strip()
    #             path = path.replace("\\","")
    #             if the_path_i_like(path):
    #                 if path.startswith(('http://', 'https://')):
    #                     try:
    #                         # if extract_base_domain(args.url) == extract_base_domain(path):
    #                         path = extract_path(path)
    #                         if path not in paths and path != "/":
    #                             paths.append(path)
    #                             if re.match(pattern, path) and path != "/":
    #                                 path_without_slash = path.replace('/','')
    #                                 if path_without_slash not in subpaths_count.keys():
    #                                     subpaths_count[path_without_slash] = 1
    #                                 subpaths_count[path_without_slash] += 1
    #                     except:
    #                         pass
    #                 else:
    #                     if path not in paths:
    #                         paths.append(path)
    #                         if re.match(pattern, path):
    #                             path_without_slash = path.replace('/','')
    #                             if path_without_slash not in subpaths_count.keys():
    #                                 subpaths_count[path_without_slash] = 1
    #                             subpaths_count[path_without_slash] += 1
    # with open('extracted_path_wordlist.txt', 'w') as outfile:
    #     outfile.write("\n".join(paths))

    # for filename in glob.glob('linkfinder_output_*.txt'):
        # with open(filename, 'r') as infile:
        #     outfile.write(infile.read())
        # os.remove(filename)


def process_path(path):
    path = path.strip()
    
    if path.startswith(('http://', 'https://')):
        try:
            extracted_path = extract_path_with_queries(path)
            if extracted_path != "/":
                return extracted_path
        except:
            return None
    else:
        return path

if args.wordlist:
    paths = set(paths)
    
    with open(args.wordlist, "r") as paths_file, multiprocessing.Pool() as pool:
        results = pool.imap_unordered(process_path, paths_file, chunksize=100)
        
        for result in results:
            if result:
                paths.add(result)  # Avoid None values and keep only valid paths
    
    paths = list(paths)

if args.use_raft_directory_wordlist:

    with open(f"/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)

if args.use_raft_word_wordlist:

    with open(f"/usr/share/seclists/Discovery/Web-Content/raft-large-words.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)
    

if args.use_common_wordlists:
    
    with open(f"/usr/share/seclists/Discovery/Web-Content/dirsearch.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)
        
    with open(f"/usr/share/seclists/Discovery/Web-Content/common.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)
    
    with open(f"/home/deus/documents/meta_wordlist.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)
    
    with open(f"/usr/share/seclists/Discovery/Web-Content/quickhits.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)
    
    with open(f"/usr/share/seclists/Discovery/Web-Content/dsstorewordlist.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)
    
    with open(f"/usr/share/wfuzz/wordlist/general/admin-panels.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)

if args.use_meta_wordlist:
    with open(f"/home/deus/documents/meta_wordlist.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)

if args.use_big_meta_wordlist:
    with open(f"/home/deus/documents/big_meta_wordlist.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)

if args.use_assetnotes_apiroutes_wordlist:
    with open(f"/home/deus/documents/httparchive_apiroutes_2024_05_28.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)

if args.use_customized_assetnotes_apiroutes_wordlist:
    with open(f"/home/deus/documents/customized_assetnotes_apiroutes.txt", "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            paths.append(path)

if args.naming_convention:
    new_paths = set()
    for path in paths:
        subpaths = path.split("/")

        for naming_convention in args.naming_convention:
            new_path = path
            if naming_convention == "snake_case":
                for subpath in subpaths:
                    new_path = new_path.replace(subpath, humps.decamelize(humps.camelize(subpath)))
                
            elif naming_convention == "camelCase":
                for subpath in subpaths:
                    new_path = new_path.replace(subpath, humps.camelize(subpath))
                
            elif naming_convention == "PascalCase":
                for subpath in subpaths:
                    new_path = new_path.replace(subpath, humps.pascalize(subpath))
                
            elif naming_convention == "kebab-case":
                for subpath in subpaths:
                    new_path = new_path.replace(subpath, humps.kebabize(subpath))

            new_path = lowercase_or_uppercase(new_path)

            new_paths.add(new_path)
    
    paths = list(new_paths)

paths = list(set(paths))


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

        print("reached here 33")
        ports = list(range(8000, 15000))
        random.shuffle(ports)

        for port in ports:
            if is_port_available(port):
                available_port = port
                break

        print("reached here 11")
        # mimick_users = response_has_cookies(hostname)
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



            print("reached here 11")
            for user_agent in user_agents:
                if user_agent not in used_user_agents:
                    used_user_agents.add(user_agent)

                    user_agent_arg = f"-g {user_agent}"

        else:
            domain_arg = ""
            user_count_arg = ""
            user_agent_arg = ""

        print("reached here 1")
        print(domain_arg)
        print(user_count_arg)
        print(user_agent_arg)


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


        return available_port, rota_proc
    except Exception as e:
        print("Error:", e)
        

def rota_exit_handler(rota_proc):
    os.killpg(os.getpgid(rota_proc.pid), signal.SIGKILL)

    try:
        rota_proc.wait(timeout=5)
    except Exception:
        pass

def permutation_based(url, extracted_paths):
    try:

        if "http://" in url or "https://" in url:
            hostname = urlparse(url).hostname
        elif ":" in url:
            hostname = url.split(":")[0]
        else:
            hostname = url


        # proxies = []
        # if args.no_proxy:
        #     proxies.append("self")
        # else:
        #     port, rota_proc = get_proxy_port(hostname, rate_limit, used_user_agents)
        #     proxies.append(f"127.0.0.1:{port}")

        # proc_num = len(proxies)


        tried_paths = []
        pattern_paths = []
        print(f"Started Stage 3 of {url}")
        if os.path.isfile(args.permutate_wordlist):
            # print(f"{path} is a regular file.")
            with open(args.permutate_wordlist, "r") as paths_file:
                for path in paths_file:
                    path = path.strip()
                    if path not in pattern_paths:
                        pattern_paths.append(path)
        elif os.path.isdir(args.permutate_wordlist):
            # print(f"{path} is a directory.")
            for f_or_d in os.listdir(args.permutate_wordlist):
                hostname = url.replace('http://', '').replace('https://', '').replace('/','').split(":")[0]

                if f"pw_{hostname}.txt" == f_or_d or f"pw_all.txt" == f_or_d:
                    # subprocess.run(
                    #     f"rg -F --text -l '{hostname}' ./../../active_crawling_and_spidering/ ./../../sources/ "
                    #     f"| xargs grep --text -lFf <(cat {args.permutate_wordlist}/{f_or_d} | sed 's|/PAYLOADDDD||g') "
                    #     f"| xargs grep --text -F -L ': {hostname}' "
                    #     f"| xargs grep --text -F -L ' http://{hostname}' "
                    #     f"| xargs grep --text -F -L ' https://{hostname}' "
                    #     f"| anew -q pf_{hostname}.txt",
                    #     shell=True,
                    #     executable='/bin/bash'
                    # )

                    # pf_file = f"pf_{hostname}.txt"

                    # # Read all lines
                    # with open(pf_file, "r") as f:
                    #     lines = f.readlines()

                    # # Filter out lines that contain "path" and end with ".txt"
                    # filtered_lines = [line for line in lines if not ("path" in line and line.strip().endswith(".txt"))]

                    # # Write the filtered lines back to the file (overwrite)
                    # with open(pf_file, "w") as f:
                    #     f.writelines(filtered_lines)

                    # pattern_cnt = 0
                    with open(f"{args.permutate_wordlist}/{f_or_d}", "r") as paths_file:
                        for path in paths_file:
                            path = path.strip()
                            # path_without_payloadddd = path.replace('/PAYLOADDDD','')
                            # if path not in pattern_paths and ( not args.filter_patterns or bool(subprocess.run(f"xargs grep -F '{hostname}/{path_without_payloadddd}' < pf_{hostname}.txt", shell=True, capture_output=True, text=True).stdout)):
                            if path not in pattern_paths:
                                pattern_paths.append(path)
                                # pattern_cnt += 1
                                # print(f"{hostname} {pattern_cnt} {path}")
        else:
            print("supplied neither file nor directory to -pw/--permutate-wordlist")
            exit()

        print(f"permut {url}: reached here 6")
        paths_permutation_list_on_num = set()
        for path in list(pattern_paths):
            for permutation_on_number in permutations_on_number(path):
                if path not in pattern_paths:
                    pattern_paths.append(permutation_on_number)
        # with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        #     results = pool.starmap(process_permutated_path, [(path, extracted_paths, tried_paths) for path in pattern_paths])

        #     with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "w") as paths_file:
        #         for result in results:
        #             for path_to_be_written in result:
        #                 paths_file.write(path_to_be_written + "\n")
        #                 tried_paths.append(path_to_be_written)

        print(f"permut {url}: reached here 5")
        # try:
        if args.subdomain_as_pattern:
            for subdomain_as_pattern in process_subdomain(extract_subdomain(url)):
                subdomain_as_pattern = subdomain_as_pattern + "/PAYLOADDDD"
                if subdomain_as_pattern in pattern_paths:
                    continue

                print(f"subdomain_as_pattern: {subdomain_as_pattern}")
                pattern_paths.append(subdomain_as_pattern)
        # except Exception as e:
        #     print(f"subdomain_as_pattern Error: {e}")

        print(f"permut {url}: reached here 1")

        for sub_pattern_paths in split_list(pattern_paths, args.pattern_split):
            subprocess.run(f"rm paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True)


            if args.slash_before_payload:
                with open(f"pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "w") as paths_file:
                    for path_to_be_written in list(set(list(paths) + extracted_paths)):
                        paths_file.write(path_to_be_written + "\n")

                cleaned_paths = set()
                for pattern_path in sub_pattern_paths:
                    cleaned_path = pattern_path.split("PAYLOADDDD")[0]
                    cleaned_paths.add(cleaned_path)

                with open(f"pw_{hostname}_is_it_slash_before_payloadddd_cook.txt", "w") as paths_file:
                    for pattern_path in cleaned_paths:
                        paths_file.write(pattern_path + "\n")

                subprocess.run(f"cat pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | sed 's/^\///g' | anew -q pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}_is_it_slash_before_payloadddd.txt", shell=True)
                subprocess.run(f"cook -l: pw_{hostname}_is_it_slash_before_payloadddd_cook.txt -p: pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}_is_it_slash_before_payloadddd.txt l p | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True)

            else:
                for pattern_path in sub_pattern_paths:
                    with open(f"pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "w") as paths_file:
                        for path_to_be_written in list(set(list(paths) + extracted_paths)):
                            paths_file.write(path_to_be_written + "\n")

                    subprocess.run(f"cp pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt untainted_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)

                    # is_it_word_specific_perm_1 = f"echo {pattern_path} | grep -q 'PAYLOADDDD~' "
                    # is_it_word_specific_perm_2 = f"echo {pattern_path} | grep -q '~PAYLOADDDD' "
                    # is_it_word_specific_perm_1 = subprocess.run(is_it_word_specific_perm_1, shell=True)
                    # is_it_word_specific_perm_2 = subprocess.run(is_it_word_specific_perm_2, shell=True)
                    # is_it_slash_before_payloadddd = f"echo {pattern_path} | grep -q '/PAYLOADDDD' "
                    # is_it_slash_after_payloadddd = f"echo {pattern_path} | grep -q 'PAYLOADDDD/' "
                    # is_it_payloadddd_between_slashes = f"echo {pattern_path} | grep -q '/PAYLOADDDD/' "

                    # # Run the check command
                    # is_it_slash_before_payloadddd = subprocess.run(is_it_slash_before_payloadddd, shell=True)
                    # is_it_slash_after_payloadddd = subprocess.run(is_it_slash_after_payloadddd, shell=True)
                    # is_it_payloadddd_between_slashes = subprocess.run(is_it_payloadddd_between_slashes, shell=True)

                    is_it_word_specific_perm_1 = 'PAYLOADDDD~' in pattern_path
                    is_it_word_specific_perm_2 = '~PAYLOADDDD' in pattern_path
                    is_it_slash_before_payloadddd = '/PAYLOADDDD' in pattern_path
                    is_it_slash_after_payloadddd = 'PAYLOADDDD/' in pattern_path
                    is_it_payloadddd_between_slashes = '/PAYLOADDDD/' in pattern_path
                    is_it_file_payloadddd = '/PAYLOADDDD.' in pattern_path

                    if is_it_file_payloadddd:
                        subprocess.run(f"echo {pattern_path} | awk -F'PAYLOADDDD' '{{print $1}}' >  pw_{hostname}.txt_for_cook_1", shell=True)
                        subprocess.run(f"echo {pattern_path} | awk -F'PAYLOADDDD' '{{print $2}}' >  pw_{hostname}.txt_for_cook_2", shell=True)
                        subprocess.run(f"cat pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | sed 's/^\///g' >  paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared", shell=True)
                        subprocess.run(f"mv paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
                        subprocess.run(f"cook -l: pw_{hostname}.txt_for_cook_1 -m: pw_{hostname}.txt_for_cook_2 -p: pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt l p m | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new", shell=True)
                        subprocess.run(f"cat paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
                        subprocess.run(f"rm pw_{hostname}.txt_for_co* paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new", shell=True)


                    if not is_it_word_specific_perm_1 and not is_it_word_specific_perm_2 and not is_it_file_payloadddd:
                        # print("entered here")
                        if is_it_payloadddd_between_slashes:
                            subprocess.run(f"echo {pattern_path} | awk -F'PAYLOADDDD' '{{print $1}}' >  pw_{hostname}.txt_for_cook_1", shell=True)
                            subprocess.run(f"echo {pattern_path} | awk -F'PAYLOADDDD' '{{print $2}}' >  pw_{hostname}.txt_for_cook_2", shell=True)
                            subprocess.run(f"cat pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | sed 's/^\///g' >  paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared", shell=True)
                            subprocess.run(f"mv paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
                            subprocess.run(f"cook -l: pw_{hostname}.txt_for_cook_1 -m: pw_{hostname}.txt_for_cook_2 -p: pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt l p m | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new", shell=True)
                        elif is_it_slash_before_payloadddd:
                            subprocess.run(f"echo {pattern_path} | sed 's/PAYLOADDDD//g' >  pw_{hostname}.txt_for_cook", shell=True)
                            # subprocess.run(f"cat pw_{hostname}.txt | grep /PAYLOADDDD | sed 's/\/PAYLOADDDD//g' >  pw_{hostname}.txt_for_cook", shell=True)
                            subprocess.run(f"cat pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | sed 's/^\///g' >  paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared", shell=True)
                            subprocess.run(f"mv paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
                            subprocess.run(f"cook -l: pw_{hostname}.txt_for_cook -p: pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt l p | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new", shell=True)

                            with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "a") as paths_file:
                            
                                for path_to_be_written in list(set(list(paths) + extracted_paths)):
                                
                                    if f'/{pattern_path.replace("/PAYLOADDDD","")}/' in path_to_be_written:
                                        part_after = path_to_be_written.split(f'/{pattern_path.replace("/PAYLOADDDD","")}/')[-1]
                                        paths_file.write(f'/{pattern_path.replace("/PAYLOADDDD","")}/{part_after}\n')

                        elif is_it_slash_after_payloadddd:
                            # subprocess.run(f"cat pw_{hostname}.txt | grep /PAYLOADDDD | sed 's/\/PAYLOADDDD//g' >  pw_{hostname}.txt_for_cook", shell=True)
                            # print("reached here1")
                            subprocess.run(f"echo {pattern_path} | sed 's/PAYLOADDDD//g' >  pw_{hostname}.txt_for_cook", shell=True)
                            # print("reached here2")
                            # exit()
                            subprocess.run(f"cat pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | sed 's/^\///g' >  paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared", shell=True)
                            subprocess.run(f"mv paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
                            subprocess.run(f"cook -l: pw_{hostname}.txt_for_cook -p: pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt p l | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new", shell=True)
                    # print(bool(is_it_slash_before_payloadddd.returnedcode))
                    # print(bool(is_it_slash_after_payloadddd))
                    # print(bool(is_it_payloadddd_between_slashes))
                        subprocess.run(f"cat paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
                        subprocess.run(f"rm pw_{hostname}.txt_for_co* paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new", shell=True)



                    # exit()

                    if args.naming_convention and (is_it_word_specific_perm_1 or is_it_word_specific_perm_2):
                        # for path_pattern in subprocess.run(f"echo {pattern_path} | grep -e ~PAYLOADDDD -e PAYLOADDDD~", shell=True, capture_output=True, text=True).stdout.split("\n"):

                        if not path_pattern:
                            continue

                        print(f"path_pattern: {path_pattern}")
                        # subpath2_exists = False
                        # subpath1_exists = False
                        if "~PAYLOADDDD~" in path_pattern:
                            parts = path_pattern.split("~PAYLOADDDD~")
                            # subpath2_exists = True
                            # subpath1_exists = True
                        elif "~PAYLOADDDD" in path_pattern:
                            # subpath1_exists = True
                            # subpath2_exists = True
                            parts = path_pattern.split("~PAYLOADDDD")
                        elif "PAYLOADDDD~" in path_pattern:
                            # subpath2_exists = True
                            # subpath1_exists = True
                            parts = path_pattern.split("PAYLOADDDD~")

                        # if subpath1_exists:
                        subpath1 = parts[0]
                        subpath1_last_part = parts[0]
                        if subpath1.split("/")[0].strip():
                            subpath1_last_part = subpath1.split("/")[0]

                        # if subpath2_exists:
                        subpath2 = parts[1]
                        subpath2_first_part = parts[1]
                        if subpath2.split("/")[0].strip():
                            subpath2_first_part = subpath2.split("/")[0]

                        for naming_convention in args.naming_convention:
                            # if subpath1_exists:
                            subpath1 = parts[0]
                            # if subpath2_exists:
                            subpath2 = parts[1]
                            if naming_convention == "snake_case":
                                # if subpath1_exists:
                                subpath1 = subpath1.replace(subpath1_last_part, subpath1_last_part.replace("~","_").lower() + "_")
                                # if subpath2_exists:
                                subpath2 = subpath2.replace(subpath2_first_part, "_" + subpath2_first_part.replace("~","_").lower())
                            elif naming_convention == "camelCase":
                                # if subpath1_exists:
                                subpath1 = subpath1.replace(subpath1_last_part, humps.camelize(subpath1_last_part.replace("~","_")))
                                # if subpath2_exists:
                                subpath2 = subpath2.replace(subpath2_first_part, humps.camelize(subpath2_first_part.replace("~","_")).capitalize())
                            elif naming_convention == "PascalCase":
                                # if subpath1_exists:
                                subpath1 = subpath1.replace(subpath1_last_part, humps.pascalize(subpath1_last_part.replace("~","_")))
                                # if subpath2_exists:
                                subpath2 = subpath2.replace(subpath2_first_part, humps.pascalize(subpath2_first_part.replace("~","_")))
                            elif naming_convention == "kebab-case":
                                # if subpath1_exists:
                                subpath1 = subpath1.replace(subpath1_last_part, humps.kebabize(subpath1_last_part.replace("~","_")).lower()  + "-")
                                # if subpath2_exists:
                                subpath2 = subpath2.replace(subpath2_first_part, "-" + humps.kebabize(subpath2_first_part.replace("~","_")).lower() )
                            # if subpath1_exists:
                            subpath1 = lowercase_or_uppercase(subpath1)
                            with open(f"subpath_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}1.txt", "w") as f1:
                                f1.write(subpath1)
                            # if subpath2_exists:
                            subpath2 = lowercase_or_uppercase(subpath2)
                            with open(f"subpath_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}2.txt", "w") as f2:
                                f2.write(subpath2)
                            subpath1_specific_args = ["",""]
                            subpath2_specific_args = ["",""]
                            # if subpath1_exists:
                            subpath1_specific_args[0] = f"-l: subpath_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}1.txt"
                            subpath1_specific_args[1] = "l"
                            # if subpath2_exists:
                            subpath2_specific_args[0] = f"-m: subpath_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}2.txt"
                            subpath2_specific_args[1] = "m"

                            subprocess.run(f"cook {subpath1_specific_args[0]} -p: untainted_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt {subpath2_specific_args[0]} {subpath1_specific_args[1]} p {subpath2_specific_args[1]} | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new", shell=True)
                            subprocess.run(f"cat paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new  | anew -q ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)

                    subprocess.run(f"rm untainted_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new subpath_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}1.txt subpath_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}2.txt ", shell=True)


            print(f"permut {url}: reached here 2")

            subprocess.run(["sed", "-i", r"s|^/||", f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"], check=True)
            if args.wordlist_ends_with:
                wordlist_ends_with_escaped_suffix = re.escape(args.wordlist_ends_with)
                subprocess.run(["sed", "-i", "-n", rf'/{wordlist_ends_with_escaped_suffix}$/p', f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"], check=True)
            
            # subprocess.run(["sed", "-i", r"s|/$||", f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"], check=True)

            # subprocess.run(f"cat paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt > paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt.new",shell=True, check=True)
            # subprocess.run(f"cat paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | sed 's|$|/|g' | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt.new",shell=True, check=True)
            # subprocess.run(f"mv paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt.new paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt",shell=True, check=True)
        
            if args.suffixes:
                subprocess.run(f"cp paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt orig_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt",shell=True, check=True)
                # subprocess.run(f"rm paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt",shell=True, check=True)
                for suffix in args.suffixes:
                    escaped_suffix = re.escape(suffix).replace('\\', r'\\').replace('&', r'\&')
                    subprocess.run(f"cat orig_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | sed 's|$|{escaped_suffix}|g' | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True, check=True)

            for method in methods:
                if os.path.exists(f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"):
                    with open(f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "r") as paths_file:
                        for path in paths_file:
                            path = path.replace("\n","")
                            tried_paths.append(path)

                    # subprocess.run(f"/home/deus/scripts/filter tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new ", shell=True)
                    # subprocess.run(f"rm ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
                    subprocess.run(f"/home/deus/scripts/filter tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | awk '!seen[$0]++' > paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new ", shell=True)
    
                    # subprocess.run(f"nproc=3 && split -n l/$nproc ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt split_part_ && parallel -j $nproc 'grep -F -v -x --text -f tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt {{}} ' ::: split_part_* | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new && rm split_part_*", shell=True)
    
    
    
                    subprocess.run(f"mv paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
    
                subprocess.run(f"/home/deus/scripts/runiq ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt > ./uniq_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True, check=True)
                
                subprocess.run(f"mv ./uniq_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True, check=True)
                
    
                # exit()
    
                print(f"permut {url}: reached here 3")
                with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", 'r') as f:
                    if any(f):
                        used_user_agents = set()
                        proxies = []
                        if args.no_proxy:
                            proxies.append("self")
                        else:
                            port, rota_proc = get_proxy_port(hostname, rate_limit, used_user_agents)
                            proxies.append(f"127.0.0.1:{port}")
    
                        proc_num = len(proxies)
                    else:
                        continue
    
                with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "r") as paths_file:
                    for path in paths_file:
                        path = path.replace("\n","")
                        tried_paths.append(path)
    
                print(f"permut {url}: reached here 4")
                # exit()
                used_proxies_across_processes = manager.list()
                pool = multiprocessing.Pool(proc_num)
                if args.paths_number == None:
                    path_files = split_file_into_n_parts(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", proc_num, url)
    
                    args_for_run_ffuf = [(part, url, proxies, used_proxies_across_processes, method) for part in path_files]
                    pool.map(run_ffuf, args_for_run_ffuf, chunksize=1)
    
                else:
                    for path_files in split_list(split_file(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", args.paths_number, url), proc_num):
                    
                        args_for_run_ffuf = [(part, url, proxies, used_proxies_across_processes, method) for part in path_files]
                        pool.map(run_ffuf, args_for_run_ffuf, chunksize=1)
                
                if not args.no_proxy:
                    rota_exit_handler(rota_proc)

            # with open(f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "a") as paths_file:
            #     for path in tried_paths:
            #         paths_file.write(path + "\n")


            # paths_output_count = 0
            # for f_or_d in os.listdir('./'):
            #     if f"directory_path_brute_output_{url.replace('http://', '').replace('https://', '').replace('/','')}" in f_or_d:
            #         paths_output_count += 1

            for method in methods:
                subprocess.run(f"cat ./endpoint_{method}_{url.replace('http://', '').replace('https://', '').replace('/','')}*.json >> endpoint_{method}_path_brute_output_{url.replace('http://', '').replace('https://', '').replace('/','')}.json ", shell=True)
                subprocess.run(f"cat ./endpoint_{method}_{url.replace('http://', '').replace('https://', '').replace('/','')}*.json | jq -r .url | unfurl paths | anew -q tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
                subprocess.run(f"rm ./endpoint_{method}_{url.replace('http://', '').replace('https://', '').replace('/','')}*", shell=True)

            # subprocess.run(f"cat ./directory_{url.replace('http://', '').replace('https://', '').replace('/','')}*.json >> directory_path_brute_output_{url.replace('http://', '').replace('https://', '').replace('/','')}.json ", shell=True)
            # subprocess.run(f"cat ./directory_{url.replace('http://', '').replace('https://', '').replace('/','')}*.json | jq -r .url | unfurl paths | anew -q tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)

            subprocess.run(["sed", "-i", r"s|^/||", f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"], check=True)
            subprocess.run(f"/home/deus/scripts/runiq tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt > output_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True, check=True)
            subprocess.run(f"mv output_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)

            # subprocess.run(f"rm ./directory_{url.replace('http://', '').replace('https://', '').replace('/','')}*", shell=True)
            subprocess.run(f"rm paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True)

        # with open(f"pw_{hostname}.txt", "w") as pattern_paths_file:
        #     for pattern_path in pattern_paths:
        #         pattern_paths_file.write(pattern_path + "\n")
    except Exception as e:
        print("Errrrrrrrrrrror:", e)


def non_permutation_based(url, extracted_paths):
    try:
    
    
        if "http://" in url or "https://" in url:
            hostname = urlparse(url).hostname
        elif ":" in url:
            hostname = url.split(":")[0]
        else:
            hostname = url

        print("reached here 0")

        tried_paths = []
        print(f"Started Stage 1 of {url}")
        # with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        #     results = pool.starmap(process_generic_path, [(path, tried_paths) for path in list(set(list(paths) + extracted_paths))])

        #     with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "w") as paths_file:
        #         for result in results:
        #             for path_to_be_written in result:
        #                 paths_file.write(path_to_be_written + "\n")
        #                 tried_paths.append(path_to_be_written)

        with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "w") as paths_file:
            for path_to_be_written in list(set(list(paths) + extracted_paths)):
                paths_file.write(path_to_be_written + "\n")
        
        subprocess.run(["sed", "-i", r"s|^/||", f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"], check=True)
        if args.wordlist_ends_with:
            wordlist_ends_with_escaped_suffix = re.escape(args.wordlist_ends_with)
            subprocess.run(["sed", "-i", "-n", rf'/{wordlist_ends_with_escaped_suffix}$/p', f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"], check=True)
        
        # subprocess.run(["sed", "-i", r"s|/$||", f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"], check=True)

        # subprocess.run(f"cat paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt > paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt.new",shell=True, check=True)
        # subprocess.run(f"cat paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | sed 's|$|/|g' | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt.new",shell=True, check=True)
        # subprocess.run(f"mv paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt.new paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt",shell=True, check=True)

        print("reached here 000")

        if args.suffixes:
            subprocess.run(f"cp paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt orig_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt",shell=True, check=True)
            # subprocess.run(f"rm paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt",shell=True, check=True)
            for suffix in args.suffixes:
                escaped_suffix = re.escape(suffix).replace('\\', r'\\').replace('&', r'\&')
                subprocess.run(f"cat orig_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | sed 's|$|{escaped_suffix}|g' | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True, check=True)

        print("reached here 111")

        for method in methods:
            if os.path.exists(f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"):
                with open(f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "r") as paths_file:
                    for path in paths_file:
                        path = path.replace("\n","")
                        tried_paths.append(path)
                # subprocess.run(f"/home/deus/scripts/filter tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new ", shell=True)

                # subprocess.run(f"nproc=3 && split -n l/$nproc ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt split_part_ && parallel -j $nproc 'grep -F -v -x --text -f tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt {{}} ' ::: split_part_* | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new && rm split_part_*", shell=True)

                subprocess.run(f"/home/deus/scripts/filter tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new ", shell=True)

                # subprocess.run(f"rm ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
                subprocess.run(f"mv paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)

            print("reached here 2222")
            subprocess.run(f"/home/deus/scripts/runiq ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt > ./uniq_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True, check=True)
                
            subprocess.run(f"mv ./uniq_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True, check=True)
                
    
            with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", 'r') as f:
                if any(f):
                    used_user_agents = set()
                    proxies = []
                    if args.no_proxy:
                        proxies.append("self")
                    else:
                        port, rota_proc = get_proxy_port(hostname, rate_limit, used_user_agents)
                        proxies.append(f"127.0.0.1:{port}")
    
                    proc_num = len(proxies)
                else:
                    continue
    
            with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "r") as paths_file:
                for path in paths_file:
                    path = path.replace("\n","")
                    tried_paths.append(path)
    
            used_proxies_across_processes = manager.list()
            pool = multiprocessing.Pool(proc_num)
            if args.paths_number == None:
                path_files = split_file_into_n_parts(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", proc_num, url)
    
                args_for_run_ffuf = [(part, url, proxies, used_proxies_across_processes, method) for part in path_files]
                pool.map(run_ffuf, args_for_run_ffuf, chunksize=1)
    
                # pool.map(run_ffuf, split_file_into_n_parts(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", proc_num, url), chunksize=1)
            else:
                for path_files in split_list(split_file(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", args.paths_number, url), proc_num):
                
                    args_for_run_ffuf = [(part, url, proxies, used_proxies_across_processes, method) for part in path_files]
                    pool.map(run_ffuf, args_for_run_ffuf, chunksize=1)
    
            if not args.no_proxy:
                rota_exit_handler(rota_proc)

                    # pool.map(run_ffuf, path_files, chunksize=1)
        
        # Stage 2
        print(f"Started Stage 2 of {url}")
        subdomain_pattern_paths  = []
        for subdomain_as_pattern in process_subdomain(extract_subdomain(url)):
            if subdomain_as_pattern not in paths or subdomain_as_pattern + "/" not in paths or "/" + subdomain_as_pattern not in paths or "/" + subdomain_as_pattern + "/" not in paths:
                continue

            subdomain_pattern_paths.append(subdomain_as_pattern + "/PAYLOADDDD")
        # with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        #     results = pool.starmap(process_permutated_path, [(path, extracted_paths, tried_paths) for path in subdomain_pattern_paths])
        #     with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "w") as paths_file:
        #         for result in results:
        #             for path_to_be_written in result:
        #                 paths_file.write(path_to_be_written + "\n")
        #                 tried_paths.append(path_to_be_written)

        # we're skipping it for now
        subdomain_pattern_paths  = []
        if subdomain_pattern_paths:
            with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "w") as paths_file:
                for path_to_be_written in list(set(list(paths) + extracted_paths)):
                    paths_file.write(path_to_be_written + "\n")

            with open(f"subdomain_pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "w") as subdomain_pattern_paths_file:
                for subdomain_pattern_path in subdomain_pattern_paths:
                    subdomain_pattern_paths_file.write(subdomain_pattern_path + "\n")
            subprocess.run(f"cat subdomain_pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | sed 's/\/PAYLOADDDD//g' >  subdomain_pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared", shell=True)
            subprocess.run(f"rm subdomain_pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
            subprocess.run(f"mv subdomain_pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared subdomain_pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
            subprocess.run(f"cat paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | sed 's/^\///g' >  paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared", shell=True)
            subprocess.run(f"rm paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
            subprocess.run(f"mv paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_prepared paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
            subprocess.run(f"cook -l: subdomain_pattern_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt -p: paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt l / p | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new", shell=True)
            subprocess.run(f"rm ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
            subprocess.run(f"mv paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
            subprocess.run(["sed", "-i", r"s|^/||", f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"], check=True)
            if args.wordlist_ends_with:
                wordlist_ends_with_escaped_suffix = re.escape(args.wordlist_ends_with)
                subprocess.run(["sed", "-i", "-n", rf'/{wordlist_ends_with_escaped_suffix}$/p', f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"], check=True)
            
            for method in methods:
            # subprocess.run(["sed", "-i", r"s|/$||", f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"], check=True)
                if os.path.exists(f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"):
                    # subprocess.run(f"/home/deus/scripts/filter tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new ", shell=True)
                    # subprocess.run(f"rm ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
                    # subprocess.run(f"nproc=3 && split -n l/$nproc ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt split_part_ && parallel -j $nproc 'grep -F -v -x --text -f tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt {{}} ' ::: split_part_* | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new && rm split_part_*", shell=True)
                    
                    with open(f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "r") as paths_file:
                        for path in paths_file:
                            path = path.replace("\n","")
                            tried_paths.append(path)
                    
                    subprocess.run(f"/home/deus/scripts/filter tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt | anew -q paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new ", shell=True)

                    subprocess.run(f"mv paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt_new ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)

                subprocess.run(f"/home/deus/scripts/runiq ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt > ./uniq_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True, check=True)
                
                subprocess.run(f"mv ./uniq_paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ./paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True, check=True)
                
    
    
                with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", 'r') as f:
                    if any(f):
                        used_user_agents = set()
                        proxies = []
                        if args.no_proxy:
                            proxies.append("self")
                        else:
                            port, rota_proc = get_proxy_port(hostname, rate_limit, used_user_agents)
                            proxies.append(f"127.0.0.1:{port}")

                        proc_num = len(proxies)
                    else:
                        continue
    
                with open(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "r") as paths_file:
                    for path in paths_file:
                        path = path.replace("\n","")
                        tried_paths.append(path)

                used_proxies_across_processes = manager.list()
                pool = multiprocessing.Pool(proc_num)
                if args.paths_number == None:

                    path_files = split_file_into_n_parts(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", proc_num, url)

                    args_for_run_ffuf = [(part, url, proxies, used_proxies_across_processes, method) for part in path_files]
                    pool.map(run_ffuf, args_for_run_ffuf, chunksize=1)

                    # pool.map(run_ffuf, split_file_into_n_parts(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", proc_num, url), chunksize=1)
                else:
                    for path_files in split_list(split_file(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", args.paths_number, url), proc_num):

                        args_for_run_ffuf = [(part, url, proxies, used_proxies_across_processes, method) for part in path_files]
                        pool.map(run_ffuf, args_for_run_ffuf, chunksize=1)

                if not args.no_proxy:
                    rota_exit_handler(rota_proc)

                # for path_files in split_list(split_file(f"paths_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", args.paths_number), proc_num, url):
                #     pool.map(run_ffuf, path_files, chunksize=1)
        # with open(f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "a") as paths_file:
        #     for path in tried_paths:
        #         paths_file.write(path + "\n")

        # subprocess.run(f"/home/deus/scripts/runiq tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt > output_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True, check=True)
        # subprocess.run(f"mv output_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)

        # subprocess.run(
        #     ["awk", "-u", "-o", f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"],
        #     stdin=open(f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", "r")
        #                 )

        # paths_output_count = 0
        # for f_or_d in os.listdir('./'):
        #     if f"endpoint_path_brute_output_{url.replace('http://', '').replace('https://', '').replace('/','')}" in f_or_d:
        #         paths_output_count += 1

        for method in methods:
            # if method != "GET_DIRECTORY":
            subprocess.run(f"cat ./endpoint_{method}_{url.replace('http://', '').replace('https://', '').replace('/','')}*.json >> endpoint_{method}_path_brute_output_{url.replace('http://', '').replace('https://', '').replace('/','')}.json ", shell=True)
            subprocess.run(f"cat ./endpoint_{method}_{url.replace('http://', '').replace('https://', '').replace('/','')}*.json | jq -r .url | unfurl paths | anew -q tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)
            subprocess.run(f"rm ./endpoint_{method}_{url.replace('http://', '').replace('https://', '').replace('/','')}*", shell=True)

        # subprocess.run(f"cat ./directory_{url.replace('http://', '').replace('https://', '').replace('/','')}*.json >> directory_path_brute_output_{url.replace('http://', '').replace('https://', '').replace('/','')}.json ", shell=True)
        # subprocess.run(f"cat ./directory_{url.replace('http://', '').replace('https://', '').replace('/','')}*.json | jq -r .url | unfurl paths | anew -q tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)

        subprocess.run(["sed", "-i", r"s|^/||", f"tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt"], check=True)
        subprocess.run(f"/home/deus/scripts/runiq tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt > output_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt", shell=True, check=True)
        subprocess.run(f"mv output_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt tried_paths_for_{method}_{url.replace('http://', '').replace('https://', '').replace('/','').replace('/','')}.txt ", shell=True)

        # subprocess.run(f"rm ./directory_{url.replace('http://', '').replace('https://', '').replace('/','')}*", shell=True)

    except Exception as e:
        print("Errrror:", e)

def main():
    max_workers = args.nhosts
    last_start = time.monotonic()
    futures = []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for url, paths in urls.items():
            # throttle start times
            now = time.monotonic()
            wait = 10 - (now - last_start)
            if wait > 0:
                time.sleep(wait)
            last_start = time.monotonic()

            if args.permutate_wordlist is None:
                futures.append(pool.submit(non_permutation_based, url, paths))
            else:
                futures.append(pool.submit(permutation_based, url, paths))

        # collect results as they finish (or just do [f.result() for f in futures])
        results = []
        for fut in as_completed(futures):
            results.append(fut.result())

    return results



main()
        
stop_event.set()

print("Done")
