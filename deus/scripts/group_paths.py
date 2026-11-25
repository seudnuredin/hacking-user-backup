import humps
import argparse
import json
from sentence_transformers import SentenceTransformer, util
from urllib.parse import urlparse
model = SentenceTransformer('all-MiniLM-L6-v2')  # A lightweight, efficient SBERT model

parser = argparse.ArgumentParser(description="Contextualize Paths")
parser.add_argument("-u", "--urls-file", required=True, help="urls file to perform")
args = parser.parse_args()

urls = []
paths = []
subpaths_of_paths = []
contextualized_paths = dict()
with open(args.urls_file, 'r', encoding='utf-8') as urls_file:
    for url in urls_file:
        url = url.strip()
        urls.append(url)
        path = urlparse(url).path
        paths.append(path)

def split_subpath(subpath):
    return humps.kebabize(subpath).split("-")

for path in paths:
    subpaths = path.split("/")
    for subpath in list(subpaths):
        subpaths.extend(split_subpath(subpath))
    
    subpaths_of_paths.append(subpaths)

# Simple cache for embeddings
embedding_cache = {}

def get_embedding(text):
    if text not in embedding_cache:
        embedding_cache[text] = model.encode(text, convert_to_tensor=True)
    return embedding_cache[text]

def are_they_similar_subpaths(subpaths1, subpaths2):
    similarity_and_context_pairs = []

    for subpath1 in subpaths1:
        if not subpath1 or len(subpath1) < 3:
            continue
        
        for subpath2 in subpaths2:
            if not subpath2 or len(subpath2) < 3:
                continue

            embedding1 = get_embedding(subpath1)
            embedding2 = get_embedding(subpath2)

            similarity = util.cos_sim(embedding1, embedding2)
            similarity_num = round(similarity.item(), 1)
            if similarity_num >= 0.6:
                similarity_and_context_pairs.append([bool(similarity_num >= 0.4), subpath1])
    
    return similarity_and_context_pairs


for i in range(0, len(paths)):
    urlI = urls[i]
    pathI = paths[i]
    subpathsI = subpaths_of_paths[i]
    for x in range(0, len(paths)):
        urlX = urls[x]
        pathX = paths[x]
        subpathsX = subpaths_of_paths[x]
        similarity_and_context_pairs = are_they_similar_subpaths(subpathsI, subpathsX)
        for similarity_and_context_pair in similarity_and_context_pairs:
            similar = similarity_and_context_pair[0]
            subpath1 = similarity_and_context_pair[1]
            # similar, subpath1 = are_they_similar_subpaths(subpathsI, subpathsX)
            if similar:
                if subpath1 not in list(contextualized_paths.keys()):
                    contextualized_paths[subpath1] = list()

                if urlI not in contextualized_paths[subpath1]:
                    contextualized_paths[subpath1].append(urlI)
                if urlX not in contextualized_paths[subpath1]:
                    contextualized_paths[subpath1].append(urlX)

                # with open("grouped_paths.json", "w") as f:
                #     json.dump(contextualized_paths, f, indent=4)

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

for key in list(contextualized_paths.keys()):
    if len(contextualized_paths[key]) == 1:
        contextualized_paths.pop(key)

with open("grouped_paths.json", "w") as f:
    json.dump(contextualized_paths, f, indent=4)
