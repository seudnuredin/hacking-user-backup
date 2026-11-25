import multiprocessing
try:
   multiprocessing.set_start_method('fork', force=True)
   print("forked")
except RuntimeError:
    print("unable to fork!")
    exit()

import sqlite3
import re
import sys
import subprocess
import time
import os
import shutil
import requests
import hashlib
import json
import socks
from botasaurus.request import request, Request
import signal

conn = sqlite3.connect('/home/deus/targets/source_monitoring/sources.db')
cursor = conn.cursor()
cursor.execute("""SELECT * FROM sources""")
sources = cursor.fetchall()
conn.close()

sources_len = len(sources)
counter = multiprocessing.Value('i',1)

def check_diff(source):
    global sources
    global sources_len
    global counter

    index_of_source = sources.index(source)
    
    def hash_file(content):
        h = hashlib.sha1()
        h.update(content)
        return h.hexdigest()
    
    @request(proxy="https://isp.smartproxy.com:10000",max_retry=2)
    def return_hash_of_downloaded_file(request: Request, data):
        hash_of_file = 0
        
        try:
            response = request.get(data, timeout=10)

            def save_it_as_file_get_its_sha1sum():
                hash_of_file = 0
                
                hash_of_file = hash_file(response.content)
                with open(f'/home/deus/targets/source_monitoring/sources/{hash_of_file}', 'wb') as out_file:
                    out_file.write(response.content)
                
                return hash_of_file
            try:
                hash_of_file = save_it_as_file_get_its_sha1sum()
            except:
                hash_of_file = save_it_as_file_get_its_sha1sum()
        except:
            pass
        return hash_of_file

    url_of_source = source[1]
    hash_of_source = source[2]
    
    current_hash_of_source = return_hash_of_downloaded_file(data=url_of_source)
    
    if hash_of_source != current_hash_of_source:

        diff_output = list()
        if source[3] == 1:
            diff_output = subprocess.run(f"bash -c ' diff <(js-beautify --no-rename --no-types  /home/deus/targets/source_monitoring/sources/{current_hash_of_source}) <(js-beautify --no-rename --no-types  /home/deus/targets/source_monitoring/sources/{hash_of_source}) '", shell=True, capture_output=True, text=True).stdout.split("\n")
        else:
            diff_output = subprocess.run(f"bash -c ' diff /home/deus/targets/source_monitoring/sources/{current_hash_of_source} /home/deus/targets/source_monitoring/sources/{hash_of_source} '", shell=True, capture_output=True, text=True).stdout.split("\n")
        line_count = -1
        for line in diff_output:
            if line == "---":
                break
            line_count += 1
        
        # if they are different enough
        if source[4] < line_count:
            conn = sqlite3.connect('/home/deus/targets/source_monitoring/sources.db')
            cursor = conn.cursor()
            cursor.execute("""UPDATE sources SET sha1_sum = ? WHERE id = ?""", (current_hash_of_source, source[0]))
            conn.commit()
            conn.close()

            log_file = open("/home/deus/targets/source_monitoring/logfile.log", "a")
            log_file.write("change detected: " + str(source[3]) + "'s url " + str(url_of_source) + " with " + str(hash_of_source) + " is returning " + str(current_hash_of_source) + "\n")
            log_file.close()
    
    with counter.get_lock():
        counter.value += 1

pool = multiprocessing.Pool(20)
pool.map(check_diff, sources, chunksize=1)


# subprocess.run(f'/bin/bash -c \'rm /tmp/web_resources/web_resource_to_be_hashed_* \' ', shell=True)