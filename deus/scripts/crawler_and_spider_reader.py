import json
import os
import subprocess

def read_katana_json_output(path_to_output):
    reqs_and_resps_of_single_phase = list()
    with open(path_to_output, "r") as file_output:
        for line in file_output:
            try:
                # result = subprocess.run(
                #         ['jq', '.'],
                #         input=line.strip().encode('utf-8'),
                #         capture_output=True,
                #         check=True
                #     )
                reqs_and_resps_of_single_phase.append(json.loads(line.strip()))
            except:
                pass

    return reqs_and_resps_of_single_phase

def get_all_values(d):
    values = []
    
    def extract_values(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                extract_values(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_values(item)
        else:
            values.append(obj)
    
    extract_values(d)
    return "_".join(values)

links = set()
forms = set()
paths_of_outputs = os.listdir("./")

for path in paths_of_outputs:
    reqs_and_resps_of_single_phase = read_katana_json_output(path)
    for req_and_resp in reqs_and_resps_of_single_phase:
        
        if "response" in req_and_resp.keys() and "forms" in req_and_resp["response"].keys() and get_all_values(req_and_resp["response"]["forms"]) not in forms:
            forms.add(get_all_values(req_and_resp["response"]["forms"]))
            links.add(req_and_resp["request"]["endpoint"])


links = list(links)
print(json.dumps(links))

