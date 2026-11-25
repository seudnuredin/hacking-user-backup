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
from urllib.parse import urlparse
from collections import Counter
import os

def check_url(url):
    global proxy_setting_lock
    global used_proxies_across_processes
    global proxies

    # proxy = ""
    with proxy_setting_lock:
        # proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
        counter1 = Counter(proxies)
        counter2 = Counter(used_proxies_across_processes)
        result_counter = counter1 - counter2
        result = list(result_counter.elements())
        proxy = result[0]

        used_proxies_across_processes.append(proxy)
    
    # Set proxy
    proxies_for_request = {
        'http': f'socks5h://{proxy}',
        'https': f'socks5h://{proxy}'
    } if proxy != "self" else None

    """Check if the URL returns a 200 status code."""
    working_url = False
    try:
        response = requests.get(url, timeout=10, proxies=proxies_for_request, verify=False)

        if response.status_code == 200:
            working_url = True
        elif 300 <= response.status_code < 400:
            redirect_url = response.headers.get('Location')
            if url in redirect_url:
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

parser = argparse.ArgumentParser(description="Run feroxbuster with specified URL, request file, and methods.")
parser.add_argument("-ul", "--url-list", required=True, help="file of target page URLS")
parser.add_argument('-rl', '--rate-limit', type=int, help='Limit number of katana to instantiate')
parser.add_argument('-krl', '--katana-rate-limit', type=int, help='Limit number of requests per second for katana')
parser.add_argument('-np', '--no-proxy', action='store_true', help='don\'t use proxies and instead use the server ip')
parser.add_argument('-d', '--delay', type=int, required=False, help='delay between requests')
parser.add_argument('-H', '--headers', required=False, help='file that has headers to include in katana requests to the target')
args = parser.parse_args()

urls = list()
# urls = []
manager = multiprocessing.Manager()
used_proxies_across_processes = manager.list()
proxy_setting_lock = multiprocessing.Lock()

# with open(args.url_list, 'r') as page_urls_file:
#     for page_url in page_urls_file:
#         page_url = page_url.strip()
#         if page_url not in urls:
#             urls.append(page_url)
        
#         parsed_page_url_netloc = urlparse(page_url).scheme + '://' + urlparse(page_url).netloc.split(":")[0]
#         if parsed_page_url_netloc not in urls:
#             urls.append(parsed_page_url_netloc)


if args.url_list:
    with open(args.url_list, 'r') as page_urls_file:
        for page_url in page_urls_file:
            page_url = page_url.strip()
            urls.append(page_url)

proxies = []
if args.no_proxy:
    proxies.append("self")
else:
    if not args.rate_limit:
        with open('/home/deus/documents/proxies.txt') as proxy_file:
            for proxy in proxy_file:
                proxy = proxy.strip()
                if proxy != "":
                    proxy = proxy.split(':')
                    proxies.append(f"isp.smartproxy.com:{proxy[1]}")
    else:
        available_proxies = list()
        with open('/home/deus/documents/proxies.txt') as proxy_file:
            for proxy in proxy_file:
                proxy = proxy.strip()
                if proxy != "":
                    proxy = proxy.split(':')
                    available_proxies.append(f"isp.smartproxy.com:{proxy[1]}")
        
        available_proxies_len = len(available_proxies)
        
        for i in range(0, args.rate_limit):
            proxies.append(available_proxies[i % available_proxies_len])

# set up working urls
# urls = list(set(process_urls(urls)))
urls = list(set(process_urls(urls)))

def scrape_first_couple_pages(url):
    global proxy_setting_lock
    global used_proxies_across_processes
    global proxies
    global urls
    global args

    with proxy_setting_lock:
        # proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
        counter1 = Counter(proxies)
        counter2 = Counter(used_proxies_across_processes)
        result_counter = counter1 - counter2
        result = list(result_counter.elements())
        proxy = result[0]
        
        used_proxies_across_processes.append(proxy)
    
    katana_rate_limit = 1
    if args.katana_rate_limit:
        katana_rate_limit = args.katana_rate_limit

    katana_headers = ""
    if args.headers:
        katana_headers = f"-H {args.headers}"

    if proxy != "self":
        proxy_for_katana = f"-proxy http://{proxy}"
    else:
        proxy_for_katana = ""

    subprocess.run(f"katana -u {url} {proxy_for_katana} -sc -ns -c 1 -p 1 -rl {katana_rate_limit} {katana_headers} -rd 0 -d 2 -strategy breadth-first -silent -sr -srd ./{urlparse(url).netloc}_main_{urls.index(url)}_traffic", shell=True, preexec_fn=os.setsid , stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    with proxy_setting_lock:
        used_proxies_across_processes.remove(proxy)


pool = multiprocessing.Pool(len(proxies))
pool.map(scrape_first_couple_pages, urls, chunksize=1)


# later for utilizing this script in other scripts like sqli. cat ./katana_google.com.json | jq '.response | .forms' and cat ./katana_google.com.json | jq '.request'