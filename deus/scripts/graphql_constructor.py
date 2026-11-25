import re
import json
import sys


with open(sys.argv[1], 'r') as raw_escaped_graphqls:
    for raw_escaped_graphql in raw_escaped_graphqls:

        # 2. Un-escape into real newlines/tabs
        query_str = raw_escaped_graphql.encode('utf-8').decode('unicode_escape').replace("\\n","\n").replace("\\t","\t")

        # 3. Extract operationName
        op_match = re.search(r'(query|mutation)\s+([A-Za-z_-]\w*)', query_str)
        operation_name = op_match.group(2) if op_match else None

        # 4. Find ALL variable names before a colon
        #    e.g. matches clientId, fooBar, baz in ($clientId: ID!, $fooBar: String, $baz: Int)
        before_brace = query_str.split('{', 1)[0]

# 2. Find variables before colon in that part only
        var_names = re.findall(r'\$(\w+)\s*:', before_brace)

        # 5. Build a variables dict with placeholder values
        #    (You can replace the "PLACEHOLDER" with real data as needed.)
        variables = {name: "PLACEHOLDER" for name in var_names}

        # 6. Assemble final payload
        payload = {
            "operationName": operation_name,
            "variables": variables,
            "query": query_str
        }

        # 7. Pretty-print JSON
        print(json.dumps(payload))
