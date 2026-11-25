directory_or_file="$@"

# rm param_preliminary_wordlist.txt


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
        echo "removed: $output_file"
        # exit
    done

    if [[ $added_original_paths -eq 1 ]]; then
        echo "got here"
        cat $input_file | nl | anew -q $2.txt
    fi
}

# comment the 4 lines of codes below to manually edit param_pre... file and use it directly

cat ./../../extracted_paths_and_params/extracted_param_wordlist.txt | grep -E '^[A-Za-z_-]+$' | sort -u > wordlist_for_param_pattern_prepare.txt

generate_path_pattern wordlist_for_param_pattern_prepare param_based_path_pattern_prepare_output

sort -nr -k1,1 param_based_path_pattern_prepare_output.txt | awk '$1 && $2' | awk '$1 >= 2' | awk '{print $2}' | awk '!seen[$0]++' | head -n 100 > subpaths2.txt
while IFS= read -r k; do   [[ "$k" =~ ^~?PAYLOADDDD~?$ ]] && continue;   r=$(printf '%s\n' "$k" | sed -E 's/~?PAYLOADDDD~?/[A-Z_-]+[A-Za-z_-]+/g');   grep --text -E -e "^/?${r}(/|$)"        ./../../extracted_paths_and_params/extracted_param_wordlist.txt     | head -n2; done < subpaths2.txt | anew -q param_preliminary_wordlist.txt

all_params_count=$(wc -l < param_preliminary_wordlist.txt)

find $directory_or_file -type f  | grep -F -e method_and_url_file_within_threshold | while read -r file; do

    [ "$(wc -l < "$file")" -eq 0 ] && continue

    domain=$(echo $file | rev | cut -d / -f -1 | cut -d . -f 2- | rev | cut -d . -f 4-)


    non_param_paths=()

    while read -r path; do
        if [[ ! " ${non_param_paths[@]} " =~ " ${path} " ]]; then
            non_param_paths+=("$path")
        fi
    done < <(cat $file | awk '{print $2}' | unfurl paths | awk -F/ '{for (i=1; i<NF; i++) printf "%s/", $i; print ""}' | sort -u)

    is_param_based_host=0
    for path in "${non_param_paths[@]}"; do

        params_count=$(cat $file | awk '{print $2}' | unfurl paths | grep "^$path" | awk -F/ '{print $NF}' | sort -u | grep -Fx -f param_preliminary_wordlist.txt | wc -l)
        
        if [ "$params_count" -lt $((all_params_count / 2)) ] && [ "$params_count" -lt 10 ] && [ "$params_count" -ne 0 ]; then
            is_param_based_host=1

            echo $domain
            echo $params_count
            echo $path
            echo $file

        fi

    done

    if [ "$is_param_based_host" -eq 1 ]; then
        echo $domain | anew -q hosts_with_paths_and_params.txt
    else
        echo $domain | anew -q hosts_with_paths.txt
    fi

done

