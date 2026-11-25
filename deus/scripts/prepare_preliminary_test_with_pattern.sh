
# handle_signal() {
#   echo "Caught signal: $1"
#   # Add your custom logic here (e.g., cleanup)
# #   exit 1
# }

# # Loop through all signals
# for sig in $(kill -l | tr ' ' '\n'); do
#     trap "handle_signal $sig" "$sig"
# done

pattern_type=$1
url_file=$2
existence_count=$3

rm preliminary_wordlist.txt potential_dir.txt pw_* pf_*
# cat <(awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_extractor_rust_output.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_extractor_rust_output.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_extractor_rust_output.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_extractor_rust_output.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt) | grep --text -v -F -i -f  /usr/share/seclists/Discovery/Web-Content/raft-large-extensions-lowercase.txt  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | grep --text -vE '^[0-9/]+$' | anew preliminary_wordlist.txt | anew -q potential_dir.txt

# cat <(awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt) | grep --text -v -F -i -f  /usr/share/seclists/Discovery/Web-Content/raft-large-extensions-lowercase.txt  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | grep --text -vE '^[0-9/]+$' | anew preliminary_wordlist.txt | anew -q potential_dir.txt

# cat <(awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt) | grep --text -v -F -i -f  /usr/share/seclists/Discovery/Web-Content/raft-large-extensions-lowercase.txt  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | grep --text -vE '^[0-9/]+$' | anew preliminary_wordlist.txt | anew -q potential_dir.txt

cat <(awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_extractor_rust_output.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_extractor_rust_output.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_extractor_rust_output.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt)  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9./_ -]' | grep --text -vE '^[0-9/]+$' | anew preliminary_wordlist.txt | anew -q potential_dir.txt

cat <(awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt)  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9./_ -]' | grep --text -vE '^[0-9/]+$' | anew preliminary_wordlist.txt | anew -q potential_dir.txt

cat <(awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../../extracted_paths_and_params/path_count.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt)  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9./_ -]' | grep --text -vE '^[0-9/]+$' | anew preliminary_wordlist.txt | anew -q potential_dir.txt


if [[ "$pattern_type" == "all" ]]; then
    cat potential_dir.txt | sed 's/$/\/PAYLOADDDD/g' | grep -v PAYLOADDDD/PAYLOADDDD > pw_all.txt
elif [[ "$pattern_type" == "specific" ]]; then

    # while IFS= read -r url_file_line; do
    #     unfurled=$(echo "$url_file_line" | unfurl domains)
    #     rg -F --text -l "$unfurled" ./../../active_crawling_and_spidering/ ./../../sources/ | xargs grep --text -lFf potential_dir.txt | xargs grep --text -F -L ": $unfurled" | xargs grep --text -F -L " http://$unfurled" | xargs grep --text -F -L " https://$unfurled" | grep -Fv -e path_extractor_rust_output.txt -e extracted_path_wordlist.txt -e /paths.txt | anew -q "pf_${unfurled}.txt"
    # done < "$url_file"

    cat "$url_file" | unfurl domains > unfurled_domains.txt
    cook -l: ./potential_dir.txt -p: ./unfurled_domains.txt p / l > all_patterns.txt
    while read -r path; do
        cat "$path" | rg --text -F -f ./all_patterns.txt | anew -q all_matched_patterns.txt
    done < <(find ./../../extracted_paths_and_params/)

    assign_patterns_by_url() {
        pattern_line=$1
        url_file=$2
        
        while IFS= read -r url_file_line; do
            unfurled=$(echo "$url_file_line" | unfurl domains)
            
            # while read -r path; do
            if rg --text --pcre2 -q -- "$unfurled/${pattern_line}(?![[:alnum:]?#])" ./all_matched_patterns.txt; then
                
                flock -x /tmp/pw_lock -c "echo \"$pattern_line/PAYLOADDDD\" | anew -q \"pw_${unfurled}.txt\""
                
                break
            fi
            # done < <(find ./../../extracted_paths_and_params/)

        done < "$url_file"
    }
    export -f assign_patterns_by_url

    assign_patterns_by_existence() {
        pattern_line=$1
        url_file=$2
        existence_count=$3
        
        while IFS= read -r host; do
            pattern_count=$(grep -R -xF -l "$pattern_line/PAYLOADDDD" ./pw_* | wc -l)
            
            if [ "$pattern_count" -gt "$existence_count" ]; then
                while read -r pw_file; do

                flock -x /tmp/mylock -c "grep -Fxv \"$pattern_line/PAYLOADDDD\" \"$pw_file\" > temp && mv temp \"$pw_file\""

                done < <(grep -R -xF -l "$pattern_line/PAYLOADDDD" ./pw_*)
                break

            else
                echo "$pattern_line/PAYLOADDDD" | anew -q "pw_${host}.txt"
            fi

        done < <(rg -F --text -l "$pattern_line" ./../../active_crawling_and_spidering/ ./../../sources/ | xargs dirname | rev | cut -d / -f1 | rev | sort -u | grep -Fx -f <(cat $url_file | unfurl domains) )

    }
    export -f assign_patterns_by_existence
    
    # parallel -j "$(nproc)" assign_patterns_by_existence :::: ./potential_dir.txt
    if [ "$existence_count" -gt 0 ]; then
        # if [[ ! -s "log.txt" ]]; then
        echo -e "Seq\tHost\tStarttime\tJobRuntime\tSend\tReceive\tExitval\tSignal\tCommand" > log.txt
        # fi

        last_line_count=$(wc -l < log.txt)

        while true; do

            parallel -j "$(nproc)" --resume --joblog log.txt assign_patterns_by_existence {} "$url_file" "$existence_count" :::: ./potential_dir.txt
            parallel -j "$(nproc)" --resume-failed --joblog log.txt assign_patterns_by_existence {} "$url_file" "$existence_count" :::: ./potential_dir.txt

            new_line_count=$(wc -l < log.txt)

            if [[ "$new_line_count" -eq "$last_line_count" ]]; then
                echo "No new jobs added. Done."
                break
            fi

            # Update last_line_count for next iteration
            last_line_count=$new_line_count
        done

        # parallel -j "$(nproc)" assign_patterns_by_existence {} "$url_file" "$existence_count" :::: ./potential_dir.txt
    fi

    # if [[ ! -s "log.txt" ]]; then
    echo -e "Seq\tHost\tStarttime\tJobRuntime\tSend\tReceive\tExitval\tSignal\tCommand" > log.txt
    # fi

    last_line_count=$(wc -l < log.txt)

    while true; do

        parallel -j "$(nproc)" --resume --joblog log.txt assign_patterns_by_url {} "$url_file" :::: ./potential_dir.txt
        parallel -j "$(nproc)" --resume-failed --joblog log.txt assign_patterns_by_url {} "$url_file" :::: ./potential_dir.txt

        new_line_count=$(wc -l < log.txt)

        if [[ "$new_line_count" -eq "$last_line_count" ]]; then
            echo "No new jobs added. Done."
            break
        fi

        # Update last_line_count for next iteration
        last_line_count=$new_line_count
    done

    # parallel -j "$(nproc)" assign_patterns_by_url {} "$url_file" :::: ./potential_dir.txt
fi

# exit
# cat <(grep / <(cat ./../../extracted_paths_and_params/extracted_path_and_param_wordlist.txt ./../../extracted_paths_and_params/extracted_path_wordlist.txt )) <( grep / <(cat ./../../extracted_paths_and_params/extracted_path_and_param_wordlist.txt ./../../extracted_paths_and_params/extracted_path_wordlist.txt ) | unfurl paths) | rg --text -e '^.{0,200}$' | rg --text -e '^[^/]*(/[^/]*){0,6}$' | cut -d ? -f -1 | sort -u > wordlist_for_path_pattern_prepare.txt
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
# mkdir wordlist_for_param_pattern_prepare

# for list_split in 5000 7500; do
#     split -l $list_split wordlist_for_param_pattern_prepare.txt ./wordlist_for_param_pattern_prepare/wordlist_for_param_pattern_prepare_ --additional-suffix=.txt

#     for file in wordlist_for_param_pattern_prepare/*; do
#       ~/scripts/path_pattern_prepare "$file" | anew -q param_based_path_pattern_prepare_output.txt
#     done

# done


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
