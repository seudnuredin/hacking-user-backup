
import argparse
import json
import re
import subprocess

parser = argparse.ArgumentParser(description="Run feroxbuster with specified URL, request file, and methods.")
parser.add_argument("-lsj", "--locate-source-json", required=True, help="The target URL. or file of target URLS")
parser.add_argument("-ih", "--interested-hosts", required=True, help="The target URL. or file of target URLS")
parser.add_argument("-u", "--update", required=False, action='store_true', help="The target URL. or file of target URLS")
args = parser.parse_args()


interested_hosts = set()

with open(args.interested_hosts, 'r') as file:
    for host in file:
        host = host.strip()
        if host.startswith(('http://', 'https://')):
            parsed_host = urlparse(host)
            interested_hosts.add(parsed_host.netloc)
        else:
            interested_hosts.add(host)

hosts = set()
locate_source_json = dict()

with open(args.locate_source_json, 'r') as file:
    locate_source_json = json.load(file)

for key1,items1 in locate_source_json.items():
    for key2,items2 in locate_source_json[key1].items():
        print('items1: ' + str(items1))
        print('items2: ' + str(items2))
        
        for host in interested_hosts:
            if type(items2) is list and host in items2:
                hosts.update(items2)
                hosts.add(key1)
                

# for key1,items1 in locate_source_json.items():
#     for key2,items2 in locate_source_json[key1].items():
#         for host in hosts:
#             if host in items2["domains"]:
#                 hosts.add(host)
#                 hosts.add(key1)


extracted = []

for host in hosts:
    match = re.match(r'^[^.]+\.(.+?)\.', host)
    if match:
        extracted.append(f"{match.group(1)}")

most_common_middle = max(set(extracted), key=extracted.count)
if not args.update:
    subprocess.run(f"cp -r ./../subtarget ./../{most_common_middle}", shell=True, executable='/bin/bash')
else:
    subprocess.run(f"rm ./for_httpx.txt.new", shell=True, executable='/bin/bash')

for host in hosts:
    host = host.strip()
    # file.write(f"{host}\n")
    if not args.update:
        subprocess.run(f'cat rate_limit_config_all.jsonl | grep -F ://{host}" |  anew -q ./../{most_common_middle}/rate_limit_config_all.jsonl', shell=True, executable='/bin/bash')
    
        subprocess.run(f"echo {host} | anew -q ./../{most_common_middle}/all_subtarget_domains.txt", shell=True, executable='/bin/bash')
        subprocess.run(f"echo {host} | grep -Fx -f ./for_httpx.txt | anew -q ./../{most_common_middle}/for_httpx.txt", shell=True, executable='/bin/bash')
    else:
        subprocess.run(f'cat ./../all/rate_limit_config_all.jsonl | grep -F ://{host}" |  anew -q ./rate_limit_config_all.jsonl', shell=True, executable='/bin/bash')
    
        subprocess.run(f"echo {host} | anew -q ./all_subtarget_domains.txt", shell=True, executable='/bin/bash')
        subprocess.run(f"echo {host} | anew -q ./for_httpx.txt >> ./for_httpx.txt.new", shell=True, executable='/bin/bash')

