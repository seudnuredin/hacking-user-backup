# Queries


# handle_signal() {
#   echo "Caught signal: $1"
#   # Add your custom logic here (e.g., cleanup)
# #   exit 1
# }

# # Loop through all signals
# for sig in $(kill -l | tr ' ' '\n'); do
#     trap "handle_signal $sig" "$sig"
# done


cat ./../extracted_paths_and_params/extracted_path_and_param_wordlist.txt  | grep -i --text -f <(sed 's/^/\\./' /usr/share/seclists/Fuzzing/file-extensions-all-cases.txt | sed 's/$/$/' | grep -i -F -v -e .css -e .jpeg -e .jpg -e .png -e .svg -e .gif -e .tiff -e .tif -e .webp -e .bmp -e .ico -e .ttf -e .woff -e .woff2 -e .otf -e .mp3 -e .wav -e .webm -e .aac -e .ogg -e .au -e .aiff -e .aif -e .mp4 -e .mpeg -e .mpg -e .ogv -e .ts -e .avi -e .flv -e .wmv -e .mov -e .3gp -e .eot -e .apk -e .bin -e .exe -e .msi -e .dll -e .pdf -e .application -e .pjpeg) | awk '!seen[$0]++' > raw_queries.txt


# cat ./../extracted_paths_and_params/extracted_path_wordlist.txt <( cat ./../extracted_paths_and_params/extracted_path_wordlist.txt | unfurl paths) | rg --text -e '^.{0,200}$' | rg --text -e '^[^/]*(/[^/]*){0,6}$' | cut -d ? -f -1 | sort -u > wordlist_for_path_pattern_prepare.txt
# ~/scripts/path_pattern_prepare wordlist_for_path_pattern_prepare.txt > path_pattern_prepare_output.txt
cat ./../extracted_paths_and_params/extracted_path_wordlist.txt <( cat ./../extracted_paths_and_params/extracted_path_wordlist.txt | unfurl paths) | rg --text -e '^.{0,200}$' | rg --text -e '^[^/]*(/[^/]*){0,6}$' | cut -d ? -f -1 | sort -u > wordlist_for_path_pattern_prepare.txt

output_dir="wordlist_for_path_pattern_prepare"
mkdir -p "$output_dir"
input_file="wordlist_for_path_pattern_prepare.txt"

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

for file in $output_dir/*; do
  ~/scripts/path_pattern_prepare "$file" | anew -q path_pattern_prepare_output.txt
done

# for list_split in 5000 7500; do
#     split -l $list_split wordlist_for_path_pattern_prepare.txt ./wordlist_for_path_pattern_prepare/wordlist_for_path_pattern_prepare_ --additional-suffix=.txt

#     for file in wordlist_for_path_pattern_prepare/*; do
#       ~/scripts/path_pattern_prepare "$file" | anew -q path_pattern_prepare_output.txt
#     done

# done

sort -nr -k1,1 path_pattern_prepare_output.txt | awk '{print $2}' | sed 's:^/*::' | cut -d / -f -1  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' > subpaths.txt
sort -nr -k1,1 path_pattern_prepare_output.txt | awk '{print $2}' | sed 's:^/*::' | cut -d / -f -2  | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | awk '$1 >= 2' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | awk '{print $2}' | anew -q subpaths.txt
while IFS= read -r k; do grep --text -e "^$k/" -e "^/$k/" ./../extracted_paths_and_params/extracted_path_and_param_wordlist.txt | awk '!/\/$/ { print length, $0 }'  | sort -n | head -n2 | cut -d' ' -f2-; done < subpaths.txt | anew -q raw_queries.txt
while IFS= read -r k; do grep --text -e "^$k/" -e "^/$k/" ./../extracted_paths_and_params/extracted_path_and_param_wordlist.txt | awk '/\/$/ { print length, $0 }'  | sort -n | head -n1 | cut -d' ' -f2- ; done < subpaths.txt | anew -q raw_queries.txt
while IFS= read -r k; do grep --text -e "^$k/" -e "^/$k/" ./../extracted_paths_and_params/extracted_path_and_param_wordlist.txt | awk -F. '!seen[$NF]++ && NF > 1'  | sort -n | head -n1 | cut -d' ' -f2- ; done < subpaths.txt | anew -q raw_queries.txt


# cat ./../extracted_paths_and_params/extracted_param_wordlist.txt | grep -E '^[A-Za-z_-]+$' > wordlist_for_param_pattern_prepare.txt
# ~/scripts/path_pattern_prepare wordlist_for_param_pattern_prepare.txt > param_based_path_pattern_prepare_output.txt
# sort -nr -k1,1 param_based_path_pattern_prepare_output.txt | awk '$1 && $2' | awk '$1 >= 2' | head -n 100 | awk '{print $2}' > subpaths2.txt
# while IFS= read -r k; do   [[ "$k" =~ ^~?PAYLOADDDD~?$ ]] && continue;   r=$(printf '%s\n' "$k" | sed -E 's/~?PAYLOADDDD~?/[A-Z_-]+[A-Za-z_-]+/g');   grep --text -E -e "^/?${r}(/|$)"        ./../extracted_paths_and_params/extracted_param_wordlist.txt     | head -n2; done < subpaths2.txt | anew queries_old.txt | anew -q queries.txt



# cat ./../active_crawling_and_spidering/*/index.txt | awk '$3 != "(200" && $3 != "(OK)" && $4 != "OK)" { print $1}' | grep -vxF -f <( cat ./../active_crawling_and_spidering/*/index.txt  |  awk '$3 == "(200" || $3 == "(OK)" || $4 == "OK)" { print $1}') | xargs -I {} cat ./../active_crawling_and_spidering/{} 2>/dev/null | htmlq -t "*" | rg --text -e '^.{0,100}$' | awk '!seen[$0]++' | anew -q raw_queries.txt

# find ./../fuzz -type f | parallel -j"$(nproc)" 'jq empty "{}" >/dev/null 2>&1 && jq -r ".. | strings" "{}"' | awk '!seen[$0]++' | anew -q raw_queries.txt
# find ./../active_crawling_and_spidering -type f | parallel -j"$(nproc)" 'jq empty "{}" >/dev/null 2>&1 && jq -r ".. | strings" "{}"' | awk '!seen[$0]++' | anew -q raw_queries.txt
# find ./../fuzz -type f | parallel -j"$(nproc)" 'jq empty "{}" >/dev/null 2>&1 && jq -r ".. | strings" "{}"' | awk '!seen[$0]++' | tr ' ' '\n' | awk '!seen[$0]++' | anew -q raw_queries.txt
# find ./../active_crawling_and_spidering -type f | parallel -j"$(nproc)" 'jq empty "{}" >/dev/null 2>&1 && jq -r ".. | strings" "{}"' | awk '!seen[$0]++' | tr ' ' '\n' | awk '!seen[$0]++' | anew -q raw_queries.txt
# find ./../fuzz -type f | parallel -j"$(nproc)" 'htmlq -t "*" "{}" 2>/dev/null || true' | awk '!seen[$0]++' | anew -q raw_queries.txt


cat raw_queries.txt | grep  -v  '[^A-Za-z0-9(.:_ /-]'  | tr ':' '\n' | sed 's/^ *//' | sed 's/ *$//' | grep -ivF -f <(cat ./../../domains.txt | unfurl format %r ) | grep -v -e GET -e POST -e PUT -e PATCH -e DELETE | sed -E 's/\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b//g' | sed '/^$/d' | awk 'length($0) > 4' | sort -fu > rectified_queries.txt
cat rectified_queries.txt | anew queries_old.txt | anew -q queries.txt


# Special Queries

cat ./../active_crawling_and_spidering/*/index.txt | awk '$3 != "(200" && $3 != "(OK)" && $4 != "OK)" { print $1}' | grep -vxF -f <( cat ./../active_crawling_and_spidering/*/index.txt  |  awk '$3 == "(200" || $3 == "(OK)" || $4 == "OK)" { print $1}') | xargs -I {} cat ./../active_crawling_and_spidering/{} 2>/dev/null | htmlq -t "*" | rg --text -e '^.{0,100}$' | awk '!seen[$0]++' | anew -q raw_special_queries.txt

find ./../fuzz -type f | parallel -j"$(nproc)" 'jq empty "{}" >/dev/null 2>&1 && jq -r ".. | strings" "{}"' | awk '!seen[$0]++' | anew -q raw_special_queries.txt

find ./../active_crawling_and_spidering -type f | parallel -j"$(nproc)" 'jq empty "{}" >/dev/null 2>&1 && jq -r ".. | strings" "{}"' | awk '!seen[$0]++' | anew -q raw_special_queries.txt
find ./../fuzz -type f | parallel -j"$(nproc)" 'jq empty "{}" >/dev/null 2>&1 && jq -r ".. | strings" "{}"' | awk '!seen[$0]++' | tr ' ' '\n' | awk '!seen[$0]++' | anew -q raw_special_queries.txt
find ./../active_crawling_and_spidering -type f | parallel -j"$(nproc)" 'jq empty "{}" >/dev/null 2>&1 && jq -r ".. | strings" "{}"' | awk '!seen[$0]++' | tr ' ' '\n' | awk '!seen[$0]++' | anew -q raw_special_queries.txt
find ./../fuzz -type f | parallel -j"$(nproc)" 'htmlq -t "*" "{}" 2>/dev/null || true' | awk '!seen[$0]++' | anew -q raw_special_queries.txt

cat raw_special_queries.txt | grep  -v  '[^A-Za-z0-9(.:_ /-]'  | tr ':' '\n' | sed 's/^ *//' | sed 's/ *$//' | grep -ivF -f <(cat ./../../domains.txt | unfurl format %r ) | grep -v -e GET -e POST -e PUT -e PATCH -e DELETE | sed -E 's/\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b//g' | sed '/^$/d' | awk 'length($0) > 4' | sort -fu > rectified_special_queries.txt

awk '
BEGIN {
  # Load dictionary words into an array "dict"
  while ((getline word < "/usr/share/dict/words") > 0) {
    dict[tolower(word)] = 1
  }
  close("/usr/share/dict/words")
}
{
  found_non_dict = 0
  for (i = 1; i <= NF; i++) {
    # Remove non-alpha chars from the word
    w = tolower($i)
    gsub(/[^a-z]/, "", w)
    if (w != "" && !(w in dict)) {
      found_non_dict = 1
      break
    }
  }
  if (found_non_dict) print
}' <(cat rectified_special_queries.txt | grep -Fv ' ' ) > rectified_special_queries_2.txt


cat rectified_special_queries.txt | grep -F ' ' | anew -q rectified_special_queries_2.txt

mv rectified_special_queries_2.txt rectified_special_queries.txt

cat rectified_special_queries.txt | anew special_queries_old.txt > special_queries.txt



# bash ~/scripts/get_banner.sh

# cat banners.txt | anew banner_queries_old.txt > banner_queries.txt
# cat banners.txt | tr ' ' '\n' | anew banner_queries_old.txt | anew -q banner_queries.txt

