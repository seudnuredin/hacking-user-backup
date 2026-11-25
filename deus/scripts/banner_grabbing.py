import multiprocessing
try:
   multiprocessing.set_start_method('fork', force=True)
   print("forked")
except RuntimeError:
    print("unable to fork!")
    exit()
import json
import subprocess
import argparse
import os
import json
# import time

parser = argparse.ArgumentParser(description="Run banner grabbing on list of (sub)domains from given file with rate limit and/or no proxy")
parser.add_argument("-df", "--domains-file", required=True, help="file containing a list of (sub)domains")
parser.add_argument('-rl', '--rate-limit', type=int, help='Limit number of requests per second (per directory) (default: 1, i.e. 1 r/s)')
parser.add_argument('-np', '--no-proxy', action='store_true', help='don\'t use proxies and instead use the server ip')
args = parser.parse_args()

manager = multiprocessing.Manager()
used_proxychains_proxies_across_processes = manager.list()
used_proxies_across_processes = manager.list()
urls_and_or_suburls_with_their_shared_backends = manager.dict()
counter = multiprocessing.Value('i',1)
proxy_setting_lock = multiprocessing.Lock()
urls_banners_file_lock = multiprocessing.Lock()

web_urls = set()

subprocess.run(f" bash -c \'  httpx -ports 80,443,8080,8443,8000,8888 -l {args.domains_file} -timeout 10 -threads 50 -silent -o urls_with_web_servers_listening_on_common_http_ports \' ", shell=True)
# ,8080,8443,8000,8888
with open('urls_with_web_servers_listening_on_common_http_ports') as file:
    for url in file:
        url = url.strip()
        web_urls.add(url)

web_urls = list(web_urls)
web_urls_len = len(web_urls)
def grab_banner(url):
    global proxychains_proxies
    global proxies
    global used_proxychains_proxies_across_processes
    global used_proxies_across_processes
    global web_urls
    global web_urls_len
    global proxy_setting_lock
    global urls_banners_file_lock
    
    index_of_url = web_urls.index(url)

    url_banner = dict()
    url_banner["url"] = url

    # while True:
    #     try:
    #         proxychains_proxy = list(set(proxychains_proxies) - set(used_proxychains_proxies_across_processes))[0]
    #         used_proxychains_proxies_across_processes.append(proxychains_proxy)
    #         break
    #     except:
    #         time.sleep(2)
    
    with proxy_setting_lock:
        while True:
            try:
                if args.rate_limit == None:
                    proxychains_proxy = list(set(proxychains_proxies) - set(used_proxychains_proxies_across_processes))[0]
                else:
                    for l_proxy in proxychains_proxies:
                        l_proxy_count = used_proxychains_proxies_across_processes.count(l_proxy)

                        if l_proxy_count < args.rate_limit:
                            proxychains_proxy = l_proxy
                
                if proxychains_proxy:
                    used_proxychains_proxies_across_processes.append(proxychains_proxy)
                else:
                     raise ValueError("proxy is empty")
                break
            except ValueError as e:
                log_file = open("banner_grabbing.log", "a")
                log_file.write(f" Error: {e} from {','.join(proxies)}\n")
                log_file.close()
                time.sleep(2)
        
        while True:
            try:
                if args.rate_limit == None:
                    proxy = list(set(proxies) - set(used_proxies_across_processes))[0]
                else:
                    for l_proxy in proxies:
                        l_proxy_count = used_proxies_across_processes.count(l_proxy)

                        if l_proxy_count < args.rate_limit:
                            proxy = l_proxy
                
                if proxy:
                    used_proxies_across_processes.append(proxy)
                else:
                     raise ValueError("proxy is empty")
                break
            except ValueError as e:
                log_file = open("banner_grabbing.log", "a")
                log_file.write(f" Error: {e} from {','.join(proxies)}\n")
                log_file.close()
                time.sleep(2)

    if proxy == "self":
        try:
            url_banner["browser_based_wappalyzer"] = subprocess.run(f' bash -c \' /home/deus/scripts/browser_based_wappalyzer {url} \' ', shell=True, capture_output=True, text=True, timeout=120).stdout.strip()

            if url_banner["browser_based_wappalyzer"]:
                url_banner["browser_based_wappalyzer"] = json.loads(url_banner["browser_based_wappalyzer"])

        except subprocess.TimeoutExpired:
            pass
    else:
        try:
            url_banner["browser_based_wappalyzer"] = subprocess.run(f' bash -c \' /home/deus/scripts/browser_based_wappalyzer {url} {proxy}  \' ', shell=True, capture_output=True, text=True, timeout=120).stdout.strip()
            
            if url_banner["browser_based_wappalyzer"]:
                url_banner["browser_based_wappalyzer"] = json.loads(url_banner["browser_based_wappalyzer"])
        except subprocess.TimeoutExpired:
            pass
    
    if proxy == "self":
        try:
            url_banner["projectdiscovery_wappalyzer"] = subprocess.run(f' bash -c \' /home/deus/scripts/projectdiscovery_wappalyzer -url={url} \' ', shell=True, capture_output=True, text=True, timeout=120).stdout.strip()

            if url_banner["projectdiscovery_wappalyzer"]:
                url_banner["projectdiscovery_wappalyzer"] = json.loads(url_banner["projectdiscovery_wappalyzer"])
        except subprocess.TimeoutExpired:
            pass
    else:
        try:
            url_banner["projectdiscovery_wappalyzer"] = subprocess.run(f' bash -c \' /home/deus/scripts/projectdiscovery_wappalyzer -url={url} -proxy=socks5://{proxy}  \' ', shell=True, capture_output=True, text=True, timeout=120).stdout.strip()
            
            if url_banner["projectdiscovery_wappalyzer"]:
                url_banner["projectdiscovery_wappalyzer"] = json.loads(url_banner["projectdiscovery_wappalyzer"])
        except subprocess.TimeoutExpired:
            pass
    
    if proxychains_proxy == "self":
        try:
            subprocess.run(f' bash -c \' whatweb {url} --log-json=whatweb_{index_of_url}.json \' ', shell=True, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            pass
    else:
        try:
            subprocess.run(f' bash -c \' proxychains4 -f /home/deus/documents/{proxychains_proxy} -q whatweb {url} --log-json=whatweb_{index_of_url}.json  \' ', shell=True, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            pass
    if os.path.exists(f'whatweb_{index_of_url}.json'):
        with open(f'whatweb_{index_of_url}.json', 'r') as file:
            try:
                url_banner["whatweb"] = ""
                url_banner["whatweb"] = json.load(file)
            except:
                pass
    with urls_banners_file_lock:
        with open('urls_banners.json', 'a') as file:
            file.write(json.dumps(url_banner))

    used_proxychains_proxies_across_processes.remove(proxychains_proxy)
    used_proxies_across_processes.remove(proxy)

    log_file = open("logfile.log", "a")
    log_file.write("Finished " + str(counter.value) + "/" + str(web_urls_len) + "\n")
    log_file.close()
    with counter.get_lock():
        counter.value += 1
    
    subprocess.run(f'/bin/bash -c \'rm whatweb_{index_of_url}.json \' ', shell=True)
    


subprocess.run(['bash', '-c','python3 /home/deus/scripts/setup_proxy.py'],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a')
                 )

proxychains_proxies = list()
proxies = list()
if args.no_proxy:
    proxychains_proxies = ["self"]
    proxies = ["self"]
else:
    for f_or_d in os.listdir('/home/deus/documents'):
        if "proxychains" in f_or_d:
            proxychains_proxies.append(f_or_d)
    
    with open('/home/deus/documents/proxies.txt') as proxy_file:
        for proxy in proxy_file:
            proxy = proxy.replace("\n","")
            if proxy != "":
                proxy = proxy.split(':')
                proxies.append(f"isp.smartproxy.com:{proxy[1]}")

if args.rate_limit == None:
    pool = multiprocessing.Pool(min(len(proxychains_proxies),len(proxies)))
else:
    
    # log_file = open("logfile.log", "a")
    # log_file.write(f" {len(proxies) * args.rate_limit} \n")
    # log_file.close()
    pool = multiprocessing.Pool(min(len(proxychains_proxies),len(proxies)) * args.rate_limit)

# pool = multiprocessing.Pool(min(len(proxychains_proxies),len(proxies)))
pool.map(grab_banner, web_urls, chunksize=1)
