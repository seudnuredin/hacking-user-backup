import argparse
from collections import defaultdict
from sentence_transformers import SentenceTransformer, util
import humps

model = SentenceTransformer('all-MiniLM-L6-v2')  # A lightweight, efficient SBERT model

embedding_cache = {}
synonyms_cache = {}

def get_embedding(text):
    if text not in embedding_cache:
        embedding_cache[text] = model.encode(text, convert_to_tensor=True)
    return embedding_cache[text]

def split_param(param):
    return humps.kebabize(param).split("-")

def are_they_similar_params(params1, params2):
    # similarity_and_context_pairs = []
    print(param1)
    print(param2)

    for param1 in split_param(params2):
        if not param1 or len(param1) < 3:
            continue
    
        for param2 in split_param(params2):
            if not param2 or len(param2) < 3:
                continue

            # if (param1, param2) in synonyms_cache:
            #     similarity_and_context_pairs.append(synonyms_cache[(param1, param2)])
            #     continue

            embedding1 = get_embedding(param1)
            embedding2 = get_embedding(param2)
            similarity = util.cos_sim(embedding1, embedding2)
            similarity_num = round(similarity.item(), 1)
            similarity_bool = similarity_num >= 0.4
            if similarity_bool:
                synonyms_cache[(param1, param2)] = [similarity_bool, param1]
                return similarity_bool


parser = argparse.ArgumentParser(description="Run fuzz with specified URL, request file, and methods.")
parser.add_argument("-pf", "--paths-file", required=False, help="file containing output paths with keys in them")
parser.add_argument("-ipf", "--interested-paths-file", required=False, help="file containing output paths with keys in them")
args = parser.parse_args()

output_paths = []
interested_output_paths = []
interested_output_paths_raw = []
if args.paths_file:
    with open(args.paths_file, "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            req_type = path.split("_")[0]
            req_signature = path.split("_")[2]
            raw_keys_list = path.split("--key--")
            keys = []
            for i in range(1, len(raw_keys_list) - 1):
                keys.append(raw_keys_list[i])
            
            output_paths.append({"req_type": req_type, "req_signature": req_signature, "keys": keys}) 
            
if args.interested_paths_file:
    with open(args.interested_paths_file, "r") as paths_file:
        for path in paths_file:
            path = path.strip()
            req_type = path.split("_")[0]
            req_signature = path.split("_")[2]
            raw_keys_list = path.split("--key--")
            keys = []
            for i in range(1, len(raw_keys_list) - 1):
                keys.append(raw_keys_list[i])
            
            interested_output_paths.append({"req_type": req_type, "req_signature": req_signature, "keys": keys})
            interested_output_paths_raw.append(path)
            

grouped_output_paths = defaultdict(lambda: defaultdict(list))

for idx, item in enumerate(output_paths):
    rtype = item["req_type"]
    rsig = item["req_signature"]
    # store both the key list and the original index
    grouped_output_paths[rtype][rsig].append((idx, item["keys"]))

def does_the_req_has_an_id(output_path):
    # ---- Iteration example ----
    for rtype, sig_dict in grouped_output_paths.items():
        if output_path["req_type"] != rtype:
            continue
        
        for rsig, entries in sig_dict.items():
            if output_path["req_signature"] != rsig:
                continue
            
            for idx, keys in entries:
                # idx is the index of this record in interested_output_paths
                # print(f"    from index {idx} -> keys: {keys}")

                for key in keys:
                    if key in output_path["keys"] or key.isdigit():
                        continue
                    similarity_bool = are_they_similar_params(key, "id")
                    
                    if similarity_bool:
                        return similarity_bool
                    
                    similarity_bool = are_they_similar_params(key, "email")
                    
                    if similarity_bool:
                        return similarity_bool
                    
                    


# in user-req, in interesting paths, an id that doesn't exist on that particular(matching req_signature) from grouped_output_paths

final_output_paths = []

for idx, output_path in enumerate(interested_output_paths):
    if "user-req" in output_path["req_type"]:
        if does_the_req_has_an_id(output_path):
            final_output_paths.append(interested_output_paths_raw[idx])
    
    if "attacker-req" in output_path["req_type"]:
        for key in output_path["keys"]:
            
            similarity_bool = are_they_similar_params(key, "id")
            
            if similarity_bool:
                final_output_paths.append(interested_output_paths_raw[idx])
                    
            
            similarity_bool = are_they_similar_params(key, "email")
            
            if similarity_bool:
                final_output_paths.append(interested_output_paths_raw[idx])
                    
            
        # does_the_req_has_an_id(output_path)

# in attacker-req, in interesting paths, the existence of id should be checked

print("\n".join(final_output_paths))

