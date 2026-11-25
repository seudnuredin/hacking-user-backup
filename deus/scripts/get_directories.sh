rate="$1"
shift 1
directory_or_file="$@"

rm path_pattern_prepare_output.txt pw_all.txt

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



domains=()

while read -r file; do
    domain=$(echo $file | rev | cut -d / -f -1 | cut -d . -f 2- | rev | cut -d . -f 4-)
    if [[ ! " ${domains[@]} " =~ " ${domain} " ]]; then
        domains+=("$domain")
    fi
    
done < <(find $directory_or_file -type f | grep -e method_and_url)

mkdir ./get_directories_patterns
mkdir ./get_directories_patterns_test
get_dirs() {

    generate_path_pattern $1 path_pattern_prepare_output

    awk '$1 && $2' path_pattern_prepare_output.txt | grep /PAYLOADDDD$ | awk '{print $2}' | sed 's|^/||' | sort -u > $1.txt
    

    echo "Started on: $domain"


    ffuf -u "https://$domain/FUZZ" -timeout 10 -json -w $1.txt -mc all -s -rate $rate -t $rate -X GET -H "User-Agent: Mozilla/5.0 Windows NT 10.0 Win64 AppleWebKit/537.36 Chrome/69.0.3497.100" -noninteractive -x http://127.0.0.1:9239 > ./ffuf_output.json

    # exit
    cat ffuf_output.json | grep -Fv '"status":502' > ffuf_output_2.json
    mv ffuf_output_2.json ffuf_output.json

    rm ./get_directories_patterns_test/method_and_url_file*
    (
      cd ./get_directories_patterns_test/ || exit 1
      bash ~/scripts/preliminary_path_brute_force_output_reader.sh all all $content_measure ./../ffuf_output.json
    )
    # cat method_and_url_file* | awk '{print $2}' | unfurl paths | sort -u | anew pw_${domain}_old.txt | anew -q pw_${domain}.txt
    cat ./get_directories_patterns_test/method_and_url_file* | awk '{print $2}' | unfurl paths | sort -u | anew -q ./get_directories_patterns_test/pw_${domain}.txt
    cat ./get_directories_patterns_test/method_and_url_file* | awk '{print $2}' | anew -q all_directories.txt

}

rota --config /home/deus/documents/rota_config.yml -p 9239 > /dev/null 2>&1 &
rota_pid=$!
added_original_paths=0
content_measure=5
for domain in "${domains[@]}"; do
    rm wordlist_${domain}.txt

    find $directory_or_file -type f | grep -F $domain | grep -F -e method_and_url | while read -r file; do


#         cat $file | awk '{print $2}' | unfurl paths | awk -F/ '{
#   for (i = 2; i <= NF; i++) {
#     path = ""
#     for (j = 2; j <= i; j++) path = path "/" $j
#     print path "/test1"
#     print path "/test2"
#   }
# }' | anew -q wordlist_${domain}.txt

        cat $file | awk '{print $2}' | unfurl paths | anew -q wordlist_${domain}.txt
    done

    prev_lines=0

    while true; do
        current_lines=$(wc -l < "wordlist_${domain}.txt" 2>/dev/null)

        if [[ "$current_lines" -eq "$prev_lines" || "$current_lines" -eq 0 ]]; then
            break
        fi

        prev_lines=$current_lines

        get_dirs "wordlist_${domain}"
    done

    # get_dirs wordlist_${domain}
    # get_dirs wordlist_${domain}
    # get_dirs wordlist_${domain}
    # get_dirs wordlist_${domain}
    # get_dirs wordlist_${domain}
    # get_dirs wordlist_${domain}

done

added_original_paths=1
content_measure=1
for domain in "${domains[@]}"; do

    line_count=$(wc -l < "./get_directories_patterns_test/pw_${domain}.txt")

    # Skip if line count is 0
    if [[ $line_count -eq 0 ]]; then
        continue
    fi

    count=0
    lines=()
    while IFS= read -r line; do
      echo "$line"
      grep -- "$line" "./get_directories_patterns_test/pw_${domain}.txt" > "wordlist_${domain}_${count}.txt"
      ((count++))
      lines+=("$line")
    done < <(cat ./get_directories_patterns_test/pw_${domain}.txt | cut -d / -f -2 | sort -u | sed 's|$|/|')

    # exit

    rm ./get_directories_patterns_test/pw_${domain}.txt

    for line in "${lines[@]}"; do
        echo "${line}PAYLOADDDD" | anew -q ./get_directories_patterns_test/pw_${domain}.txt
    done

    for file in wordlist_${domain}_*; do
        # echo $file
        file=$(echo $file | sed 's|.txt$||g')
        # echo $file
        # exit
        get_dirs $file
        get_dirs $file
        get_dirs $file
        get_dirs $file

    done

done


kill "$rota_pid"

for file in ./get_directories_patterns_test/pw_*; do
    # Step 1: remove lines starting with /PAYLOADDDD
    grep -v '^/PAYLOADDDD' "$file" | grep /PAYLOADDDD > "${file}.tmp"

    # Step 2: loop until no change in checksum
    while true; do
        old_checksum=$(md5sum "${file}.tmp" | awk '{print $1}')
        sed 's|PAYLOADDDD/PAYLOADDDD|PAYLOADDDD|g' "${file}.tmp" | grep -v '^//PAYLOADDDD$' > "${file}.tmp.new"
        new_checksum=$(md5sum "${file}.tmp.new" | awk '{print $1}')
        if [[ "$old_checksum" == "$new_checksum" ]]; then
            break
        fi
        mv "${file}.tmp.new" | grep /PAYLOADDDD$ > "${file}.tmp"
    done

    # Step 3: sort uniquely and save final result
    sort -u "${file}.tmp.new" > "$file"

    domain=$(echo "$file" | awk 'match($0, /pw_(.*)\.txt/, a) { print a[1] }')

    cat "$file" | anew -q ./get_directories_patterns/pw_${domain}.txt

    # Clean up
    rm -f "${file}.tmp" "${file}.tmp.new"
done

rm -rf ./wordlist_*
