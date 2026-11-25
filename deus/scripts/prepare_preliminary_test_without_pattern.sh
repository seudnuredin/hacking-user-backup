# handle_signal() {
#   echo "Caught signal: $1"
#   # Add your custom logic here (e.g., cleanup)
# #   exit 1
# }

# # Loop through all signals
# for sig in $(kill -l | tr ' ' '\n'); do
#     trap "handle_signal $sig" "$sig"
# done

rm preliminary_wordlist.txt
cat <(awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_extractor_rust_output.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_extractor_rust_output.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_extractor_rust_output.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt)  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9./_ -]' | grep --text -vE '^[0-9/]+$' | anew -q preliminary_wordlist.txt

cat <(awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt)  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9./_ -]' | grep --text -vE '^[0-9/]+$' | anew -q preliminary_wordlist.txt

cat <(awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt)  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9./_ -]' | grep --text -vE '^[0-9/]+$' | anew -q preliminary_wordlist.txt


cat ./../../extracted_paths_and_params/path_wordlist.txt ./../../extracted_paths_and_params/extracted_path_wordlist.txt <( cat ./../../extracted_paths_and_params/path_wordlist.txt ./../../extracted_paths_and_params/extracted_path_wordlist.txt | unfurl paths) | rg --text -e '^.{0,200}$' | rg --text -e '^[^/]*(/[^/]*){0,6}$' | cut -d ? -f -1 | sort -u > wordlist_for_path_pattern_prepare.txt
# mkdir wordlist_for_path_pattern_prepare

# for list_split in 5000 7500; do
#     split -l $list_split wordlist_for_path_pattern_prepare.txt ./wordlist_for_path_pattern_prepare/wordlist_for_path_pattern_prepare_ --additional-suffix=.txt

#     for file in wordlist_for_path_pattern_prepare/*; do
#       ~/scripts/path_pattern_prepare "$file" | anew -q path_pattern_prepare_output.txt
#     done

# done

generate_path_pattern() {
    output_dir="$1"
    mkdir -p "$output_dir"
    input_file="$1.txt"
    
    group_size=5000  # or 7500
    overlap=1000     # amount of overlap
    slide_size=$((group_size - overlap))
    
    total_lines=$(wc -l < "$input_file")
    start=0
    index=0
    
    while [ $start -lt $total_lines ]; do
        end=$((start + group_size))
        sed -n "$((start + 1)),$((end))p" "$input_file" > "$output_dir/wordlist_chunk_$index.txt"
        
        start=$((start + slide_size))
        index=$((index + 1))
    done
    
    rm $2.txt
    for file in $output_dir/*; do
      ~/scripts/path_pattern_prepare "$file" | anew -q $2.txt
      rm $file
    done
}

generate_path_pattern wordlist_for_path_pattern_prepare path_pattern_prepare_output

sort -nr -k1,1 path_pattern_prepare_output.txt | awk '{print $2}' | sed 's:^/*::' | awk '!seen[$0]++' | cut -d / -f -1  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' > subpaths.txt
sort -nr -k1,1 path_pattern_prepare_output.txt | awk '{print $2}' | sed 's:^/*::' | awk '!seen[$0]++' | cut -d / -f -2  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' | anew -q subpaths.txt
sort -nr -k1,1 path_pattern_prepare_output.txt | awk '{print $2}' | sed 's:^/*::' | awk '!seen[$0]++' | cut -d / -f -3  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' | anew -q subpaths.txt
# while IFS= read -r k; do grep --text -e "^$k/" -e "^/$k/" ./../../extracted_paths_and_params/extracted_path_and_param_wordlist.txt | awk '!/\/$/ { print length, $0 }'  | sort -n | head -n2 | cut -d' ' -f2-; done < subpaths.txt | anew -q preliminary_wordlist.txt
# while IFS= read -r k; do grep --text -e "^$k/" -e "^/$k/" ./../../extracted_paths_and_params/extracted_path_and_param_wordlist.txt | awk '/\/$/ { print length, $0 }'  | sort -n | head -n1 | cut -d' ' -f2- ; done < subpaths.txt | anew -q preliminary_wordlist.txt
# while IFS= read -r k; do grep --text -e "^$k/" -e "^/$k/" ./../../extracted_paths_and_params/extracted_path_and_param_wordlist.txt | awk -F. '!seen[$NF]++ && NF > 1'  | sort -n | head -n1 | cut -d' ' -f2- ; done < subpaths.txt | anew -q preliminary_wordlist.txt

export NPROC=$(nproc)
cat subpaths.txt | parallel -j "$NPROC" '
  k={}
  grep --text -e "^$k/" -e "^/$k/" ./../../extracted_paths_and_params/extracted_path_and_param_wordlist.txt |
  awk "!/\/$/ { print length, \$0 }" |
  sort -n |
  head -n2 |
  cut -d" " -f2-
' | anew -q preliminary_wordlist.txt

cat subpaths.txt | parallel -j "$NPROC" '
  k={}
  grep --text -e "^$k/" -e "^/$k/" ./../../extracted_paths_and_params/extracted_path_and_param_wordlist.txt |
  awk "/\/$/ { print length, \$0 }" |
  sort -n |
  head -n1 |
  cut -d" " -f2-
' | anew -q preliminary_wordlist.txt


cat subpaths.txt | parallel -j "$NPROC" '
  k={}
  grep --text -e "^$k/" -e "^/$k/" ./../../extracted_paths_and_params/extracted_path_and_param_wordlist.txt |
  awk -F. "NF > 1 && !seen[\$NF]++ { print length(\$0), \$0 }" |
  sort -n |
  head -n1 |
  cut -d" " -f2-
' | anew -q preliminary_wordlist.txt

cat ./../../extracted_paths_and_params/extracted_param_wordlist.txt | grep -E '^[A-Za-z_-]+$' | sort -u > wordlist_for_param_pattern_prepare.txt

generate_path_pattern wordlist_for_param_pattern_prepare param_based_path_pattern_prepare_output

sort -nr -k1,1 param_based_path_pattern_prepare_output.txt | awk '$1 && $2' | awk '$1 >= 2' | awk '{print $2}' | awk '!seen[$0]++' | head -n 100 > subpaths2.txt
while IFS= read -r k; do   [[ "$k" =~ ^~?PAYLOADDDD~?$ ]] && continue;   r=$(printf '%s\n' "$k" | sed -E 's/~?PAYLOADDDD~?/[A-Z_-]+[A-Za-z_-]+/g');   grep --text -E -e "^/?${r}(/|$)"        ./../../extracted_paths_and_params/extracted_param_wordlist.txt     | head -n2; done < subpaths2.txt | anew -q preliminary_wordlist.txt

# cat ./../../repo/extracted_path_wordlist.txt <( cat ./../../repo/extracted_path_wordlist.txt | unfurl paths) | rg --text -e '^.{0,200}$' | rg --text -e '^[^/]*(/[^/]*){0,6}$' | cut -d ? -f -1 | sort -u > repo_wordlist_for_path_pattern_prepare.txt


# generate_path_pattern repo_wordlist_for_path_pattern_prepare repo_path_pattern_prepare_output

# sort -nr -k1,1 repo_path_pattern_prepare_output.txt | awk '{print $2}' | sed 's:^/*::' | awk '!seen[$0]++' |  cut -d / -f -1  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' > repo_subpaths.txt
# sort -nr -k1,1 repo_path_pattern_prepare_output.txt | awk '{print $2}' | sed 's:^/*::' | awk '!seen[$0]++' | cut -d / -f -2  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' | anew -q repo_subpaths.txt
# while IFS= read -r k; do grep --text -e "^$k/" -e "^/$k/" ./../../repo/extracted_path_wordlist.txt | awk '!/\/$/ { print length, $0 }'  | sort -n | head -n2 | cut -d' ' -f2-; done < repo_subpaths.txt | anew -q preliminary_wordlist.txt
# while IFS= read -r k; do grep --text -e "^$k/" -e "^/$k/" ./../../repo/extracted_path_wordlist.txt | awk '/\/$/ { print length, $0 }'  | sort -n | head -n1 | cut -d' ' -f2- ; done < repo_subpaths.txt | anew -q preliminary_wordlist.txt
# while IFS= read -r k; do grep --text -e "^$k/" -e "^/$k/" ./../../repo/extracted_path_wordlist.txt | awk -F. '!seen[$NF]++ && NF > 1'  | sort -n | head -n1 | cut -d' ' -f2- ; done < repo_subpaths.txt | anew -q preliminary_wordlist.txt
