


~/scripts/path_pattern_prepare <(find . -mindepth 3 -maxdepth 3 -type d -printf '%f\n') > param_based_path_pattern_prepare_output.txt
sort -nr -k1,1 param_based_path_pattern_prepare_output.txt | awk '$1 && $2' | awk '$1 >= 2' | head -n 100 | awk '{print $2}' > subpaths2.txt

while IFS= read -r k; do   [[ "$k" =~ ^~?PAYLOADDDD~?$ ]] && continue;   r=$(printf '%s\n' "$k" | sed -E 's/~?PAYLOADDDD~?/[A-Z_-]+[A-Za-z_-]+/g');   grep --text -E -e "^/?${r}(/|$)"        <(find . -mindepth 3 -maxdepth 3 -type d -printf '%f\n')     | head -n2; done < subpaths2.txt | sort -fu | awk 'length($0) > 4' | anew special_queries_old.txt > special_queries.txt

while IFS= read -r k; do   [[ "$k" =~ ^~?PAYLOADDDD~?$ ]] && continue;   r=$(printf '%s\n' "$k" | sed -E 's/~?PAYLOADDDD~?/[A-Z_-]+[A-Za-z_-]+/g');   grep --text -E -e "^/?${r}(/|$)"        <(find . -mindepth 3 -maxdepth 3 -type d -printf '%f\n')     | head -n2; done < subpaths2.txt | python3.7 -c 'import humps; import sys; [print(humps.kebabize(line)) for line in sys.stdin if line.strip()] ' | tr '-' '\n' | sort -fu | awk 'length($0) > 4' | anew special_queries_old.txt | anew -q special_queries.txt

