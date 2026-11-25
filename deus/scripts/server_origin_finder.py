import sys
import requests
import json
import subprocess
from urllib.parse import urlparse
import os
import re

hostnames_we_should_dns_history_for = set()
keyword_we_should_perform_reverse_ssl_grabbing_on = ""

# if "all" == sys.argv[1]:
#     with open('./../collected_domains.txt') as file:
#         for hostname in file:
#             hostname = hostname.replace("\n","")
#             hostnames_we_should_dns_history_for.add(hostname)

if "*" in sys.argv[1]:
    sys.argv[1] = sys.argv[1].replace("*","")
    with open('./../collected_domains.txt') as file:
        for hostname in file:
            hostname = hostname.replace("\n","")
            if sys.argv[1] in hostname:
                hostnames_we_should_dns_history_for.add(hostname)
    
    keyword_we_should_perform_reverse_ssl_grabbing_on = sys.argv[1].split('.')[-2]
else:
    hostnames_we_should_dns_history_for.add(sys.argv[1])
    keyword_we_should_perform_reverse_ssl_grabbing_on = sys.argv[1].split('.')[-2]

dns_history_ips = set()
url_we_want_origin_ip_of = sys.argv[2]

def add_entry(ip, hostname):
    hosts_file = "/etc/hosts"
    entry = f"{ip} {hostname}\n"

    with open(hosts_file, "r") as file:
        if entry.strip() in [line.strip() for line in file.readlines()]:
            return

    with open(hosts_file, "a") as file:
        file.write(entry)

def remove_entry(ip, hostname):
    hosts_file = "/etc/hosts"
    entry = f"{ip} {hostname}"

    with open(hosts_file, "r") as file:
        lines = file.readlines()

    updated_lines = [line for line in lines if line.strip() != entry]

    with open(hosts_file, "w") as file:
        file.writelines(updated_lines)

def get_dns_history(hostname, page):

    url = f"https://api.securitytrails.com/v1/history/{hostname}/dns/a?page={page}"

    headers = {
        "accept": "application/json",
        "APIKEY": "m1MgQiaofHIJJT4pYUyEYvKb62JuDmiy"
    }

    response = requests.get(url, headers=headers)
    dns_history = json.loads(response.text)
    try:
        for record in dns_history["records"]:
            for value in record["values"]:
                dns_history_ips.add(value["ip"])
    except:
        print(response.text)
        # exit()
    
    if dns_history["pages"] != page:
        get_dns_history(hostname, page + 1)

for hostname in hostnames_we_should_dns_history_for:
    get_dns_history(hostname, 1)

dns_history_ips = list(dns_history_ips)

# dns_history_ips = ['82.97.136.109', '82.97.136.82', '62.116.130.8', '82.97.136.83', '82.97.160.83', '82.97.160.82', '82.97.160.11', '82.97.136.195']

hostname_we_want_origin_ip_of = urlparse(url_we_want_origin_ip_of).hostname
for ip in list(dns_history_ips):
    
    error_count = 0
    url_we_want_origin_ip_of_for_this_instance = f'http://{hostname_we_want_origin_ip_of}'

    server_error_status_code_pattern = r'is\s*["\']5\d{2}["\']'

    while True:
        add_entry(ip, hostname_we_want_origin_ip_of)

        command = f"wafw00f {url_we_want_origin_ip_of_for_this_instance}"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        remove_entry(ip, hostname_we_want_origin_ip_of)

        output = result.stdout.strip()
        error = result.stderr.strip()
        
        if error != "":
            error_count += 1

            if error_count % 2 == 0:
                url_we_want_origin_ip_of_for_this_instance = f'http://{hostname_we_want_origin_ip_of}'
            else:
                url_we_want_origin_ip_of_for_this_instance = f'https://{hostname_we_want_origin_ip_of}'


            if error_count == 3:
                break
            continue
        
        if "no waf" not in output.lower() and not re.search(server_error_status_code_pattern, output.lower()):
            dns_history_ips.remove(ip)
        
        break

# print(dns_history_ips)

with open(f'/tmp/dns_history_ips.txt','w') as dns_history_ips_file:
    for ip in dns_history_ips:
        dns_history_ips_file.write(f"{ip}\n")

previous_output_count = 0

for f_or_d in os.listdir('./'):
    if "server_origin_finder_output_" in f_or_d:
        previous_output_count += 1

previous_output_count += 1

error_count = 0
while True:
    command = f"cat /tmp/dns_history_ips.txt | hakoriginfinder -h {url_we_want_origin_ip_of} > server_origin_finder_output_{previous_output_count}.txt"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout.strip()
    error = result.stderr.strip()
    
    if error != "" or "Error" in output:
        print(error)
        error_count += 1
        if error_count == 3:
            break
        continue
    
    break

os.remove('/tmp/dns_history_ips.txt')

# print(dns_history_ips)
