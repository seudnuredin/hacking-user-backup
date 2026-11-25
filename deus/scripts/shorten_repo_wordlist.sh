
# handle_signal() {
#   echo "Caught signal: $1"
#   # Add your custom logic here (e.g., cleanup)
# #   exit 1
# }

# # Loop through all signals
# for sig in $(kill -l | tr ' ' '\n'); do
#     trap "handle_signal $sig" "$sig"
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


cat ./extracted_path_wordlist.txt <( cat ./extracted_path_wordlist.txt | unfurl paths) | rg --text -e '^.{0,200}$' | rg --text -e '^[^/]*(/[^/]*){0,6}$' | cut -d ? -f -1 | sort -u > repo_wordlist_for_path_pattern_prepare.txt


generate_path_pattern repo_wordlist_for_path_pattern_prepare repo_path_pattern_prepare_output

sort -nr -k1,1 repo_path_pattern_prepare_output.txt | awk '{print $2}' | sed 's:^/*::' | awk '!seen[$0]++' |  cut -d / -f -1  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' > repo_subpaths.txt
sort -nr -k1,1 repo_path_pattern_prepare_output.txt | awk '{print $2}' | sed 's:^/*::' | awk '!seen[$0]++' | cut -d / -f -2  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' | anew -q repo_subpaths.txt
sort -nr -k1,1 repo_path_pattern_prepare_output.txt | awk '{print $2}' | sed 's:^/*::' | awk '!seen[$0]++' | cut -d / -f -3  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' | anew -q repo_subpaths.txt



export NPROC=$(nproc)
cat repo_subpaths.txt | parallel -j "$NPROC" '
  k={}
  grep --text -e "^$k/" -e "^/$k/" ./extracted_path_wordlist.txt |
  awk "!/\/$/ { print length, \$0 }" |
  sort -n |
  head -n2 |
  cut -d" " -f2-
' | anew -q repo_preliminary_wordlist.txt

cat repo_subpaths.txt | parallel -j "$NPROC" '
  k={}
  grep --text -e "^$k/" -e "^/$k/" ./extracted_path_wordlist.txt |
  awk "/\/$/ { print length, \$0 }" |
  sort -n |
  head -n1 |
  cut -d" " -f2-
' | anew -q repo_preliminary_wordlist.txt


cat repo_subpaths.txt | parallel -j "$NPROC" '
  k={}
  grep --text -e "^$k/" -e "^/$k/" ./extracted_path_wordlist.txt |
  awk -F. "NF > 1 && !seen[\$NF]++ { print length(\$0), \$0 }" |
  sort -n |
  head -n1 |
  cut -d" " -f2-
' | anew -q repo_preliminary_wordlist.txt

