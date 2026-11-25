path_file="$1"

# Step 1: Generate subpaths from all paths
declare -A seen
subpaths=()

while IFS= read -r path; do
    IFS='/' read -ra parts <<< "${path#/}"
    for part in "${parts[@]}"; do
        if [[ -n "$part" && -z "${seen[$part]}" ]]; then
            subpaths+=("$part")
            seen["$part"]=1
        fi
    done
done < "$path_file"

# Step 2: function for parallel search
search_subpath() {
    local dir="$1"
    local subpath="$2"
    rg -F --json --text "$subpath/" "$dir" | jq -c 'select(.type=="match") | {path: .data.path.text, match: .data.submatches[].match.text}'
    rg -F --json --text "/$subpath" "$dir" | jq -c 'select(.type=="match") | {path: .data.path.text, match: .data.submatches[].match.text}'
}

export -f search_subpath

echo -e "Seq\tHost\tStarttime\tJobRuntime\tSend\tReceive\tExitval\tSignal\tCommand" > log.txt

last_line_count=$(wc -l < log.txt)

while true; do

    parallel -j "$(nproc)" --resume --joblog log.txt  search_subpath ./../sources/ ::: "${subpaths[@]}"
    parallel -j "$(nproc)" --resume-failed --joblog log.txt  search_subpath ./../sources/ ::: "${subpaths[@]}"


    new_line_count=$(wc -l < log.txt)

    if [[ "$new_line_count" -eq "$last_line_count" ]]; then
        echo "No new jobs added. Done."
        break
    fi

    # Update last_line_count for next iteration
    last_line_count=$new_line_count
done

echo -e "Seq\tHost\tStarttime\tJobRuntime\tSend\tReceive\tExitval\tSignal\tCommand" > log.txt

last_line_count=$(wc -l < log.txt)

while true; do

    parallel -j "$(nproc)" --resume --joblog log.txt  search_subpath ./../active_crawling_and_spidering/ ::: "${subpaths[@]}"
    parallel -j "$(nproc)" --resume-failed --joblog log.txt  search_subpath ./../active_crawling_and_spidering/ ::: "${subpaths[@]}"


    new_line_count=$(wc -l < log.txt)

    if [[ "$new_line_count" -eq "$last_line_count" ]]; then
        echo "No new jobs added. Done."
        break
    fi

    # Update last_line_count for next iteration
    last_line_count=$new_line_count
done


for f in ./../active_crawling_and_spidering/*traffic*.tar.gz; 
do 
    # Extract and capture the top-level folder name
    extracted_dir=$(tar -tzf "$f" | head -1 | cut -f2 -d"/")

     # Skip if directory already exists in the file
    if grep -qxF "$extracted_dir" extracted_dirs.txt 2>/dev/null; then
        continue
    fi

    echo "$extracted_dir" | anew -q extracted_dirs.txt

    tar -xzf "$f" -C ./../active_crawling_and_spidering/
    
    echo -e "Seq\tHost\tStarttime\tJobRuntime\tSend\tReceive\tExitval\tSignal\tCommand" > log.txt

    last_line_count=$(wc -l < log.txt)

    while true; do

        parallel -j "$(nproc)" --resume --joblog log.txt  search_subpath "./../active_crawling_and_spidering/$extracted_dir" ::: "${subpaths[@]}"
        parallel -j "$(nproc)" --resume-failed --joblog log.txt  search_subpath "./../active_crawling_and_spidering/$extracted_dir" ::: "${subpaths[@]}"

        new_line_count=$(wc -l < log.txt)

        if [[ "$new_line_count" -eq "$last_line_count" ]]; then
            echo "No new jobs added. Done."
            break
        fi

        # Update last_line_count for next iteration
        last_line_count=$new_line_count
    done

    # Delete extracted folder
    find ./../active_crawling_and_spidering -maxdepth 1 | grep -v ^./active_crawling_and_spidering$ | grep -Fv .tar.gz | grep -F -e main_ -e sub_ | xargs rm -rf
    
done

