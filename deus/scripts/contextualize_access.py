import humps
import argparse
import json
from sentence_transformers import SentenceTransformer, util
from urllib.parse import urlparse
from multiprocessing import Pool, cpu_count
model = SentenceTransformer('all-MiniLM-L6-v2')  # A lightweight, efficient SBERT model

parser = argparse.ArgumentParser(description="Contextualize Paths")
parser.add_argument("-u", "--urls-file", required=False, help="urls file to perform")
parser.add_argument("-j", "--jsonl-file", required=False, help="jsonl file to perform")
parser.add_argument("-w", "--words-file", required=False, help="words to use instead of the default one")
args = parser.parse_args()

if not args.urls_file and not args.jsonl_file:
    print("you must supply either --urls-file or --jsonl-file arg")
    exit()

urls = []
paths = []
associated_words_of_urls = []
contextualized_paths = dict()
words = set()
familiar_words = set()
all_keys = list()

if args.urls_file:
    with open(args.urls_file, 'r', encoding='utf-8') as urls_file:
        for url in urls_file:
            url = url.strip()
            urls.append(url)
            path = urlparse(url).path
            paths.append(path)

if args.jsonl_file:
    with open(args.jsonl_file, 'r', encoding='utf-8') as jsonl_file:
        for url_keys in jsonl_file:
            url_keys = json.loads(url_keys.strip())
            url = url_keys["url"]
            urls.append(url)
            path = urlparse(url).path
            paths.append(path)
    
            all_keys.append(url_keys["keys"])

if args.words_file:
    with open(args.words_file, 'r', encoding='utf-8') as words_file:
        for word in words_file:
            word = word.strip()
            words.add(word.lower())
else:
    with open('/home/deus/documents/words.txt', 'r', encoding='utf-8') as words_file:
        for word in words_file:
            word = word.strip()
            words.add(word.lower())

def split_word(subpath):
    return humps.kebabize(subpath).split("-")

for path in paths:
    subpaths = path.split("/")
    for subpath in list(subpaths):
        subpaths.extend(split_word(subpath))
    
    for subpath in subpaths:
        if subpath.lower() in words and len(subpath) > 2:
            familiar_words.add(subpath)
    
    for i in range(len(subpaths) - 1, -1, -1):
        if subpaths[i] not in familiar_words:
            subpaths.pop(i)

    associated_words_of_urls.append(subpaths)

for keys in all_keys:
    # subpaths = path.split("/")
    for key in list(keys):
        keys.extend(split_word(key))
    
    for key in keys:
        if key.lower() in words and len(key) > 2:
            familiar_words.add(key)
    
    for i in range(len(keys) - 1, -1, -1):
        if keys[i] not in familiar_words:
            keys.pop(i)

    associated_words_of_urls.append(keys)

familiar_words = list(familiar_words)
# Simple cache for embeddings
embedding_cache = {}
synonyms_cache = {}

def get_embedding(text):
    if text not in embedding_cache:
        embedding_cache[text] = model.encode(text, convert_to_tensor=True)
    return embedding_cache[text]

def are_they_similar_subpaths(subpath1, subpaths2):
    similarity_and_context_pairs = []


    # for subpath1 in subpaths1:
        # if not subpath1 or len(subpath1) < 3:
        #     continue
    
    for subpath2 in subpaths2:
        if not subpath2 or len(subpath2) < 3:
            continue
        
        if (subpath1, subpath2) in synonyms_cache:
            similarity_and_context_pairs.append(synonyms_cache[(subpath1, subpath2)])
            continue

        embedding1 = get_embedding(subpath1)
        embedding2 = get_embedding(subpath2)
        similarity = util.cos_sim(embedding1, embedding2)
        similarity_num = round(similarity.item(), 1)
        if similarity_num >= 0.6:
            similarity_and_context_pairs.append([bool(similarity_num >= 0.4), subpath1])
            synonyms_cache[(subpath1, subpath2)] = [bool(similarity_num >= 0.4), subpath1]

    return similarity_and_context_pairs

def process_outer_index(i):
    local_context = {}
    # urlI = urls[i]
    # pathI = paths[i]
    familiar_word = familiar_words[i]

    for x in range(len(paths)):
        urlX = urls[x]
        pathX = paths[x]
        associated_wordsX = associated_words_of_urls[x]

        similarity_and_context_pairs = are_they_similar_subpaths(familiar_word, associated_wordsX)
        for similar, subpath1 in similarity_and_context_pairs:
            if similar:
                if subpath1 not in local_context:
                    local_context[subpath1] = []

                # if urlI not in local_context[subpath1]:
                #     local_context[subpath1].append(urlI)
                if urlX not in local_context[subpath1]:
                    local_context[subpath1].append(urlX)
    return local_context


def merge_dicts(dicts):
    merged = {}
    for d in dicts:
        for key, val in d.items():
            if key not in merged:
                merged[key] = []
            for item in val:
                if item not in merged[key]:
                    merged[key].append(item)
    return merged

# def merge_dicts(dicts):
#     merged = {}
    
#     for d in dicts:
#         for key, val in d.items():
#             # Try to find an existing similar key in merged
#             found_key = None
#             for existing_key in merged.keys():
#                 if len(existing_key) < 3:
#                     continue
                
#                 similarity_pairs = are_they_similar_subpaths(key, existing_key)
#                 for similar, _ in similarity_pairs:
#                     if similar:
#                         found_key = existing_key
#                         break
#                 if found_key:
#                     break
            
#             # If found, merge into that key
#             if found_key:
#                 for item in val:
#                     if item not in merged[found_key]:
#                         merged[found_key].append(item)
#             else:
#                 # Otherwise, create a new key
#                 merged[key] = list(val)
            
#             if key != found_key and len(found_key) > len(key):
#                 my_dict[key] = my_dict.pop(found_key)
    
#     return merged


# if __name__ == "__main__":
with Pool(cpu_count()) as pool:
    results = pool.map(process_outer_index, range(len(familiar_words)))

contextualized_paths = merge_dicts(results)

# for i in range(0, len(paths)):
#     urlI = urls[i]
#     pathI = paths[i]
#     familiar_word = associated_words_of_urls[i]
#     for x in range(0, len(paths)):
#         urlX = urls[x]
#         pathX = paths[x]
#         associated_wordsX = associated_words_of_urls[x]
#         similarity_and_context_pairs = are_they_similar_subpaths(familiar_word, associated_wordsX)
#         for similarity_and_context_pair in similarity_and_context_pairs:
#             similar = similarity_and_context_pair[0]
            
#             if similar:
#                 if subpath1 not in list(contextualized_paths.keys()):
#                     contextualized_paths[subpath1] = list()

#                 if urlI not in contextualized_paths[subpath1]:
#                     contextualized_paths[subpath1].append(urlI)
#                 if urlX not in contextualized_paths[subpath1]:
#                     contextualized_paths[subpath1].append(urlX)


# for all_paths in list(contextualized_paths.values()):
#     for path in paths:
#         path_doesnt_exist = True
#         path_only_exists_in_common_context = True
#         for specific_paths in all_paths:
#             if path in specific_paths:
#                 path_doesnt_exist = False
#                 if len(specific_paths) > 5:
#                     path_only_exists_in_common_context = False
        
#         if path_doesnt_exist:
#             if "unk" not in list(contextualized_paths.keys()):
#                 contextualized_paths["unk"] = list()
#             contextualized_paths["unk"].append(path)
        
#         if path_only_exists_in_common_context:
#             if "com_unk" not in list(contextualized_paths.keys()):
#                 contextualized_paths["com_unk"] = list()
#             contextualized_paths["com_unk"].append(path)

# for key in list(contextualized_paths.keys()):
#     if len(contextualized_paths[key]) == 1:
#         contextualized_paths.pop(key)

with open("grouped_paths.json", "w") as f:
    json.dump(contextualized_paths, f, indent=4)
