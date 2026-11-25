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
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal
from urllib3.exceptions import InsecureRequestWarning
from ipwhois import IPWhois
from ipwhois.exceptions import IPDefinedError
import socket
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import shlex
import math

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument('-rl', '--rate-limit', required=True, type=int, help='upper bound rate limit')
parser.add_argument('-mr', '--min-rate', required=True, type=int, help='lower bound rate limit')
parser.add_argument('-np', '--no-proxy', action='store_true', help='don\'t use proxies and instead use the server ip')
parser.add_argument('-H', '--header', required=False, help='a header to add all requests like -H "X-Hackerone: seudxs"')
parser.add_argument("-uf", "--urls-file", required=True, help="urls of file we need to find their rate limit")
args = parser.parse_args()


def is_port_available(port, host='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


# Custom HTTPAdapter that retries on any exception
class RetryOnAnyExceptionAdapter(HTTPAdapter):
    def __init__(self, max_retries=5, backoff_factor=1, retry_statuses=None):
        self.max_retries_count = max_retries
        self.backoff_factor = backoff_factor
        self.retry_statuses = retry_statuses or {502}
        super().__init__()

    def send(self, request, **kwargs):
        retries = 0
        while retries <= self.max_retries_count:
            try:
                response = super().send(request, **kwargs)
                if response.status_code in self.retry_statuses:
                    raise requests.exceptions.RetryError(f"Retryable HTTP status: {response.status_code}")
                return response
            except Exception as e:
                retries += 1
                if retries > self.max_retries_count:
                    raise
                wait_time = self.backoff_factor * (2 ** (retries - 1))
                print(f"[Retry {retries}] Exception or status error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

# Create adapter with the retry strategy
adapter = RetryOnAnyExceptionAdapter(max_retries=5, backoff_factor=1, retry_statuses={502})

# Create a session and mount the adapter
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)
session.verify = False
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
})


user_agent_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}

# def response_has_cookies(url, proxy, retries = 0):
#     try:
#         proxies = {
#             "http": proxy,
#             "https": proxy
#         }
    
#         headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
#         }

#         for scheme in ['https', 'http']:
#             try:
#                 response = requests.get(f'{scheme}://{url}', proxies=proxies, headers=headers, timeout=30, verify=False)
#             except requests.exceptions.SSLError:
#                 pass
            
#             if bool(response.cookies):
#                 return bool(response.cookies)
        
#         # print(response.cookies)
#         # exit()
#         return False
#     except Exception as e:
#         print(f"Request failed (attempt {retries + 1}): {e}")
#         if retries < 2:
#             return response_has_cookies(url, proxy, retries + 1)
        
#         return False

def response_has_cookies(url, proxy, retries = 0):
    try:
        proxies = {
            "http": proxy,
            "https": proxy
        }
    
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }

        response = requests.get(url, proxies=proxies, headers=headers, timeout=30, verify=False)
        return bool(response.cookies)
    except requests.RequestException as e:
        print(f"Request failed (attempt {retries + 1}): {e}")
        if retries < 2:
            return response_has_cookies(url, proxy, retries + 1)
        return False


user_agents = set()


base_path = '/home/deus/documents'
for f_or_d in os.listdir(base_path):
    if "user_agent" in f_or_d:
        user_agents.add(os.path.join(base_path, f_or_d))

def get_proxy_port(url, rate_limit, proxy):

    available_port = ""
    available_user_agent = ""

    log_file = open("logfile.log", "a")
    log_file.write("get_proxy_port: here 0\n")
    log_file.close()

    ports = list(range(8000, 15000))
    random.shuffle(ports)

    for port in ports:
        if is_port_available(port):
            available_port = port
            break
    
    log_file = open("logfile.log", "a")
    log_file.write("get_proxy_port: here 1\n")
    log_file.close()

    mimick_users = response_has_cookies(url, proxy)

    if mimick_users:

        domain_arg = f"--domain {url}"



        # if rate_limit < 190:
        #     rate_limit += 5
        
        user_count_arg = f"-u {rate_limit}"


        # for user_agent in user_agents:
            # if user_agent not in used_user_agents:
            #     used_user_agents.add(user_agent)
        user_agent_arg = f"-g {random.choice(list(user_agents))}"
        

        is_cookie_used = True

    else:
        is_cookie_used = False
        domain_arg = ""
        user_count_arg = ""
        user_agent_arg = ""
    
    log_file = open("logfile.log", "a")
    log_file.write("get_proxy_port: here 2\n")
    log_file.close()

    proxy_arg = f"-x http://{proxy}"

    with open("logfile.log", "a") as f:
        rota_proc = subprocess.Popen(
            ["rota", "--config", "/home/deus/documents/rota_config.yml",*shlex.split(domain_arg),*shlex.split(user_count_arg),*shlex.split(user_agent_arg),*shlex.split(proxy_arg), "-p", f"{available_port}"],
            stdout=f,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )


    log_file = open("logfile.log", "a")
    log_file.write("get_proxy_port: here 3\n")
    log_file.close()

    if user_count_arg:
        user_count_arg_time = int(user_count_arg.split(" ")[1]) * 5
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
                    ["rota", "--config", "/home/deus/documents/rota_config.yml",*shlex.split(domain_arg),*shlex.split(user_count_arg),*shlex.split(user_agent_arg),*shlex.split(proxy_arg), "-p", f"{available_port}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )


                while is_port_available(available_port):
                    time.sleep(5)
                
                is_cookie_used = False
                
                break

    log_file = open("logfile.log", "a")
    log_file.write("get_proxy_port: here 4\n")
    log_file.close()

    return available_port, rota_proc, is_cookie_used

def send_request(url, req_proxies, delay, rate, wordlist_gen):
    try:
        # if delay != 0:
        #     time.sleep(delay)
        
        # response = requests.get(f'{url}/suppposssetoberandoommfdosfdsf', proxies=req_proxies, headers=user_agent_header, timeout=30, verify=False)

        cmd = ["ffuf"]
        cmd.append("-u")
        cmd.append(url + "/FUZZ")
        cmd.extend("-timeout 10 -mc all -s -json -noninteractive".split(" "))
        cmd.append("-rate")
        cmd.append(str(rate))
        cmd.append("-t")
        cmd.append(str(rate))
        cmd.append("-x")
        cmd.append(req_proxies["http"])
        cmd.append("-w")

        port = urlparse(req_proxies["http"]).port

        with open(f"wordlist_with_port_{port}.txt", "w") as f:
            for i in range(0, wordlist_gen):
                f.write(f"suppposssetoberandoommfdosfdsf{i}\n")

        cmd.append(f"wordlist_with_port_{port}.txt")


        cmd.append("-X")
        cmd.append("GET")
        
        if delay != 0:
            cmd.append("-p")
            cmd.append(str(delay))

        cmd.extend(["-H",f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"])
        cmd = [x for x in cmd if x]
        cmd = list(map(str, cmd))


        with open(f"ffuf_output_with_port_{port}.jsonl", "w") as output_file:
            result = subprocess.run(cmd, preexec_fn=os.setsid, stdout=output_file)
        
        status_codes = []
        
        with open(f"ffuf_output_with_port_{port}.jsonl") as f:
            for line in f:
                data = json.loads(line)
                status_codes.append(data.get('status'))

        # os.remove(f"ffuf_output_with_port_{port}.jsonl")
        # os.remove(f"wordlist_with_port_{port}.txt")

        return status_codes
        # return response.status_code
    except Exception as e:
        print(f"Error: {e}")

def save_rate_details(url, rate, delay, is_cookie_used):
    config = {
    "url": url,
    "rate": rate,
    "delay": delay,
    "is_cookie_used": is_cookie_used
    }

    with open(f"rate_limit_config_min_{args.min_rate}.jsonl", "a") as file:
        file.write(f"{json.dumps(config)}\n")


def rota_exit_handler(rota_proc):
    os.killpg(os.getpgid(rota_proc.pid), signal.SIGKILL)

    try:
        rota_proc.wait(timeout=5)
    except Exception:
        pass

def subtract_until_smallest(numbers, start_number):
    if not numbers:
        return start_number
    
    min_in_list = min(numbers)
    result = start_number

    while result >= min_in_list:
        result -= 1

    return result

def test_url_rate(url):
    global args
    global used_proxies_across_processes
    global proxies
    global proxy_setting_lock
    global session

    with proxy_setting_lock:
        counter1 = Counter(proxies)
        counter2 = Counter(used_proxies_across_processes)
        result_counter = counter1 - counter2
        result = list(result_counter.elements())
        proxy = result[0]

        used_proxies_across_processes.append(proxy)
    
    log_file = open("logfile.log", "a")
    log_file.write(f"entered url: {url}\n")
    log_file.close()

    log_file = open("logfile.log", "a")
    log_file.write("here 1\n")
    log_file.close()
    
    if url.endswith('/'):
        url = url[:-1]

    req_proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}',
    }

    try:
        res = requests.get(f'{url}/suppposssetoberandoommfdosfdsf', proxies=req_proxies, headers=user_agent_header, timeout=30, verify=False)
    except Exception as e:
        print(f"Failed to get status code: {e}")
        with proxy_setting_lock:
            used_proxies_across_processes.remove(proxy)
        
        return

    status_code_for_random_path = res.status_code

    log_file = open("logfile.log", "a")
    log_file.write("here 2\n")
    log_file.close()

    # hostname = urlparse(url).hostname
    rate = args.min_rate
    previous_rate = 0
    rate_increment = args.min_rate
    tripped_rate_limit = False
    cooloff_time = 300

    log_file = open("logfile.log", "a")
    log_file.write("here 3\n")
    log_file.close()

    allowed_rates = set()
    disallowed_rates = set()

    # for rate in range(1, args.rate_limit + 1):
    saved_config = False
    delay = 0
    first_time = True
    while rate < args.rate_limit:
        first_time = False

        log_file = open("logfile.log", "a")
        log_file.write("here 4\n")
        log_file.close()

        while tripped_rate_limit:
            log_file = open("logfile.log", "a")
            log_file.write("here 5\n")
            log_file.close()

            # req_proxies = {
            #     'http': proxy,
            #     'https': proxy,
            # }

            req_proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}',
            }

            time.sleep(cooloff_time)

            try:
                res = requests.get(f'{url}/suppposssetoberandoommfdosfdsf', proxies=req_proxies, headers=user_agent_header, timeout=30, verify=False)
            except Exception as e:
                print(f"Failed to get status code after tripping rate limit: {e}")


            if res.status_code != status_code_for_random_path:
                cooloff_time += 60

                log_file = open("logfile.log", "a")
                log_file.write("here 6\n")
                log_file.close()

                continue
            else:
                break

        log_file = open("logfile.log", "a")
        log_file.write("here 7\n")
        log_file.close()

        if not args.no_proxy:
            log_file = open("logfile.log", "a")
            log_file.write(f"url: {url}\n")
            log_file.write(f"rate: {rate}\n")
            log_file.write(f"proxy: {proxy}\n")
            log_file.close()

            port, rota_proc, is_cookie_used = get_proxy_port(url, rate, proxy)

            req_proxies = {
                'http': f'http://127.0.0.1:{port}',
                'https': f'http://127.0.0.1:{port}',
            }

            log_file = open("logfile.log", "a")
            log_file.write("here 8\n")
            log_file.close()

        else:
            req_proxies = None

        # with ThreadPoolExecutor(max_workers=rate) as executor:

        log_file = open("logfile.log", "a")
        log_file.write("here 9\n")
        log_file.close()

        futures = list()

        # for i in range(max(20 * rate, 50)):
        #     futures.append(executor.submit(send_request, url, req_proxies, delay))

        wordlist_gen = max(25 * rate, 50)
        
        status_codes = send_request(url, req_proxies, delay, rate, wordlist_gen)

        if not status_codes:
            status_codes = list()

        log_file = open("logfile.log", "a")
        log_file.write("here 99\n")
        log_file.close()

        break_tf_out = False
        continue_tf_out = False
        for status_code in status_codes:
            # status_code = future.result()
            if status_code != status_code_for_random_path and status_code >= 400 and status_code != 404:

                if args.min_rate >= rate:
                    break_tf_out = True
                    break

                # disallowed_rates.add(rate)

                # tripped_rate_limit = True

                # if rate == 1:
                #     delay += 1
                # else:
                #     if rate_increment == 1 and not saved_config:
                #         save_rate_details(url, previous_rate, delay, is_cookie_used)
                #         saved_config = True

                #         if not args.no_proxy:
                #             rota_exit_handler(rota_proc)
                        
                #         break_tf_out = True
                #         break
                #     else:
                #         rate_increment = math.ceil(rate_increment / 2)
                #         rate = previous_rate + rate_increment
                        
                # continue_tf_out = True
                # break


                save_rate_details(url, previous_rate, delay, is_cookie_used)
                saved_config = True
                
                break_tf_out = True
                break
        
        if break_tf_out:
            if not args.no_proxy:
                rota_exit_handler(rota_proc)

            break
        
        if continue_tf_out:
            continue

        log_file = open("logfile.log", "a")
        log_file.write("here 100\n")
        log_file.close()

        if not args.no_proxy:
            rota_exit_handler(rota_proc)
        
        if ((delay != 0 and rate_increment == 1) or (rate_increment == 1 and args.min_rate == 1 and not first_time)) and not saved_config:
            saved_config = True
            save_rate_details(url, rate, delay, is_cookie_used)
            break
        
        if rate_increment != args.min_rate:
            rate_increment = math.ceil(rate_increment / 2)

        log_file = open("logfile.log", "a")
        log_file.write("here 10\n")
        log_file.close()

        previous_rate = rate


        rate += rate_increment

        rate = subtract_until_smallest(disallowed_rates, rate)

        if any(rate <= x for x in allowed_rates):
            saved_config = True
            save_rate_details(url, rate, delay, is_cookie_used)
            break


        allowed_rates.add(previous_rate)

        tripped_rate_limit = False

        log_file = open("logfile.log", "a")
        log_file.write("here 11\n")
        log_file.close()

    log_file = open("logfile.log", "a")
    log_file.write("here 12\n")
    log_file.close()

    if args.min_rate < rate and not saved_config:
        saved_config = True
        save_rate_details(url, rate, delay, is_cookie_used)

    with proxy_setting_lock:
        used_proxies_across_processes.remove(proxy)
    
    

manager = multiprocessing.Manager()
used_proxies_across_processes = manager.list()
proxy_setting_lock = multiprocessing.Lock()

urls = list()

with open(args.urls_file) as urls_file:
    for url in urls_file:
        url = url.strip()
        
        urls.append(url)

proxies = list()
if args.no_proxy:
    proxies.append("self")
else:
    with open('/home/deus/documents/proxies.txt') as proxy_file:
        for proxy in proxy_file:
            proxy = proxy.strip()
            if proxy != "":
                proxy = proxy.split(':')
                # proxies.append(f"isp.decodo.com:{proxy[1]}")
                proxies.append(f"{proxy[0]}:{proxy[1]}")


random.shuffle(proxies)
pool = multiprocessing.Pool(len(proxies))
pool.map(test_url_rate, urls, chunksize=1)

