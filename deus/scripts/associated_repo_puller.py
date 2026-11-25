import argparse
from urllib.parse import urlparse, parse_qs, parse_qsl, quote, unquote, urlencode, urlunparse
import requests
import subprocess
import os
import hashlib
import time
import socket
import random
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import signal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import threading
import copy
import json

os.environ['PYTHONUNBUFFERED'] = "1"

os.makedirs("downloads", exist_ok=True)

def is_port_available(port, host='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False

available_port = ""

ports = list(range(8000, 9000))
random.shuffle(ports)

for port in ports:
    if is_port_available(port):
        available_port = port
        break

# rota_proc = subprocess.Popen(
#     ["rota", "--config", "./rota_config.yml", "-p", f"{available_port}"],
#     stdout=subprocess.DEVNULL,
#     stderr=subprocess.DEVNULL,
#     preexec_fn=os.setsid
# )

# while is_port_available(available_port):
#     time.sleep(5)


proxies = {
    'http': f'http://127.0.0.1:{available_port}',
    'https': f'http://127.0.0.1:{available_port}',
}


# Define a retry strategy
retry_strategy = Retry(
    total=5,                         # Total number of retries
    status_forcelist=[502],         # Retry on 502 errors
    allowed_methods=["HEAD", "GET", "OPTIONS"],  # Methods to retry
    backoff_factor=1,               # Wait time between retries: 1s, 2s, 4s...
)

# Create adapter with the retry strategy
adapter = HTTPAdapter(max_retries=retry_strategy)

# Load user-agents from file
with open('/home/deus/documents/user_agents_aa', 'r') as f:
    USER_AGENTS = [line.strip() for line in f if line.strip()]

with open('/home/deus/documents/user_agents_ab', 'r') as f:
    USER_AGENTS.extend([line.strip() for line in f if line.strip()])

class RandomUserAgentSession(requests.Session):
    def __init__(self, user_agents):
        super().__init__()
        self.user_agents = user_agents

    def request(self, method, url, **kwargs):
        headers = kwargs.pop('headers', {})
        headers['User-Agent'] = random.choice(self.user_agents)
        kwargs['headers'] = headers
        return super().request(method, url, **kwargs)

# Create a session and mount the adapter
session = RandomUserAgentSession(USER_AGENTS)
session.mount("http://", adapter)
session.mount("https://", adapter)
session.verify = False
# session.proxies.update(proxies)
# session.headers.update({
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
# })

def rota_exit_handler(rota_proc):
    os.killpg(os.getpgid(rota_proc.pid), signal.SIGKILL)

    try:
        rota_proc.wait(timeout=5)
    except Exception:
        pass

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

def escape_lucene_regex(s):


    lucene_specials = r'+-!():^[]{}"~*?|&\/.'  # characters that need escaping
    escaped = ''
    for char in s:
        if char in lucene_specials:
            escaped += fr'\{char}'
        else:
            escaped += char
    

    # result = re.sub(r'^(?:\\/)+', r'', escaped)

    return escaped


def prepare_grep_app_params(query_strings, normal_query, special_query, banner_query):
    params = list()

    for query_string in query_strings:

        if normal_query:

            # param = {
            #     "f.lang": "HTML",
            #     "f.lang": "HTML+ERB",
            #     "f.lang": "HTML+Razor",
            #     "f.lang": "HTML+Django",
            #     "f.lang": "HTML+EEX",
            #     "f.lang": "HTML+ECR",
            #     "f.lang": "RHTML",
            #     "f.lang": "PHTML",
            #     "q": query_string,
            #     "page": '1'
            # }

            param = [
                ("q", query_string),
                ("page", "1")
            ]

            params.append(param)
        
        if special_query:
            param = [
                ("q", query_string),
                ("page", "1")
            ]

            params.append(param)

            for keyword in special_keywords:
                query1 = escape_lucene_regex(query_string)
                # query2 = f'[ /]?{keyword}[ /]?'
                query2 = keyword

                # param = {
                #     "f.lang": "HTML",
                #     "f.lang": "HTML+ERB",
                #     "f.lang": "HTML+Razor",
                #     "f.lang": "HTML+Django",
                #     "f.lang": "HTML+EEX",
                #     "f.lang": "HTML+ECR",
                #     "f.lang": "RHTML",
                #     "f.lang": "PHTML",
                #     "regexp": "true",
                #     "q": f"(?s){query1}.*{query2}",
                #     "page": '1'
                # }

                param = [
                    ("regexp", "true"),
                    ("q", f"(?s){query1}.*{query2}"),
                    ("page", "1")
                ]

                params.append(param)

                # param = {
                #     "f.lang": "HTML",
                #     "f.lang": "HTML+ERB",
                #     "f.lang": "HTML+Razor",
                #     "f.lang": "HTML+Django",
                #     "f.lang": "HTML+EEX",
                #     "f.lang": "HTML+ECR",
                #     "f.lang": "RHTML",
                #     "f.lang": "PHTML",
                #     "regexp": "true",
                #     "q": f"(?s){query2}.*{query1}",
                #     "page": '1'
                # }

                param = [
                    ("regexp", "true"),
                    ("q", f"(?s){query2}.*{query1}"),
                    ("page", "1")
                ]

                params.append(param)
        
        if banner_query:
            param = [
                ("q", f' {query_string} '),
                ("f.lang", "Markdown"),
                ("page", "1")
            ]

            params.append(param)

            for keyword in special_keywords:
                query1 = escape_lucene_regex(query_string)
                # query2 = f'[ /]?{keyword}[ /]?'
                query2 = keyword

                # param = {
                #     "f.lang": "HTML",
                #     "f.lang": "HTML+ERB",
                #     "f.lang": "HTML+Razor",
                #     "f.lang": "HTML+Django",
                #     "f.lang": "HTML+EEX",
                #     "f.lang": "HTML+ECR",
                #     "f.lang": "RHTML",
                #     "f.lang": "PHTML",
                #     "regexp": "true",
                #     "q": f"(?s){query1}.*{query2}",
                #     "page": '1'
                # }

                param = [
                    ("regexp", "true"),
                    ("q", f"(?s) {query1} .* {query2} "),
                    ("f.lang", "Markdown"),
                    ("page", "1")
                ]

                params.append(param)

                # param = {
                #     "f.lang": "HTML",
                #     "f.lang": "HTML+ERB",
                #     "f.lang": "HTML+Razor",
                #     "f.lang": "HTML+Django",
                #     "f.lang": "HTML+EEX",
                #     "f.lang": "HTML+ECR",
                #     "f.lang": "RHTML",
                #     "f.lang": "PHTML",
                #     "regexp": "true",
                #     "q": f"(?s){query2}.*{query1}",
                #     "page": '1'
                # }

                param = [
                    ("regexp", "true"),
                    ("q", f"(?s) {query2} .* {query1} "),
                    ("f.lang", "Markdown"),
                    ("page", "1")
                ]

                params.append(param)

    return params

def prepare_github_params(query_strings, normal_query, special_query, banner_query):
    params = list()

    for query_string in query_strings:
        if normal_query:
            param = {
                "q": query_string,
                "page": '1',
                "per_page": '100'
            }

            params.append(param)

        if special_query:
            param = {
                "q": query_string,
                "page": '1',
                "per_page": '100'
            }

            params.append(param)
            
            for keyword in special_keywords:
                query1 = query_string
                query2 = keyword

                param = {
                    "q": f'"{query1}" AND "{query2}"',
                    "page": '1',
                    "per_page": '100'
                }

                params.append(param)
        
        if banner_query:
            param = {
                "q": f' {query_string} ',
                "page": '1',
                "per_page": '100',
                "sort": 'stars'
            }

            params.append(param)
            
            for keyword in special_keywords:
                query1 = query_string
                query2 = keyword

                param = {
                    "q": f'" {query1} " AND " {query2} "',
                    "page": '1',
                    "per_page": '100',
                    "sort": 'stars'
                }

                params.append(param)

    return params

def increment_page(params, count):
    return [(k, str(count) if k == "page" and isinstance(v, str) else v) if k == "page" else (k, v) for (k, v) in params]

def fetch_all_grep_app_pages(params):
    encoded_params = '&'.join(f"{custom_quote(k)}={custom_quote(v)}" for k, v in params)
    url = f"{grep_app_url}?{encoded_params}"

    print(f"fetch_all_grep_app_pages's url: {url}")

    stack = [url]
    pages_data = []
    last_set_of_repos = list()
    no_change_detected = 0

    page_count = 1
    
    while stack:
        current_url = stack.pop()

        error_count = 0
        while True:
            try:
                response = session.get(current_url, cookies={})

                if response.status_code != 200:
                    print(f"Request failed: {current_url} {response.status_code} {response.text}")
                    return pages_data
                    # exit()

                data = response.json()
                pages_data.append(data)

                # link_header = response.headers.get("link", "")
                set_of_repos = [hit['path']['raw'] for hit in data.get('hits', {}).get('hits', []) if 'repo' in hit and 'raw' in hit['repo']]
            except Exception as e:
                print("Error:", e)
                error_count += 1
                if error_count == 3:
                    break

                continue
            
            break
        
        if sorted(last_set_of_repos) == sorted(set_of_repos):
            no_change_detected += 1
        else:
            last_set_of_repos = set_of_repos

        if len(set_of_repos) == 0 or no_change_detected == 3:
            return pages_data
        
        # next_url = increment_page_in_url(current_url)
        page_count += 1
        next_page = increment_page(params, page_count)
        next_encoded_params = '&'.join(f"{custom_quote(k)}={custom_quote(v)}" for k, v in next_page)
        next_url = f"{grep_app_url}?{next_encoded_params}"

        print("next_url: " + next_url)
        stack.append(next_url)

            

    return pages_data

def custom_quote(s):
    encode_set = ":?#@& ;=+%"
    # Safe characters are all printable ASCII except the ones to encode
    all_ascii = ''.join(chr(i) for i in range(32, 127))
    safe_chars = ''.join(c for c in all_ascii if c not in encode_set)
    return quote(s, safe=safe_chars)

def get_repos_and_resources_from_grep_app(params):
    try:
        # time.sleep(1)

        # first_page_url = add_query_params(grep_app_url, params)
        encoded_params = '&'.join(f"{custom_quote(k)}={custom_quote(v)}" for k, v in params)

        first_page_url = f"{grep_app_url}?{encoded_params}"

        repos = list()
        repo_for_resources = list()
        resources = list()

        error_count = 0
        while True:
            response = session.get(first_page_url, cookies={})
            try:
                data = response.json()

                repos.extend([f"https://github.com/{hit['repo']['raw']}.git" for hit in data.get('hits', {}).get('hits', []) if 'repo' in hit and 'raw' in hit['repo']])


                if data["hits"]["total"] > 5000 or data["hits"]["total"] == 0:
                    return [], [], data["hits"]["total"]
            except:
                # Print the status code
                print("Status Code:", response.status_code)

                # Print all headers
                print("Headers:", response.headers)

                # Print the response body (as text)
                print("Body:", response.text)
                error_count += 1
                if error_count == 3:
                    break

                continue

            break

        for data in fetch_all_grep_app_pages(params):
            try:
                repos.extend([f"https://github.com/{hit['repo']['raw']}.git" for hit in data.get('hits', {}).get('hits', []) if 'repo' in hit and 'raw' in hit['repo']])
            except Exception as e:
                print("Error:", e)

            try:
                repo_for_resources.extend([hit['repo']['raw'] for hit in data.get('hits', {}).get('hits', []) if 'repo' in hit and 'raw' in hit['repo']])
            except Exception as e:
                print("Error:", e)

        # repo_for_resources = list(set(repo_for_resources))
        repo_for_resources = list(dict.fromkeys(repo_for_resources))

        print("reached here 2")
        for repo in repo_for_resources:

            repo_params = copy.deepcopy(params)

            # Modify the "q" parameter
            new_q_value = "/"
            repo_params = [(k, new_q_value if k == "q" else v) for k, v in repo_params]

            repo_params.extend([("f.lang", "HTML"),
                    ("f.lang", "JavaScript"),
                    ("f.lang", "TypeScript"),
                    ("f.lang", "Markdown"),
                    ("f.lang", "HTML+ERB"),
                    ("f.lang", "HTML+Razor"),
                    ("f.lang", "HTML+Django"),
                    ("f.lang", "HTML+EEX"),
                    ("f.lang", "HTML+ECR"),
                    ("f.lang", "RHTML"),
                    ("f.lang", "PHTML"),
                    ("f.repo", repo)])

            encoded_params = '&'.join(f"{custom_quote(k)}={custom_quote(v)}" for k, v in repo_params)

            first_repo_url = f"{grep_app_url}?{encoded_params}"

            response = session.get(first_repo_url, cookies={})
            # try:
            data = response.json()

            print("reached here 0")

            if data["hits"]["total"] > 20 or data["hits"]["total"] == 0:
                continue

            print("reached here 1")

            for data in fetch_all_grep_app_pages(repo_params):
                print("reached here 5")
                try:
                    resources.extend([f"https://raw.githubusercontent.com/{hit['repo']['raw']}/refs/heads/{hit['branch']['raw']}/{hit['path']['raw']}" for hit in data.get('hits', {}).get('hits', []) if 'repo' in hit and 'raw' in hit['repo']])
                except Exception as e:
                    print("Error:", e)


            print(f"reached here 4 {len(set(resources))}")
            if len(set(resources)) > 250:
                break

        print("reached here 3")

        repos = list(set(repos))
        resources = list(set(resources))

        if len(repos) > 10:
            repos = []

        # if len(resources) > 5000:
        #     resources = []
        #     print("more than 5000")
        # else:
        #     print("less than 5000")


        return repos, resources, data["hits"]["total"]
    except Exception as e:

        # log_file = open("logfile.log", "a")
        # log_file.write(f"Error:{e}")
        # log_file.close()
        print("Error:", e)




def grep_app_no_skip_handler(grep_app_params):
    global repos
    global resources
    
    for param in grep_app_params:

        log_file = open("logfile.log", "a")
        log_file.write(f"grep app querying: {param}\n")
        log_file.close()

        param_repos, param_resources, total_count = get_repos_and_resources_from_grep_app(param)

        repos.extend(param_repos)
        resources.extend(param_resources)

def grep_app_skip_handler(grep_app_params):
    global repos
    global resources
    
    param_without_special_keyword_total_count = 0
    for param in grep_app_params:

        log_file = open("logfile.log", "a")
        log_file.write(f"grep app querying: {param}\n")
        log_file.close()

        if param_without_special_keyword_total_count == 0 and grep_app_params.index(param) % ((len(special_keywords) * 2) + 1) != 0:
            log_file = open("logfile.log", "a")
            log_file.write(f"skipped grep app querying: {param}\n")
            log_file.close()
            continue

        param_repos, param_resources, total_count = get_repos_and_resources_from_grep_app(param)

        if grep_app_params.index(param) % ((len(special_keywords) * 2) + 1) == 0:
            param_without_special_keyword_total_count = total_count

        repos.extend(param_repos)
        resources.extend(param_resources)


github_access_token_header =  { "Authorization": "Bearer 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"}

github_undownloadable_resources = dict()
def get_downloadable_resource(resource_url):

    if resource_url in list(github_undownloadable_resources.keys()):
        return github_undownloadable_resources[resource_url]
        
    
    time.sleep(2)

    print("resource_url: " + resource_url)


    response = session.get(resource_url, headers=github_access_token_header, cookies={})
    data = response.json()


    try:
        downloadable_resource_url = data["download_url"]
        print("downloadable_resource_url: " + downloadable_resource_url)
    except:
        print("error getting download_url: " + str(data))

    github_undownloadable_resources[resource_url] = downloadable_resource_url
    
    return downloadable_resource_url

def get_downloadable_resource_local(html_url):
    return "/".join(html_url.replace("github.com","raw.githubusercontent.com").split("/blob/", 1))

github_stars_count = dict()
def get_stars_count(repo_url):

    if repo_url in list(github_stars_count.keys()):
        return github_stars_count[repo_url]
    
    time.sleep(2)

    response = session.get(repo_url, headers=github_access_token_header, cookies={})
    data = response.json()
    star_count = len(data)

    github_undownloadable_resources[repo_url] = star_count

    return star_count

def get_clone_url(repo_url):
    time.sleep(2)

    response = session.get(repo_url, headers=github_access_token_header, cookies={})
    data = response.json()
    clone_url = data["clone_url"]

    return clone_url

def increment_page_in_url(url):
    """
    Increments the 'page' query parameter in the URL by 1.
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query = {k: v[0] for k, v in query.items()}
    current_page = int(query['page'])
    query['page'] = str(current_page + 1)
    

    return add_query_params(url, query)

    # return url.replace(f"page={query['page']}", f"page={current_page + 1}")
    

def fetch_all_github_code_pages(url):
    stack = [url]
    pages_data = []
    
    while stack:
        time.sleep(7)
        current_url = stack.pop()

        if "page=5" in current_url:
            return pages_data
        
        response = session.get(current_url, headers=github_access_token_header, cookies={})

        if response.status_code != 200:
            print(f"Request failed: {current_url} {response.status_code} {response.text}")
            return pages_data

        data = response.json()
        pages_data.append(data)

        link_header = response.headers.get("link", "")
        if 'rel="next"' in link_header:
            next_url = increment_page_in_url(current_url)

            log_file = open("logfile2.log", "a")
            log_file.write(f"next_url: {next_url}\n")
            log_file.close()

            stack.append(next_url)

            

    return pages_data
  

def fetch_all_github_repo_pages(url):
    stack = [url]
    pages_data = []
    
    while stack:
        time.sleep(3)
        current_url = stack.pop()

        if "page=5" in current_url:
            return pages_data
        
        response = session.get(current_url, headers=github_access_token_header, cookies={})

        if response.status_code != 200:
            print(f"Request failed: {current_url} {response.status_code} {response.text}")
            return pages_data

        data = response.json()
        pages_data.append(data)

        link_header = response.headers.get("link", "")
        if 'rel="next"' in link_header:
            next_url = increment_page_in_url(current_url)
            
            log_file = open("logfile2.log", "a")
            log_file.write(f"next_url: {next_url}\n")
            log_file.close()

            stack.append(next_url)

            

    return pages_data

def get_less_than_n_characters_repo(repos, upper_bound_repo_len):
    repo_query_string = ""
    repo_query_list = []
    for repo in repos:
        if len(repo_query_list) == 5:
            break
        
        temp_repo_query_list = copy.copy(repo_query_list)
        temp_repo_query_list.append(repo)

        temp_repo_query_string = f"({' OR '.join([f'repo:{repo}' for repo in temp_repo_query_list])})"

        if len(temp_repo_query_string) < upper_bound_repo_len:
            repo_query_string = temp_repo_query_string
            repo_query_list = temp_repo_query_list


    return repo_query_string, repo_query_list

def get_repos_and_resources_from_github_with_banner(params):
    time.sleep(3)
    
    first_page_url = add_query_params(github_search_repo_url, params)

    response = session.get(first_page_url, headers=github_access_token_header, cookies={})
    try:
        first_page_data = response.json()
    except:
        # Print the status code
        print("Status Code:", response.status_code)

        # Print all headers
        print("Headers:", response.headers)

        # Print the response body (as text)
        print("Body:", response.text)

    try:
        if first_page_data["total_count"] > 10000 or first_page_data["total_count"] == 0:
            return [], [], first_page_data["total_count"]
    except Exception as e:
        print("Error:", e)
        print(first_page_data)
        # exit()


    repos = list()
    repo_for_resources = list()
    resources = list()

    repo_urls = []

    for data in fetch_all_github_repo_pages(first_page_url):

        log_file = open("logfile2.log", "a")
        log_file.write(f"here 1\n")
        log_file.close()

        repo_for_resources.extend([urlparse(item["html_url"]).path[1:] for item in data.get("items", [])])

        repos.extend([item["clone_url"] for item in data.get("items", [])])
    
    repo_for_resources = list(dict.fromkeys(repo_for_resources))
    repos = list(dict.fromkeys(repos))

    # skipping resource download for now

    return repos, resources, first_page_data["total_count"]



    repos_params = {
                "q": f'/ language:html OR language:Markdown ',
                "page": '1',
                "per_page": '100'
            }
    
    # already_searched_repos = []
    # while len(repos) != len(already_searched_repos):
    #     unused_repos = list(set(repos) - set(already_searched_repos))
        
    #     query_len = len(repos_params["q"])
    #     free_query_len = 256 - query_len

    #     repo_query_string, repo_query_list = get_less_than_n_characters_repo(unused_repos, free_query_len)


    search_count = 0
    for repo in repo_for_resources:
        this_repos_params = copy.deepcopy(repos_params)
        this_repos_params["q"] += f"repo:{repo}"

        first_page_url = add_query_params(github_search_code_url, this_repos_params)

        for data in fetch_all_github_code_pages(first_page_url):
            
            log_file = open("logfile2.log", "a")
            log_file.write(f"here 2\n")
            log_file.close()



            # if len(resources) < 100:
                # repos.extend(list(set([item["repository"]["url"] for item in data.get("items", []) if get_stars_count(item["repository"]["stargazers_url"]) > 10 ])))
                # resources.extend(list)
            
            resources.extend(list(set([get_downloadable_resource_local(item["html_url"]) for item in data.get("items", [])])))
        
        search_count += 1
        if search_count == 50:
            break
    

    # if len(repos) < 10:
    #     repos = [get_clone_url(repo) for repo in repos]
    
    
    return repos, resources, first_page_data["total_count"]

def get_repos_and_resources_from_github(params):
    time.sleep(7)
    
    first_page_url = add_query_params(github_search_code_url, params)

    response = session.get(first_page_url, headers=github_access_token_header, cookies={})
    try:
        first_page_data = response.json()
    except:
        # Print the status code
        print("Status Code:", response.status_code)

        # Print all headers
        print("Headers:", response.headers)

        # Print the response body (as text)
        print("Body:", response.text)

    try:
        if first_page_data["total_count"] > 5000 or first_page_data["total_count"] == 0:
            return [], [], first_page_data["total_count"]
    except Exception as e:
        print("Error:", e)
        print(first_page_data)
        # exit()


    repos = list()
    resources = list()

    repo_urls = []

    for data in fetch_all_github_code_pages(first_page_url):
        if len(resources) < 100:
            repos.extend(list(set([item["repository"]["url"] for item in data.get("items", []) if get_stars_count(item["repository"]["stargazers_url"]) > 10 ])))
            resources.extend(list(set([get_downloadable_resource(item["url"]) for item in data.get("items", [])])))
    
    repos = list(set(repos))
    if len(repos) < 10:
        repos = [get_clone_url(repo) for repo in repos]
    
    
    return repos, resources, first_page_data["total_count"]

def download_url_if_small(url):
    # time.sleep(2)
    print(f"Started downloading: {url}")
    max_size = 50 * 1024 * 1024  # 50 MB
    
    sha256 = hashlib.sha256()
    # checksum = sha256.hexdigest()
    temp_path = os.path.join(os.getcwd(), "temp_download")

    os.makedirs(temp_path, exist_ok=True)

    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip("/").split("/")
    filename = path_parts[-1]
    directory_path = os.path.join(os.getcwd(), "downloads", *path_parts[:-1])

    os.makedirs(directory_path, exist_ok=True)

    try:
        with session.get(url, stream=True, cookies={}) as r:
            r.raise_for_status()
            total = 0
            with open(f'{directory_path}/{filename}', 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        total += len(chunk)
                        if total > max_size:
                            f.close()
                            os.remove(f'{directory_path}/{filename}')
                            print(f"Aborted downloading {url}: file too large")
                            return
                        sha256.update(chunk)
                        f.write(chunk)

        # move_and_override(f'{temp_path}/{filename}', directory_path)

        # print(f"File saved to: {directory_path}")
    
    except Exception as e:
        print("Error:", e)

def split_list(lst, n):
    """
    Splits a list into a list of lists, with each sublist containing `n` elements.

    :param lst: The original list to be split.
    :param n: The number of elements per sublist.
    :return: A list of sublists.
    """
    return [lst[i:i+n] for i in range(0, len(lst), n)]


download_resource_lock = threading.Lock()
extract_resource_lock = threading.Lock()
def download_resources(resource_url):
    global resource_count
    global len_resources

    with download_resource_lock:

        resource_count += 1
        print(f'Finished: {resource_count}/{len_resources}')
        if resource_count % 100000 == 0:
            files = os.listdir('.')
            tarballs_count = len([f for f in files if f.endswith('.tar.gz') or f.endswith('.tgz')])
            
            subprocess.run(f"tar -czf downloads{tarballs_count}.tar.gz downloads/ && rm -rf downloads/ && mkdir downloads", shell=True)


    # for resource_url in resources_urls:

    # Extract GitHub username from the URL
    parsed_url = urlparse(resource_url)
    path_parts = parsed_url.path.strip("/").split("/")
    github_user = path_parts[0]  # "example" in this case
    repo_name = path_parts[1]  # "example" in this case
    download_url_if_small(resource_url)

def delete_non_html_md_files(root_dir):
    for root, _, files in os.walk(root_dir):
        for filename in files:
            if not (filename.endswith('.htm') or filename.endswith('.html') or filename.endswith('.md') or filename.endswith('.cshtml') or filename.endswith('.js') or filename.endswith('.php') or filename.endswith('.xhtml') or filename.endswith('.shtml') or filename.endswith('.asp') or filename.endswith('.aspx') or filename.endswith('.erb') or filename.endswith('.ejs') or filename.endswith('.hbs') or filename.endswith('.mustache') or filename.endswith('.vbhtml') or filename.endswith('.razor') or filename.endswith('.rhtml') or filename.endswith('.ecr') or filename.endswith('.eex') or filename.endswith('.json') or filename.endswith('.yaml') or filename.endswith('.yml') or filename.endswith('.ini') or filename.endswith('.xml') or filename.endswith('.conf') or filename.endswith('.cfg') or filename.endswith('.properties') or filename.endswith('.env') or filename.endswith('.plist')):
                file_path = os.path.join(root, filename)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

def get_disk_usage(path):
    """Returns used space in bytes for the disk containing 'path'."""
    total, used, free = shutil.disk_usage(path)
    return used

in_extraction = False
def download_repo(repo_url):
    global repo_count
    global len_repos
    global in_extraction
    git_retry_count = 0

    with download_resource_lock:
        repo_count += 1

        log_file = open("progress.log", "a")
        log_file.write(f'Finished: {repo_count}/{len_repos}\n')
        log_file.close()

        if repo_count % 2000 == 0:
            # files = os.listdir('.')
            # tarballs_count = len([f for f in files if f.endswith('.tar.gz') or f.endswith('.tgz')])
            # with extract_resource_lock:
            in_extraction = True
            time.sleep(150)
            subprocess.run("~/scripts/path_extractor_rust $(find ./ -maxdepth 1 -type d  | grep -v './$' | tr  '\n' ' ') | anew all_path_extractor_rust_output.txt > path_extractor_rust_output.txt", executable='/bin/bash' ,shell=True)
            
            subprocess.run("awk '{print $2}' path_extractor_rust_output.txt | rg --text -e '^.{1,400}$' | anew -q extracted_path_wordlist.txt", executable='/bin/bash' ,shell=True)
            
            subprocess.run("cat <(awk '{for (i=0; i<$1; i++) print $2}' ./path_extractor_rust_output.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./path_extractor_rust_output.txt | unfurl paths) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | sort | uniq -c | sort -nr | grep --text -v null | awk -v min='2' '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt) | grep --text -v -F -i -f  /usr/share/seclists/Discovery/Web-Content/raft-large-extensions-lowercase.txt  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | grep --text -vE '^[0-9/]+$' | anew -q repo_preliminary_wordlist.txt", executable='/bin/bash' ,shell=True)
            
            subprocess.run(f"rm -rf downloads/", shell=True)
            subprocess.run(f"mkdir downloads", shell=True)
            in_extraction = False
    
    # while True:
    #     try:
        # Extract GitHub username from the URL
    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip("/").split("/")
    github_user = path_parts[0]  # "example" in this case
    repo_name = path_parts[1]  # "example" in this case
    # Directory to clone into
    target_dir = os.path.join(os.getcwd(), "downloads", github_user, repo_name.replace(".git",""))
    # Run git clone
    while True:
        if in_extraction:
            time.sleep(10)
            continue
        
        initial_usage = get_disk_usage("./")
        proc = subprocess.Popen(["git", "clone", "--depth=1", repo_url, target_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid)

        try:
            while proc.poll() is None:  # While process is running
                current_usage = get_disk_usage("./")
                if current_usage - initial_usage > 5 * 1024**3:  # More than 5GB
                    print("More than 5GB used. Terminating...")
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    break
                time.sleep(2)  # Check every 2 seconds
        except Exception as e:
            print(f"Monitoring error: {e}")
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        
        stdout, stderr = proc.communicate()

        # log_file = open("progress.log", "a")
        # log_file.write(f"stdout:\n{stdout}\n")
        # log_file.close()
        
        delete_non_html_md_files(target_dir)

        if proc.returncode:
            log_file = open("progress.log", "a")
            log_file.write(f"Error {git_retry_count} with return code {proc.returncode} during git clone: {stderr}\n")
            log_file.close()

            git_retry_count += 1

            if git_retry_count == 3:
                break

            continue
        
        print(f"Repository cloned into: {target_dir}")
        break
            # break
        # except Exception as e:
        #     # print(f"Error {git_retry_count} during git clone:", e)
        #     try:
        #         delete_non_html_md_files(target_dir)
        #     except:
        #         pass

        #     log_file = open("progress.log", "a")
        #     log_file.write(f"Error {git_retry_count} during git clone: {e}\n")
        #     log_file.write(f"Return code: {e.returncode}\n")
        #     log_file.write(f"stdout:\n{e.stdout}\n")
        #     log_file.write(f"stderr:\n{e.stderr}\n")
        #     log_file.close()

        #     if git_retry_count == 3:
                # break
    


grep_app_url = "https://grep.app/api/search"
github_search_code_url = "https://api.github.com/search/code"
github_search_repo_url = "https://api.github.com/search/repositories"

special_keywords = ["swagger", "openapi", "RAML", "api blueprint", "graphql", "grpc", "AsyncAPI", "WSDL", "WADL", "Hydra", "JSON hyper", "Slate", "HAL", "OData", "JSON:API"]

parser = argparse.ArgumentParser(description="Download repos and codes where the strings are specified")
parser.add_argument("-q", "--query-file", required=False, help="file with query strings to be searched for")
parser.add_argument("-sq", "--special-query", required=False, help="file with query strings to be searched for with the special keywords ")
parser.add_argument("-bq", "--banner-query", required=False, help="file with banner strings to be searched for with the special keywords ")
parser.add_argument('-gb', '--github-based', action='store_true', help='search on github')
parser.add_argument('-gab', '--grep-app-based', action='store_true', help='search on grep app')
parser.add_argument("-dr", "--download-repos", required=False, help="file with banner strings to be searched for with the special keywords ")
parser.add_argument("-df", "--download-resources", required=False, help="file with banner strings to be searched for with the special keywords ")
args = parser.parse_args()


grep_app_params_queries = list()
grep_app_params_special_queries = list()
grep_app_params_banner_queries = list()

github_params_queries = list()
github_params_special_queries = list()
github_params_banner_queries = list()
# github_params = list()

if args.query_file:

    with open(args.query_file, 'r') as file:
        queries = list()
        for query in file:
            query = query.strip()
            queries.append(query)


        if args.grep_app_based:
            grep_app_params_queries.extend(prepare_grep_app_params(queries, True, False, False))

        if args.github_based:
            github_params_queries.extend(prepare_github_params(queries), True, False, False)

if args.special_query:
    with open(args.special_query, 'r') as file:
        queries = list()
        for query in file:
            query = query.strip()
            queries.append(query)


        if args.grep_app_based:
            grep_app_params_special_queries.extend(prepare_grep_app_params(queries, False, True, False))

        if args.github_based:
            github_params_special_queries.extend(prepare_github_params(queries, False, True, False))

if args.banner_query:
    with open(args.banner_query, 'r') as file:
        queries = list()
        for query in file:
            query = query.strip()
            queries.append(query)
        
        if args.grep_app_based:
            grep_app_params_banner_queries.extend(prepare_grep_app_params(queries, False, False, True))

        if args.github_based:
            github_params_banner_queries.extend(prepare_github_params(queries, False, False, True))


repos = list()
resources = list()

param_without_special_keyword_total_count = 0

# for param in github_params:

#     log_file = open("logfile.log", "a")
#     log_file.write(f"github querying: {param}\n")
#     log_file.close()

#     if param_without_special_keyword_total_count == 0 and github_params.index(param) % (len(special_keywords) + 1) != 0:
#         log_file = open("logfile.log", "a")
#         log_file.write(f"skipped github querying: {param}\n")
#         log_file.close()
#         continue

#     param_repos, param_resources, total_count = get_repos_and_resources_from_github(param)

#     if github_params.index(param) % (len(special_keywords) + 1) == 0:
#         param_without_special_keyword_total_count = total_count

#     repos.extend(param_repos)
#     resources.extend(param_resources)


wordlists = os.listdir('/home/deus/documents/repo_wordlists/')
wordlists_count = len(wordlists)
queries_and_wordlists = list()
matched_queries_wordlists = list()
for wordlist in wordlists:
    with open(f'/home/deus/documents/repo_wordlists/{wordlist}/query.txt', 'r') as f:
        query_and_wordlist = {"query": f.read().rstrip('\n'), "wordlist": f'/home/deus/documents/repo_wordlists/{wordlist}/wordlist.txt'}
        queries_and_wordlists.append(query_and_wordlist)

banner_repos = dict()
for param in github_params_banner_queries:
    break_tf_out = False
    for qw in queries_and_wordlists:
        if param["q"] == qw["query"]:
            matched_queries_wordlists.append(qw["wordlist"])
            break_tf_out = True
            break
    
    if break_tf_out:
        break

    log_file = open("logfile.log", "a")
    log_file.write(f"github querying: {param}\n")
    log_file.close()

    param_repos, param_resources, total_count = get_repos_and_resources_from_github_with_banner(param)

    # repos.extend(param_repos)
    banner_repos[param["q"]] = param_repos

    resources.extend(param_resources)

# temp comment below!

# with ThreadPoolExecutor(max_workers=3) as executor:
    
#     for grep_app_params_inst in split_list(grep_app_params_queries, (len(special_keywords) * 2) + 1):
#         executor.submit(grep_app_no_skip_handler, grep_app_params_inst)
        

#     for grep_app_params_inst in split_list(grep_app_params_special_queries, (len(special_keywords) * 2) + 1):
#         executor.submit(grep_app_skip_handler, grep_app_params_inst)
    
#     for grep_app_params_inst in split_list(grep_app_params_banner_queries, (len(special_keywords) * 2) + 1):
#         executor.submit(grep_app_no_skip_handler, grep_app_params_inst)


# repos = list(dict.fromkeys(repos))

new_banner_repos = dict()
for query, repos in banner_repos.items():
    unique_repos = list(dict.fromkeys(repos))
    new_banner_repos[query] = unique_repos

banner_repos = new_banner_repos

resources = list(dict.fromkeys(resources))

with open("resources.txt", "a") as file:
    for item in resources:
        file.write(item + "\n")

repos_count = len([
    file for file in os.listdir('./')
    if re.fullmatch(r"repos_\d+\.json", file)
]) + 1

with open(f"repos_{repos_count}.json", "w") as file:
    file.write(json.dumps(banner_repos))

if args.download_repos:
    with open(args.download_repos, "r") as file:
        banner_repos = json.load(file)

# if args.download_repos:
#     with open(args.download_repos, "r") as file:
#         for item in file:
#             item = item.strip()
#             repos.append(item)

if args.download_resources:
    with open(args.download_resources, "r") as file:
        for item in file:
            item = item.strip()
            resources.append(item)


len_resources = len(resources)
resource_count = 0

# len_repos = len(repos)
len_repos = sum(len(v) for v in banner_repos.values())
repo_count = 0


for query, repos in banner_repos.items():

    with ThreadPoolExecutor(max_workers=10) as executor:
        for repo in repos:
            executor.submit(download_repo, repo)

    subprocess.run("~/scripts/path_extractor_rust $(find ./ -maxdepth 1 -type d  | grep -v './$' | tr  '\n' ' ') | anew all_path_extractor_rust_output.txt  > path_extractor_rust_output.txt", executable='/bin/bash' ,shell=True)
    subprocess.run("awk '{print $2}' path_extractor_rust_output.txt | rg --text -e '^.{1,400}$' | anew -q extracted_path_wordlist.txt", executable='/bin/bash' ,shell=True)
    subprocess.run("cat <(awk '{for (i=0; i<$1; i++) print $2}' ./path_extractor_rust_output.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./path_extractor_rust_output.txt | unfurl paths) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | sort | uniq -c | sort -nr | grep --text -v null | awk -v min='2' '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt) | grep --text -v -F -i -f  /usr/share/seclists/Discovery/Web-Content/raft-large-extensions-lowercase.txt  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | grep --text -vE '^[0-9/]+$' | anew -q repo_preliminary_wordlist.txt", executable='/bin/bash' ,shell=True)
    
    subprocess.run(f"rm -rf downloads/", shell=True)
    subprocess.run(f"mkdir downloads", shell=True)
    
    subprocess.run(f"bash /home/deus/scripts/shorten_repo_wordlist.sh", shell=True)

    wordlists_count += 1
    os.makedirs(f'/home/deus/documents/repo_wordlists/wordlist_{wordlists_count}', exist_ok=True)
    with open(f'/home/deus/documents/repo_wordlists/wordlist_{wordlists_count}/query.txt', 'w') as f:
        f.write(query + '\n')
    
    subprocess.run(f"mv repo_preliminary_wordlist.txt /home/deus/documents/repo_wordlists/wordlist_{wordlists_count}/wordlist.txt", shell=True)
    matched_queries_wordlists.append(f'/home/deus/documents/repo_wordlists/wordlist_{wordlists_count}/wordlist.txt')

for wordlist in matched_queries_wordlists:
    subprocess.run(f"cat {wordlist} | anew -q final_repo_wordlist.txt", shell=True)
    
with ThreadPoolExecutor(max_workers=100) as executor:

    for resource_url in resources:
        executor.submit(download_resources, resource_url)

# rota_exit_handler(rota_proc)
