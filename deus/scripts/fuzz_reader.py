import sys
import subprocess
import argparse
import os
from multiprocessing import Pool, cpu_count
import re

parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument("-ip", "--injection-point", required=True, help="injection point id")
parser.add_argument("-ft", "--filter-type", required=True, choices=["status","line_count","word_count","content_length","content_type","body"], help="which filter to use for processing the injection point datas, available filters: status, line_count, word_count, content_length, content_type, body")
parser.add_argument("-jk", "--json-key", required=False, help="json key for when the filter type is body")
parser.add_argument("-nd", "--normal-directory", required=False, help="other account's normal output directory to check against the main output directory for shared injection point value")
parser.add_argument('-cn', '--consider-normal', action='store_true', help='if you want the normal request output of parameter to be considered in sensitive_parametersss')
args = parser.parse_args()

if args.filter_type == "body" and args.json_key == None:
    print("lmao, give it json key to look for")
    exit()

# Helper function to process a single file
def process_file_name(args):
    file_path, each_parameter, file_type, signature_only = args
    matching_files = set()

    # Check if the file matches the parameter and file_type, and doesn't contain any grep_filter items
    file_name = os.path.basename(file_path)

    pattern = r'_(.*)_'
    found_match = re.search(pattern, file_name)
    rev_cut_part = ""
    if found_match:
        rev_cut_part = found_match.group(1)

    if each_parameter == rev_cut_part and file_type in file_path:
        try:
            if signature_only:
                file_identifier = os.path.basename(file_path).split("_")[0]
            else:
                file_identifier = file_path
            
            if file_identifier:
                matching_files.add(file_identifier)
        except IndexError:
            pass  # Skip files that don't have enough path depth
    
    return matching_files

# Main function that uses multiprocessing to speed up file processing
def get_parameter_specific_file_signature(base_directory, each_parameter, file_type, signature_only):
    matching_files = set()
    file_paths = []

    # Collect all files from os.walk
    for root, _, files in os.walk(base_directory):
        for file in files:
            file_paths.append((os.path.join(root, file), each_parameter, file_type, signature_only))

    # Use multiprocessing to process each file in parallel
    with Pool(cpu_count()) as pool:
        results = pool.map(process_file_name, file_paths)

    # Combine results from all processes
    for result in results:
        matching_files.update(result)

    return sorted(matching_files)
    
# Helper function to process each file
def process_file_name_for_parameters(args):
    file_path, each_parameter, file_type = args
    matching_files = set()

    # Get the filename
    file_name = os.path.basename(file_path)

    # Check if the file matches the specified file_type
    if file_name.endswith(file_type):
        # Extract the part after the first `_` and remove the last two parts split by `_`
        try:
            pattern = r'_(.*)_'
            found_match = re.search(pattern, file_name)
            rev_cut_part = ""
            if found_match:
                rev_cut_part = found_match.group(1)

            # Check if each_parameter is in the resulting string
            
            if each_parameter != "" and each_parameter == rev_cut_part:
                matching_files.add(rev_cut_part)
            elif each_parameter == "" and rev_cut_part:
                matching_files.add(rev_cut_part)
        except IndexError:
            pass  # Skip if the file name does not have enough parts

    return matching_files

# Main function that uses multiprocessing to process files in parallel
def find_parameters(base_directory, each_parameter, file_type):
    matching_files = set()
    file_paths = []

    # Collect all files from os.walk
    for root, _, files in os.walk(base_directory):
        for file in files:
            file_paths.append((os.path.join(root, file), each_parameter, file_type))

    # Use multiprocessing to process each file in parallel
    with Pool(cpu_count()) as pool:
        results = pool.map(process_file_name_for_parameters, file_paths)

    # Combine results from all processes
    for result in results:
        matching_files.update(result)

    return sorted(matching_files)


# Helper function to process a single file
def process_file_for_values(args):
    file_path, each_parameter, file_type, filter_type = args
    matching_files = set()

    # Check if the file matches the parameter and file_type, and doesn't contain any grep_filter items
    file_name = os.path.basename(file_path)
    pattern = r'_(.*)_'
    found_match = re.search(pattern, file_name)
    rev_cut_part = ""
    if found_match:
        rev_cut_part = found_match.group(1)

    if each_parameter == rev_cut_part and file_type in file_path:
        parameter_specific_outputs = subprocess.run(f'cat {file_path} | jq empty >/dev/null 2>&1 && jq .{filter_type} {file_path} 2>/dev/null', shell=True, capture_output=True, text=True).stdout.split("\n")
        
        matching_files.update(parameter_specific_outputs)
    
    return matching_files

# Main function that uses multiprocessing to speed up file processing
def get_parameter_specific_values(base_directory, each_parameter, file_type, filter_type):
    matching_files = set()
    file_paths = []

    # Collect all files from os.walk
    for root, _, files in os.walk(base_directory):
        for file in files:
            file_paths.append((os.path.join(root, file), each_parameter, file_type, filter_type))

    # Use multiprocessing to process each file in parallel
    with Pool(cpu_count()) as pool:
        results = pool.map(process_file_for_values, file_paths)

    # Combine results from all processes
    for result in results:
        matching_files.update(result)

    return sorted(matching_files)

# Helper function to process a single file
def process_file_for_filesnames(args):
    file_path, each_parameter, file_type, filter_type, param_output = args
    matching_files = set()

    # Check if the file matches the parameter and file_type, and doesn't contain any grep_filter items
    file_name = os.path.basename(file_path)
    pattern = r'_(.*)_'
    found_match = re.search(pattern, file_name)
    rev_cut_part = ""
    if found_match:
        rev_cut_part = found_match.group(1)

    if each_parameter == rev_cut_part and file_type in file_path:
        parameter_specific_output_files = subprocess.run(f'cat {file_path} | grep -l -E \'"{filter_type}":[[:space:]]*{param_output}\'', shell=True, capture_output=True, text=True).stdout.split("\n")
        matching_files.update(parameter_specific_output_files)
    
    return matching_files

# Main function that uses multiprocessing to speed up file processing
def get_parameter_and_value_specific_files(base_directory, each_parameter, file_type, filter_type, param_output):
    matching_files = set()
    file_paths = []

    # Collect all files from os.walk
    for root, _, files in os.walk(base_directory):
        for file in files:
            file_paths.append((os.path.join(root, file), each_parameter, file_type, filter_type, param_output))

    # Use multiprocessing to process each file in parallel
    with Pool(cpu_count()) as pool:
        results = pool.map(process_file_for_filesnames, file_paths)

    # Combine results from all processes
    for result in results:
        matching_files.update(result)

    return sorted(matching_files)

if args.injection_point == "all_parametersss":
    if args.normal_directory == None:
        if args.filter_type == "body":
            parameter_specific_outputs = subprocess.run(f'find ./output -type f -name "*" | grep -F .body | sort -u | xargs cat | jq .{args.json_key} | sort -u', shell=True, capture_output=True, text=True).stdout.split("\n")
        else:
            parameter_specific_outputs = subprocess.run(f'find ./output -type f -name "*" | grep -F .json | sort -u | xargs cat | jq .{args.filter_type} | sort -u', shell=True, capture_output=True, text=True).stdout.split("\n")
        parameter_specific_outputs = [x for x in parameter_specific_outputs if x]
        parameter_specific_outputs_files = dict()
        for param_output in parameter_specific_outputs:

            if args.filter_type == "body":
                parameter_specific_output_files = subprocess.run(f'find ./output -type f -name "*" | grep -F .body | grep -v "/output/normal/" | sort -u | xargs grep -l -E \'"{args.json_key}":[[:space:]]*{param_output}\'', shell=True, capture_output=True, text=True).stdout.split("\n")
            else:        
                parameter_specific_output_files = subprocess.run(f'find ./output -type f -name "*" | grep -F .json | grep -v "/output/normal/" | sort -u | xargs grep -l -E \'"{args.filter_type}":[[:space:]]*{param_output}\'', shell=True, capture_output=True, text=True).stdout.split("\n")

            parameter_specific_output_files = [x for x in parameter_specific_output_files if x]
            parameter_specific_outputs_files[param_output] = parameter_specific_output_files
    else:
        all_parameters = find_parameters("./output", "", ".json")

        parameter_specific_outputs_files = dict()

        for each_parameter in all_parameters:
            if args.filter_type == "body":
                parameter_request_signatures = get_parameter_specific_file_signature("./output", each_parameter, ".body", True)
            else:
                parameter_request_signatures = get_parameter_specific_file_signature("./output", each_parameter, ".json", True)
            
            for req_sig in parameter_request_signatures:
                if args.filter_type == "body":
                    req_sig_output_normal = subprocess.run(f'cat ./output/normal/{req_sig}.body | jq empty >/dev/null 2>&1 && jq -r .{args.json_key} ./output/normal/{req_sig}.body 2>/dev/null | sort -u', shell=True, capture_output=True, text=True).stdout.split("\n")[0]
                    req_sig_output_new = subprocess.run(f'cat {args.normal_directory}/{req_sig}.body | jq empty >/dev/null 2>&1 && jq -r .{args.json_key} {args.normal_directory}/{req_sig}.body 2>/dev/null  | sort -u', shell=True, capture_output=True, text=True).stdout.split("\n")[0]
                else:
                    req_sig_output_normal = subprocess.run(f'cat ./output/normal/{req_sig}.json | jq empty >/dev/null 2>&1 && jq -r .{args.filter_type} ./output/normal/{req_sig}.json 2>/dev/null | sort -u', shell=True, capture_output=True, text=True).stdout.split("\n")[0]
                    req_sig_output_new = subprocess.run(f'cat {args.normal_directory}/{req_sig}.json | jq empty >/dev/null 2>&1 && jq -r .{args.filter_type} {args.normal_directory}/{req_sig}.json 2>/dev/null  | sort -u', shell=True, capture_output=True, text=True).stdout.split("\n")[0]
                
                if req_sig_output_normal == req_sig_output_new:
                    if req_sig_output_new.strip() == "":
                        req_sig_output_new = f"{args.json_key} doesnt exist"
                    if req_sig_output_new not in parameter_specific_outputs_files.keys():
                        parameter_specific_outputs_files[req_sig_output_new] = list()
                    each_parameter_to_be_appended = each_parameter + " shared"
                    if each_parameter_to_be_appended not in parameter_specific_outputs_files[req_sig_output_new]:
                        parameter_specific_outputs_files[req_sig_output_new].append(each_parameter_to_be_appended)
                else:
                    if req_sig_output_new.strip() == "":
                        req_sig_output_new = f"{args.json_key} doesnt exist"
                    if req_sig_output_new not in parameter_specific_outputs_files.keys():
                        parameter_specific_outputs_files[req_sig_output_new] = list()
                    
                    each_parameter_to_be_appended = each_parameter + " not shared"
                    if each_parameter_to_be_appended not in parameter_specific_outputs_files[req_sig_output_new]:
                        parameter_specific_outputs_files[req_sig_output_new].append(each_parameter_to_be_appended)
    
    # Sorting the dictionary by the length of the lists
    parameter_specific_outputs_files = {k: v for k, v in sorted(parameter_specific_outputs_files.items(), key=lambda item: len(item[1]), reverse=True)}
    for k,v in parameter_specific_outputs_files.items():
        if args.json_key != None:
            print(f"{args.filter_type}.{args.json_key}: {k}")
        else:
            print(f"{args.filter_type}: {k}")
        
        for file_path in v:
            print(file_path)

elif args.injection_point == "sensitive_parametersss":
    all_parameters = find_parameters("./output", "", ".json")

    parameters_outputs = dict()

    for each_parameter in all_parameters:
        if args.filter_type == "body":
            parameter_specific_outputs = get_parameter_specific_values("./output", each_parameter, ".body", args.json_key)
        else:
            parameter_specific_outputs = get_parameter_specific_values("./output", each_parameter, ".json", args.filter_type)
        
        parameter_request_signatures = get_parameter_specific_file_signature("./output", each_parameter, ".json", True)

        if args.consider_normal:
            for req_sig in parameter_request_signatures:
                req_sig_outputs = subprocess.run(f'find ./output -type f -name "*{req_sig}*" | grep -F .json | grep "/output/normal/" | sort -u | xargs cat | jq .{args.filter_type} | sort -u', shell=True, capture_output=True, text=True).stdout.split("\n")
                for req_sig_output in req_sig_outputs:
                    parameter_specific_outputs.append(req_sig_output)

        parameters_outputs[each_parameter] = [parameter_specific_outputs,parameter_request_signatures]
    
    # Sorting the dictionary by the length of the lists
    parameters_outputs = {k: v for k, v in sorted(parameters_outputs.items(), key=lambda item: len(item[1][0])/len(item[1][1]), reverse=True)}
    for k,v in parameters_outputs.items():
        print(f"{k} {len(v[0])} {len(v[1])}")

elif args.filter_type in ["status","line_count","word_count","content_length","content_type"]:
    if args.normal_directory == None:
        
        parameter_specific_outputs = get_parameter_specific_values("./output", args.injection_point, ".json", args.filter_type)
        
        parameter_specific_outputs_files = dict()
        for param_output in parameter_specific_outputs:
            parameter_specific_outputs_files[param_output] = get_parameter_and_value_specific_files("./output", args.injection_point, ".json", args.filter_type, param_output)

    else:
        parameter_request_signatures = get_parameter_specific_file_signature("./output", args.injection_point, ".json", True)

        parameter_specific_outputs_files = dict()
        for req_sig in parameter_request_signatures:
            req_sig_output_normal = subprocess.run(f'cat ./output/normal/{req_sig}.json | jq empty >/dev/null 2>&1 && jq .{args.filter_type} ./output/normal/{req_sig}.json 2>/dev/null | sort -u', shell=True, capture_output=True, text=True).stdout.split("\n")[0]
            req_sig_output_new = subprocess.run(f'cat {args.normal_directory}/{req_sig}.json | jq empty >/dev/null 2>&1 && jq .{args.filter_type} {args.normal_directory}/{req_sig}.json 2>/dev/null  | sort -u', shell=True, capture_output=True, text=True).stdout.split("\n")[0]
            
            if req_sig_output_normal == req_sig_output_new:
                    if req_sig_output_new.strip() == "":
                        req_sig_output_new = f"{args.json_key} doesnt exist"
                    if req_sig_output_new not in parameter_specific_outputs_files.keys():
                        parameter_specific_outputs_files[req_sig_output_new] = list()
                    req_sig_to_be_appended = req_sig + ".json" + " shared"
                    if req_sig_to_be_appended not in parameter_specific_outputs_files[req_sig_output_new]:
                        parameter_specific_outputs_files[req_sig_output_new].append(req_sig_to_be_appended)
            else:
                if req_sig_output_new.strip() == "":
                    req_sig_output_new = f"{args.json_key} doesnt exist"
                if req_sig_output_new not in parameter_specific_outputs_files.keys():
                    parameter_specific_outputs_files[req_sig_output_new] = list()
                req_sig_to_be_appended = req_sig + ".json" + " not shared"
                if req_sig_to_be_appended not in parameter_specific_outputs_files[req_sig_output_new]:
                    parameter_specific_outputs_files[req_sig_output_new].append(req_sig_to_be_appended)
                        
            
    # Sorting the dictionary by the length of the lists
    parameter_specific_outputs_files = {k: v for k, v in sorted(parameter_specific_outputs_files.items(), key=lambda item: len(item[1]), reverse=True)}
    for k,v in parameter_specific_outputs_files.items():
        if args.json_key != None:
            print(f"{args.filter_type}.{args.json_key}: {k}")
        else:
            print(f"{args.filter_type}: {k}")
        
        for file_path in v:
            print(file_path)
else:
    if args.normal_directory == None:
        parameter_specific_outputs = get_parameter_specific_values("./output", args.injection_point, ".body", args.json_key)
        
        parameter_specific_outputs_files = dict()
        for param_output in parameter_specific_outputs:
            parameter_specific_outputs_files[param_output] = get_parameter_and_value_specific_files("./output", args.injection_point, ".body", args.json_key, param_output)

    else:
        
        parameter_request_signatures = get_parameter_specific_file_signature("./output", args.injection_point, ".body", True)

        parameter_specific_outputs_files = dict()
        for req_sig in parameter_request_signatures:
            req_sig_output_normal = subprocess.run(f'cat ./output/normal/{req_sig}.body | jq empty >/dev/null 2>&1 && jq .{args.json_key} ./output/normal/{req_sig}.body 2>/dev/null | sort -u', shell=True, capture_output=True, text=True).stdout.split("\n")[0]
            req_sig_output_new = subprocess.run(f'cat {args.normal_directory}/{req_sig}.body | jq empty >/dev/null 2>&1 && jq .{args.json_key} {args.normal_directory}/{req_sig}.body 2>/dev/null  | sort -u', shell=True, capture_output=True, text=True).stdout.split("\n")[0]
            

            if req_sig_output_normal == req_sig_output_new:
                    if req_sig_output_new.strip() == "":
                        req_sig_output_new = f"{args.json_key} doesnt exist"
                    if req_sig_output_new not in parameter_specific_outputs_files.keys():
                        parameter_specific_outputs_files[req_sig_output_new] = list()
                    req_sig_to_be_appended = req_sig + ".body" + " shared"
                    if req_sig_to_be_appended not in parameter_specific_outputs_files[req_sig_output_new]:
                        parameter_specific_outputs_files[req_sig_output_new].append(req_sig_to_be_appended)
            else:
                if req_sig_output_new.strip() == "":
                    req_sig_output_new = f"{args.json_key} doesnt exist"
                if req_sig_output_new not in parameter_specific_outputs_files.keys():
                    parameter_specific_outputs_files[req_sig_output_new] = list()
                req_sig_to_be_appended = req_sig + ".body" + " not shared"
                if req_sig_to_be_appended not in parameter_specific_outputs_files[req_sig_output_new]:
                    parameter_specific_outputs_files[req_sig_output_new].append(req_sig_to_be_appended)

    # Sorting the dictionary by the length of the lists
    parameter_specific_outputs_files = {k: v for k, v in sorted(parameter_specific_outputs_files.items(), key=lambda item: len(item[1]), reverse=True)}
    for k,v in parameter_specific_outputs_files.items():
        if args.json_key != None:
            print(f"{args.filter_type}.{args.json_key}: {k}")
        else:
            print(f"{args.filter_type}: {k}")
        
        for file_path in v:
            print(file_path)
    