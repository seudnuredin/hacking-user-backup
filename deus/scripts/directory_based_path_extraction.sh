# directory_or_file="$@"

add_length=$1
file=$2


# handle_signal() {
#   echo "Caught signal: $1"
#   # Add your custom logic here (e.g., cleanup)
# #   exit 1
# }

# # Loop through all signals
# for sig in $(kill -l | tr ' ' '\n'); do
#     trap "handle_signal $sig" "$sig"
# done


rm preliminary_extracted_path_wordlist.txt path_pattern_prepare_output.txt

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
    for output_file in $output_dir/*; do
      ~/scripts/path_pattern_prepare "$output_file" | anew -q $2.txt
      rm $output_file
    done
}

# generate_path_pattern $(echo $file | sed 's/\.[^.]*$//' ) path_pattern_prepare_output

# sort -nr -k1,1 path_pattern_prepare_output.txt | awk '{print $2}' | sed 's/^\///g' | cut -d / -f -1  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -Fv PAYLOADDDD | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' | grep -v --text -E '^[0-9]+$' > subpaths.txt
# sort -nr -k1,1 path_pattern_prepare_output.txt | awk '{print $2}' | sed 's/^\///g' | cut -d / -f -2  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -Fv PAYLOADDDD | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' | grep -v --text -E '^[0-9]+$' | anew -q subpaths.txt


cat "$file" | cut -d / -f 2 | awk '!seen[$0]++' > subpaths.txt
# cat "$file" | cut -d / -f -2 | sort -u | anew -q subpaths.txt

extract_based_on_subpath() {
    export NPROC=$(nproc)

    cat subpaths.txt | parallel -j "$NPROC" '
      k={}
      grep --text -e "^$k/" -e "^/$k/" '"$1"' |
      sort -n |
      head -n'"$add_length"' |
      cut -d" " -f2-
    ' 

    cat subpaths.txt | parallel -j "$NPROC" '
      k={}
      grep --text -e "^$k/" -e "^/$k/" '"$1"' |
      sort -n |
      tail -n'"$add_length"' |
      cut -d" " -f2-
    ' 

}


extract_based_on_subpath $file

re_subpaths=$(paste -sd'|' subpaths.txt)

# if [[ -n "$re_subpaths" ]]; then
#     grep --text -Ev 'https?://[a-zA-Z0-9._-]+/('"$re_subpaths"')/' "$file" | sort -n | head -n 10000 
# fi

# if [[ -n "$re_subpaths" ]]; then
#     grep --text -Evf <(printf 'https?://[a-zA-Z0-9._-]+/(%s)/\n' "$re_subpaths") \
#         "$file" | sort -n | head -n 10000
# fi

if [[ -n "$re_subpaths" ]]; then
    tmp_pattern=$(mktemp)
    printf 'https?://[a-zA-Z0-9._-]+/(%s)/\n' "$re_subpaths" > "$tmp_pattern"
    grep --text -Evf "$tmp_pattern" "$file" | sort -n | head -n 10000
    rm -f "$tmp_pattern"
fi