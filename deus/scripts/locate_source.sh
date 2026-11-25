modify_at="$1"

rm pairs.txt log.txt

# handle_signal() {
#   echo "Caught signal: $1"
#   # Add your custom logic here (e.g., cleanup)
# #   exit 1
# }

# # Loop through all signals
# for sig in $(kill -l | tr ' ' '\n'); do
#     trap "handle_signal $sig" "$sig"
# done

# set -euo pipefail
# trap '' SIGHUP
# trap 'echo "❌ Error on line $LINENO: $BASH_COMMAND (exit code: $?)" >> errors.log' ERR

# 1. Export the function to process a domain and find matches
cat ./../domains.txt | unfurl format .%r. | awk '!seen[$0]++' > ./domains.txt

# find ./active_crawling_and_spidering/ ./sources/source* -type f | while read -r file; do
#   dirname "$file"
# done | sort -u | grep -F -f ./domains.txt || true | while read -r dir; do
#     echo "Processing dir: $dir"
#     (
#     cd "$dir" && 
#     bash -c "~/scripts/path_extractor_rust ./ > path_extractor_rust_output.txt" &&
#     awk '{print $2}' path_extractor_rust_output.txt | rg --text -e '^.{1,400}$' | anew -q extracted_path_wordlist.txt &&
#     cat extracted_path_wordlist.txt <( cat extracted_path_wordlist.txt | unfurl paths) <( cat extracted_path_wordlist.txt | grep --text '\/' | sed 's|\\/|/|g') | rg --text -e '^.{0,200}$'  | anew -q crude_extracted_path_wordlist.txt &&
#     cat <(cat crude_extracted_path_wordlist.txt | grep --text -v -i -e '^http://' -e '^https://' | perl -ne 'chomp; s{(?<=/)([^/]+)(?=/|$)}{ $1 =~ /[^A-Za-z0-9._-]/ ? '"$modify_at"' : $1 }ge; print "$_\n"') <( cat crude_extracted_path_wordlist.txt | sed "s/\/PAYLOADDDD\//\/$modify_at\//g" | sed "s/\/EXPR\//\/$modify_at\//g") | grep -v --text "[^a-zA-Z0-9?\./&%_=-]"  | grep -Fv --text -e /PAYLOADDDD/ -e /EXPR/ | python3 -c "import sys, urllib.parse; print(urllib.parse.unquote(sys.stdin.read()), end='')" | anew -q paths.txt ;
#     ~/scripts/param_extractor $(find ./../sources/ ./../active_crawling_and_spidering/ -maxdepth 1 -type d  | grep -v './$' | tr  '\n' ' ') >> extracted_param_wordlist.txt &&
#     awk '!seen[$0]++' extracted_param_wordlist.txt > extracted_param_wordlist.txt.new &&
#     mv extracted_param_wordlist.txt.new extracted_param_wordlist.txt
    
#     )
# done

while read -r dir; do
    echo "Processing dir: $dir"
    (
        cd "$dir" && 
    bash -c "~/scripts/path_extractor_rust ./ > path_extractor_rust_output.txt" &&
    awk '{print $2}' path_extractor_rust_output.txt | rg --text -e '^.{1,400}$' | anew -q extracted_path_wordlist.txt &&
    cat extracted_path_wordlist.txt <( cat extracted_path_wordlist.txt | unfurl paths) <( cat extracted_path_wordlist.txt | grep --text '\/' | sed 's|\\/|/|g') | rg --text -e '^.{0,200}$'  | anew -q crude_extracted_path_wordlist.txt &&
    cat <(cat crude_extracted_path_wordlist.txt | grep --text -v -i -e '^http://' -e '^https://' | perl -ne 'chomp; s{(?<=/)([^/]+)(?=/|$)}{ $1 =~ /[^A-Za-z0-9._-]/ ? '"$modify_at"' : $1 }ge; print "$_\n"') <( cat crude_extracted_path_wordlist.txt | sed "s/\/PAYLOADDDD\//\/$modify_at\//g" | sed "s/\/EXPR\//\/$modify_at\//g") | grep -v --text "[^a-zA-Z0-9?\./&%_=-]"  | grep -Fv --text -e /PAYLOADDDD/ -e /EXPR/ | python3 -c "import sys, urllib.parse; print(urllib.parse.unquote(sys.stdin.read()), end='')" | anew -q paths.txt ;
    ~/scripts/param_extractor ./ >> extracted_param_wordlist.txt &&
    awk '!seen[$0]++' extracted_param_wordlist.txt > extracted_param_wordlist.txt.new &&
    mv extracted_param_wordlist.txt.new extracted_param_wordlist.txt
    )
done < <( cat <(
    find ./active_crawling_and_spidering/ ./sources/source* -type f \
    | while read -r file; do
        dirname "$file"
    done \
    | sort -u \
    | grep -F -f ./domains.txt || true
) <( find ./sources/apk -maxdepth 1 -type d ) )

# exit

declare -A line_counts  # associative array to store line counts

while IFS= read -r paths_file; do
    i_dirname=$(dirname "$paths_file" | rev | cut -d / -f1 | rev)
    count=$(wc -l < "$paths_file")

    if [[ ! ${line_counts[$i_dirname]+_} ]]; then
        line_counts["$i_dirname"]=$count
    else
        if (( count > ${line_counts[$i_dirname]:-0} )); then
            line_counts["$i_dirname"]=$count
        fi
    fi
done < <(find ./active_crawling_and_spidering/ ./sources/source* ./sources/apk -type f | grep '/paths.txt$')


export OUTFILE=./output.json
test -f "$OUTFILE" || echo '{}' > "$OUTFILE"

find_paths_for_domain() {
    # echo "domain=$1"
    domain="$1"
    unfurled=$(echo "$domain" | unfurl domains)

    # Check if the domain is in domains.txt once
    if echo "$unfurled" | grep -Fq -f ./domains.txt; then
        # echo "unfurled=$unfurled"
        while read -r path; do 
            # echo "PATH=$path"
            if [[ "$path" == *"/apk/"* ]]; then
            #   i_dirname=$(echo "$path" | sed -n 's|.*\/apk\/\([^/]*\).*|\1|p')
                echo "$unfurled|||$path"
            else
            #   i_dirname=$(dirname "$path" | rev | cut -d / -f1 | rev)
              if echo "$path" | xargs dirname | rev | cut -d / -f1 | rev | grep -Fq -f ./domains.txt; then
                  echo "$unfurled|||$path"
              fi
            fi
            
        done < <(find ./sources ./active_crawling_and_spidering -type f \( -name paths.txt -o -name extracted_param_wordlist.txt \) -exec rg -i --text -F -l -- "$unfurled" {} + )
    fi
}
export -f find_paths_for_domain

# 2. Use GNU parallel to process all domains concurrently

# Initialize joblog if missing or empty
# if [[ ! -s "log.txt" ]]; then
echo -e "Seq\tHost\tStarttime\tJobRuntime\tSend\tReceive\tExitval\tSignal\tCommand" > log.txt
# fi

last_line_count=$(wc -l < log.txt)

while true; do

    parallel -j "$(nproc)" --resume --joblog log.txt find_paths_for_domain :::: ./all_subtarget_domains.txt >> pairs.txt
    parallel -j "$(nproc)" --resume-failed --joblog log.txt find_paths_for_domain :::: ./all_subtarget_domains.txt >> pairs.txt

    # exit

    new_line_count=$(wc -l < log.txt)

    if [[ "$new_line_count" -eq "$last_line_count" ]]; then
        echo "No new jobs added. Done."
        break
    fi

    # Update last_line_count for next iteration
    last_line_count=$new_line_count
done

# 2. Process each domain|||path pair
while IFS= read -r line; do
    domain=$(echo "$line" | cut -d '|' -f1)
    path=$(echo "$line" | cut -d '|' -f4-)

    if [[ "$path" == *"/apk/"* ]]; then
      i_dirname=$(echo "$path" | sed -n 's|.*\/apk\/\([^/]*\).*|\1|p')
    else
      i_dirname=$(dirname "$path" | rev | cut -d / -f1 | rev)
    fi

    line_count="${line_counts[$i_dirname]}"
    if ! [[ "$line_count" =~ ^[0-9]+$ ]]; then
        line_count=0
    fi

    # echo "key=$i_dirname, value=$domain, lines=$line_count"

    tmpfile=$(mktemp)
    jq --arg key "$i_dirname" --arg value "$domain" --argjson lines "$line_count" '
  if has($key) then
    .[$key].domains += [$value] | .[$key].domains |= unique
  else
    .[$key] = { domains: [$value] }
  end | .[$key].lines = $lines
' < "$OUTFILE" > "$tmpfile" && mv "$tmpfile" "$OUTFILE" 

done < pairs.txt
