import os
import json
import ipaddress
import dns.resolver
import urllib3
import re
import time
import subprocess

whoisxmlapi_keys = ["<auth_key>"]
http = urllib3.PoolManager()

def deduct_whois_chunks():
    whois_chunks_to_be_used = set()
    whois_chunks_to_be_ignored = set()

    with open("registrant_info_to_be_used") as whois_chunks_to_be_used_file:
        for whois_chunk_to_be_used in whois_chunks_to_be_used_file:
            whois_chunk_to_be_used = whois_chunk_to_be_used.replace("\n","")
            whois_chunks_to_be_used.add(whois_chunk_to_be_used)
    
    with open("registrant_info_to_be_ignored") as whois_chunks_to_be_ignored_file:
        for whois_chunk_to_be_ignored in whois_chunks_to_be_ignored_file:
            whois_chunk_to_be_ignored = whois_chunk_to_be_ignored.replace("\n","")
            whois_chunks_to_be_ignored.add(whois_chunk_to_be_ignored)

    with open("registrant_info_to_be_used","w") as whois_chunks_to_be_used_file:
        for whois_chunk_to_be_used_updated in list(whois_chunks_to_be_used - whois_chunks_to_be_ignored):
            whois_chunks_to_be_used_file.write(whois_chunk_to_be_used_updated + "\n")

def exit_after_proper_save(file_name, is_exit):
    deduct_whois_chunks()
    
    assets = set()
    with open(file_name) as file:
        for asset in file:
            assets.add(asset.replace("\n",""))
    with open(file_name,'w') as file:
        for asset in assets:
            file.write(asset + "\n")
    if is_exit:
        exit()

def reverse_whois():
    #it should take data from target_personal_whois_info_manager
    def recursively_fetcher(whois_chunk, next_page_search_after):
        for api_key in whoisxmlapi_keys:
            if next_page_search_after == 0:
                body = {"searchType": "current","mode": "purchase","punycode": True,"basicSearchTerms": {"include": [whois_chunk]}}
            else:
                body = {"searchAfter":next_page_search_after,"searchType": "current","mode": "purchase","punycode": True,"basicSearchTerms": {"include": [whois_chunk]}}
            domains_res = http.request('POST','https://reverse-whois.whoisxmlapi.com/api/v2', headers = {"X-Authentication-Token": api_key}, body = json.dumps(body))

            if domains_res.status == 200:
                res_body = json.loads(domains_res.data.decode('utf-8'))
                reverse_whois_output = open("reverse_whois_output", "a")

                for domain in res_body["domainsList"]:
                    # try:
                    #     dns.resolver.resolve(domain, 'A')
                    # except:
                    #     continue
                    reverse_whois_output.write(domain + "\n")
                    reverse_whois_output.flush()

                reverse_whois_output.close()
                if res_body["nextPageSearchAfter"] != None:
                    recursively_fetcher(whois_chunk, res_body["nextPageSearchAfter"])

                whois_chunks_to_be_ignored = open("registrant_info_to_be_ignored", "a")
                whois_chunks_to_be_ignored.write(whois_chunk + "\n")
                whois_chunks_to_be_ignored.close()

                break
            elif domains_res.status == 403:
                if api_key == whoisxmlapi_keys[-1]:
                    print("all api keys have run out of DRS credits! exiting...")
                    exit_after_proper_save('reverse_whois_output', True)
                continue
            else:
                print("ERROR with status code that isn't 403")
                exit_after_proper_save('reverse_whois_output', True)

    # for whois_chunk in ["Roche"]:
    with open('registrant_info_to_be_used') as whois_chunks:
        for whois_chunk in whois_chunks:
            whois_chunk = whois_chunk.replace("\n","")
            if whois_chunk == "":
                continue
            for api_key in whoisxmlapi_keys:
                body = {"searchType": "current","mode": "preview","punycode": True,"basicSearchTerms": {"include": [whois_chunk]}}
                domains_res = http.request('POST','https://reverse-whois.whoisxmlapi.com/api/v2', headers = {"X-Authentication-Token": api_key}, body = json.dumps(body))

                if domains_res.status == 200:
                    res_body = json.loads(domains_res.data.decode('utf-8'))
                    if res_body["domainsCount"] > 0:
                        recursively_fetcher(whois_chunk, 0)

                    break
                elif domains_res.status == 403:
                    if api_key == whoisxmlapi_keys[-1]:
                        print("all api keys have run out of DRS credits! exiting...")
                        exit_after_proper_save('reverse_whois_output', True)
                    continue
                else:
                    print("ERROR with status code that isn't 403")
                    exit_after_proper_save('reverse_whois_output', True)
    
    exit_after_proper_save('reverse_whois_output', False)

reverse_whois()