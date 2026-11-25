import os
import json
import ipaddress
import dns.resolver
import urllib3
import re
import time
import subprocess
import socket
from contextlib import closing
import random


whoisxmlapi_keys = ["at_mHadrRRnMDIbAYlXqhEoOMjrq9J9U"]
http = urllib3.PoolManager()
import requests


# Function to update cookies and resend request
def send_request(payload):

    # Define the initial endpoint and payload
    url = "https://reverse-ip.whoisxmlapi.com/api/web"

    # Define the headers
    headers = {
        "Cookie": "XSRF-TOKEN=eyJpdiI6InFIaGUwbTB3Y2RlMWM2N0NjelwvbUV3PT0iLCJ2YWx1ZSI6IjhBUWVcL1JVdm1FRnUrYXk2VzU1b0g3ck5XcXdYeEdZc0duSzE1QWZLRTRwS0VhXC83ZldMbzZURjJrOE04ZlgydSIsIm1hYyI6IjljNzRiZWIwZWIxNDlkNmQ2ODZhNWM2MjNjZWJiYWJhMjIwZWU1Yzc4YmM2NzZjYjNiZDA5NTliNWQzYTgwNDkifQ%3D%3D; emailverification_session=eyJpdiI6Im1yd3R6V1hMSGF0Z20yWWMxOTh5dFE9PSIsInZhbHVlIjoiaDVlRHlaSCsxRVdkRzNJUUpNelQzMHFycjUxXC95V09Fd0xzYUdXQ1ZDXC85Z1FZS3RtTHpTcklneHEyWlcyRFJ0UUR6TllWNjRKS3Y2QVZRdEZ6VVdodnV6Z0JvNE15WHZaRWVXOVwvallxMThSXC9Ld0dzV3JkblJNazhIcDFWUjZzIiwibWFjIjoiYzk3YTc3MWIyNzY4NjI2OTUyYzlkYjA2MGUyZmY0Y2JmZDM3MTEyYzJlOTQ0NjkyNGJlM2Q5NDdmOWM4ZGY1YiJ9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://reverse-ip.whoisxmlapi.com/",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
        "Origin": "https://reverse-ip.whoisxmlapi.com",
        "X-Csrf-Token": "Ku585IJ7G2vL1VqRuxcOrXukNscQule59nA5A8ci",
        "Sec-Gpc": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=0",
        "Te": "trailers"
    }

    # Initialize a session
    session = requests.Session()
    error_count = 0
    while True:
        try:
            # Send the initial request
            response = session.post(url, json=payload, headers=headers)

            # Check if 'Set-Cookie' header is in the response headers
            if response.status_code == 419:
                if 'Set-Cookie' in response.headers:
                    # Update cookies from the Set-Cookie header
                    session.cookies.update(response.cookies)
                    print(response.cookies)
                    # Extract the updated XSRF-TOKEN and emailverification_session from cookies
                    xsrf_token = session.cookies.get("XSRF-TOKEN")
                    emailverification_session = session.cookies.get("emailverification_session")

                    # Add the CSRF token to headers
                    # headers["X-Csrf-Token"] = xsrf_token

                    # Prepare the cookies dictionary for the request
                    cookies = {
                        "XSRF-TOKEN": xsrf_token,
                        "emailverification_session": emailverification_session
                    }
                    # print(headers)
                    # print(cookies)

                    # Resend the request with updated cookies
                    response = session.post(url, json=payload, headers=headers, cookies=cookies)

            return response
        except Exception as e:
            error_count += 1
            if error_count == 3:
                break
            # Print the exception
            print(f"An error occurred: {e}")
    
    return None

def is_port_open(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(5)
        if sock.connect_ex((host, port)) == 0:
            return True
        else:
            return False

def deduct_ips():
    ips_to_be_ignored = set()
    with open("ips_to_be_ignored") as ips_to_be_ignored_file:
        for ip_to_be_ignored in ips_to_be_ignored_file:
            ip_to_be_ignored = ip_to_be_ignored.replace("\n","")
            ips_to_be_ignored.add(ip_to_be_ignored)
    
    asn_and_its_ips = json.load(open('asn_and_its_ips_to_be_used.json'))
    for key in asn_and_its_ips.keys():
        # ips = asn_and_its_ips[key]
        # for ip in ips:
        #     if not (is_port_open(ip, 80) or is_port_open(ip, 443)):
        #         asn_and_its_ips[key].remove(ip)
        
        for ip in ips_to_be_ignored:
            if ip in asn_and_its_ips[key]:
                asn_and_its_ips[key].remove(ip)
    
    with open('asn_and_its_ips_to_be_used.json','w') as file:
        file.write(json.dumps(asn_and_its_ips))

def exit_after_proper_save(file_name, is_exit):

    deduct_ips()

    assets = set()
    with open(file_name) as file:
        for asset in file:
            assets.add(asset.replace("\n",""))
    with open(file_name,'w') as file:
        for asset in assets:
            file.write(asset + "\n")
    if is_exit:
        exit()

def ip_based_reverse_dns_lookup():
    # global payload
    # it should take data from target_ip_list_manager
    def recursively_fetcher(ip, offset):
        for api_key in whoisxmlapi_keys:
            if offset == 0:
                parameters = f'?apiKey={api_key}&ip={ip}'
            else:
                parameters = f'?apiKey={api_key}&ip={ip}&from={offset}'
            domains_res = http.request('GET','https://dns-history.whoisxmlapi.com/api/v1' + parameters)

            if domains_res.status == 200:
                res_body = json.loads(domains_res.data.decode('utf-8'))
                IP_based_reverse_dns_output = open("IP_based_reverse_dns_output", "a")
                for domain in res_body["result"]:
                    # try:
                    #     dns.resolver.resolve(domain["name"], 'A')
                    # except:
                    #     continue
                    IP_based_reverse_dns_output.write(domain["name"] + "\n")
                    IP_based_reverse_dns_output.flush()
                IP_based_reverse_dns_output.close()

                if res_body["size"] != 0:
                    recursively_fetcher(ip, res_body["result"][-1]["name"])

                ips_to_be_ignored = open("ips_to_be_ignored", "a")
                ips_to_be_ignored.write(ip + "\n")
                ips_to_be_ignored.close()

                break
            elif domains_res.status == 403:
                if api_key == whoisxmlapi_keys[-1]:
                    print("all api keys have run out of DRS credits! exiting...")
                    exit_after_proper_save('IP_based_reverse_dns_output', True)
                continue
            else:
                print("ERROR with status code that isn't 403")
                exit_after_proper_save('IP_based_reverse_dns_output', True)

    # for ip in ["198.21.19.135"]:

    asn_and_its_ips = json.load(open('asn_and_its_ips_to_be_used.json'))
    for ips in asn_and_its_ips.values():
        # print(ips)
        for ip in ips:
            # random_sleep_duration = random.uniform(5, 10)
            time.sleep(random.uniform(15, 20))
            payload = {
                "search": str(ip),
                "web-lookup-search": True,
                "g-recaptcha-response": None
            }
            res_body = dict()
            error_count = 0
            while True:

                try:
                    response = send_request(payload)
                    res_body = response.json()
                    if "code" in res_body.keys() and 500 == res_body["code"]:
                        raise ValueError(str(res_body))
                    
                    break
                except Exception as e:
                    
                    print(f"An error occurred: {e}")
                    
                    time.sleep(30)
                    error_count += 1
                    if error_count == 2:
                        break
            
            if "size" in res_body.keys() and 300 == res_body["size"]:
                recursively_fetcher(ip, 0)
            elif "size" in res_body.keys() and 300 > res_body["size"] and 0 < res_body["size"]:
                with open("IP_based_reverse_dns_output", "a") as IP_based_reverse_dns_output:
                    for domain in res_body["result"]:
                        IP_based_reverse_dns_output.write(domain["name"] + "\n")

                ips_to_be_ignored = open("ips_to_be_ignored", "a")
                ips_to_be_ignored.write(ip + "\n")
                ips_to_be_ignored.close()
            else:

                logfile = open("logfile.log", "a")
                logfile.write(f"{ip} ip failed with {res_body} body \n")
                logfile.close()

                ips_to_be_ignored = open("ips_to_be_ignored", "a")
                ips_to_be_ignored.write(ip + "\n")
                ips_to_be_ignored.close()
    
    exit_after_proper_save('IP_based_reverse_dns_output', False)


ip_based_reverse_dns_lookup()