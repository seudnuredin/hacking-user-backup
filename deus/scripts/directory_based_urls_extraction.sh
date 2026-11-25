url_limit="$1"
content_type="$2"
output_type="$3"
shift 3
directory_or_file="$@"

rm urls.txt path_pattern_prepare_output.txt raw_output.txt

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

find $directory_or_file -type f | grep -F method_and_url | while read -r file; do
    echo "Processing $file"
    
    domain=$(echo $file | rev | cut -d / -f -1 | cut -d . -f 2- | rev | cut -d . -f 4-)
    
    if [[ "$content_type" == "all" ]]; then
        cat $file | awk '{print $2}' | unfurl paths | sort -u   > paths.txt
    
    else
        cat $file | awk '$3 ~ /\/'"$content_type"'/ {print $2}' | unfurl paths | sort -u   > paths.txt
    
    fi
    # ~/scripts/path_pattern_prepare paths.txt > path_pattern_prepare_output.txt

    # generate_path_pattern paths path_pattern_prepare_output
    
    # sort -nr -k1,1 path_pattern_prepare_output.txt | awk '{print $2}' | sed 's/^\///g' | cut -d / -f -1  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -Fv PAYLOADDDD | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' | grep -v --text -E '^[0-9]+$' > subpaths.txt
    
    cat paths.txt | cut -d / -f 2 | awk '!seen[$0]++' > subpaths.txt
    # cat paths.txt | cut -d / -f -2 | sort -u | anew -q subpaths.txt

    if [[ "$content_type" == "all" ]]; then
        while IFS= read -r k; do grep --text "$domain/$k/" $file  | sort -n | head -n $url_limit ; done < subpaths.txt | anew -q raw_output.txt
        while IFS= read -r k; do grep --text "$domain/$k/" $file  | sort -n | tail -n $url_limit ; done < subpaths.txt | anew -q raw_output.txt
    else
        while IFS= read -r k; do grep --text "$domain/$k/" $file | awk '$3 ~ /\/'"$content_type"'/' | sort -n | head -n $url_limit ; done < subpaths.txt | anew -q raw_output.txt
        while IFS= read -r k; do grep --text "$domain/$k/" $file | awk '$3 ~ /\/'"$content_type"'/' | sort -n | tail -n $url_limit ; done < subpaths.txt | anew -q raw_output.txt
    fi

    re_subpaths=$(paste -sd'|' subpaths.txt)
    
    # if [[ -n "$re_subpaths" ]]; then

    #     if [[ "$content_type" == "all" ]]; then
    #         grep --text -v "$domain/($re_subpaths)/" $file  | sort -n | head -n 500 | anew -q raw_output.txt
    #     else
    #         grep --text -v "$domain/($re_subpaths)/" $file  | sort -n | head -n 500 | awk '$3 ~ /\/'"$content_type"'/' | anew -q raw_output.txt
    #     fi

    # fi

    if [[ -n "$re_subpaths" ]]; then
        tmp_pattern=$(mktemp)
        printf '%s/%s/\n' "$domain" "($re_subpaths)" > "$tmp_pattern"

        if [[ "$content_type" == "all" ]]; then
            grep --text -v -f "$tmp_pattern" "$file" \
                | sort -n | head -n 500 \
                | anew -q raw_output.txt
        else
            grep --text -v -f "$tmp_pattern" "$file" \
                | sort -n | head -n 500 \
                | awk -v ct="$content_type" '$3 ~ "/" ct "/"' \
                | anew -q raw_output.txt
        fi

        rm -f "$tmp_pattern"
    fi


done



if [[ "$output_type" == "mf_url" ]]; then
    cat raw_output.txt | anew urls_old.txt | anew -q urls.txt
elif [[ "$output_type" == "url" ]]; then
    cat raw_output.txt | awk '{print $2}' | anew urls_old.txt | anew -q urls.txt
fi
