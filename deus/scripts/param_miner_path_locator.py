import json
from urllib.parse import urlparse

url = "https://assets-aus.snapfish.com/pict/v2/collection/shared/150310241060/assets"
path = urlparse(url).path
subpaths = path.split("/")
paths = list()

with open("path_locator_output.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        try:
            record = json.loads(line)
        except:
            print(line)
            continue

        for i in range(0, len(subpaths)):
            subpath = subpaths[i]
            if (i == 0 and f"{subpath}/" == record["match"]) or (i == len(subpaths) - 1 and f"/{subpath}" == record["match"]) or (f"{subpath}/" == record["match"] or f"/{subpath}" == record["match"]):
                if "_path_" in record["path"] or "_param_" in record["path"] or "/path" in record["path"]:
                    continue

                paths.append(record["path"])
    

for path in paths:
    print(path)

