
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 pattern_type method_output_file(s)"
    exit 1
fi


if [[ "$1" != "repo" && "$1" != "target_api_paths" && "$1" != "target_api_words" && "$1" != "target_files" ]]; then
  echo "Invalid pattern_type: $2. Must be either repo, target_api_paths, target_api_words, or target_files"
  exit 1
fi

pattern_type=$1
content_type=$2

shift 2
directory_or_file="$@"

rm path_pattern_prepare_output.txt

domains=()
while read -r file; do
    domain=$(echo $file | rev | cut -d / -f -1 | cut -d . -f 2- | rev | cut -d . -f 4-)
    if [[ ! " ${domains[@]} " =~ " ${domain} " ]]; then
        domains+=("$domain")
    fi
    # echo $domain
    # domains+=("$domain")
done < <(find $directory_or_file -type f | grep -e method_and_url_file_within_threshold)

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

mkdir ./get_patterns
for domain in "${domains[@]}"; do

    rm wordlist_${domain}.txt

    find $directory_or_file -type f | grep -F $domain | grep -F -e method_and_url_file_within_threshold | while read -r file; do
        if [[ "$content_type" == "all" ]]; then
            cat $file | awk '{print $2}' | unfurl paths | anew -q wordlist_${domain}.txt
        else
            cat $file | awk '$3 ~ /\/'"$content_type"'/ {print $2}' | unfurl paths | anew -q wordlist_${domain}.txt
        fi
    done

    if [[ "$pattern_type" == "repo" || "$pattern_type" == "target_api_paths" || "$pattern_type" == "target_api_words" ]]; then


        generate_path_pattern wordlist_${domain} path_pattern_prepare_output

        if [[ "$pattern_type" == "repo" ]]; then
            mkdir ./get_patterns/repo
            awk '$1 && $2' path_pattern_prepare_output.txt | grep /PAYLOADDDD$  | grep -vF -e ^/PAYLOADDDD -e ~PAYLOADDDD -e PAYLOADDDD~ -e PAYLOADDDD/ -e PAYLOADDDD. | awk '{print $2}' | anew -q ./get_patterns/repo/pw_${domain}.txt
        fi

        if [[ "$pattern_type" == "target_api_paths" ]]; then
            mkdir ./get_patterns/target_api_paths
            awk '$1 && $2' path_pattern_prepare_output.txt | grep -e /PAYLOADDDD -e PAYLOADDDD/ | grep -vF -e ~PAYLOADDDD -e PAYLOADDDD~ -e PAYLOADDDD. | awk '{print $2}' | anew -q ./get_patterns/target_api_paths/pw_${domain}.txt
        fi

        if [[ "$pattern_type" == "target_api_words" ]]; then
            mkdir ./get_patterns/target_api_words
            awk '$1 && $2' path_pattern_prepare_output.txt | grep -e ~PAYLOADDDD -e PAYLOADDDD~ | awk '{print $2}' | anew -q ./get_patterns/target_api_words/pw_${domain}.txt
        fi

    fi

    if [[ "$pattern_type" == "target_files" ]]; then
        mkdir ./get_patterns/target_files

        while read -r file_path; do
            ext=$(echo $file_path | unfurl format %e | sort -u | sed 's|^|.|g' | grep -xFi -f /usr/share/seclists/Discovery/Web-Content/raft-large-extensions-lowercase.txt)
            if [ -z "$ext" ]; then
                continue  
            fi

            PAYLOADDDD_PATH="${file_path%/*}/PAYLOADDDD${ext}"
            echo $PAYLOADDDD_PATH | anew -q ./get_patterns/target_files/pw_${domain}.txt

            PAYLOADDDD_PATH="${file_path%/*}/PAYLOADDDD"
            echo $PAYLOADDDD_PATH | anew -q ./get_patterns/target_files/pw_${domain}.txt

        done < wordlist_${domain}.txt

        
    fi

done


rm -rf wordlist_*
