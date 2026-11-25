

~/scripts/param_extractor $(find ./../sources/ ./../active_crawling_and_spidering/ -maxdepth 1 -type d  | grep --text -v './$' | tr  '\n' ' ') >> extracted_param_wordlist.txt
awk '!seen[$0]++' extracted_param_wordlist.txt > extracted_param_wordlist.txt.new
mv extracted_param_wordlist.txt.new extracted_param_wordlist.txt
~/scripts/key_value_pair_extractor $(find ./../sources/ ./../active_crawling_and_spidering/ -maxdepth 1 -type d  | grep --text -v './$' | tr  '\n' ' ') >> key_value_pair_extractor.jsonl
awk '!seen[$0]++' key_value_pair_extractor.jsonl > key_value_pair_extractor.jsonl.new
mv key_value_pair_extractor.jsonl.new key_value_pair_extractor.jsonl
~/scripts/path_extractor_rust $(find ./../sources/ ./../active_crawling_and_spidering/ -maxdepth 1 -type d  | grep --text -v './$' | tr  '\n' ' ') >> path_extractor_rust_output.txt
awk '!seen[$0]++' path_extractor_rust_output.txt > path_extractor_rust_output.txt.new
mv path_extractor_rust_output.txt.new path_extractor_rust_output.txt


for f in ./../active_crawling_and_spidering/*traffic*.tar.gz; 
do 
    # Extract and capture the top-level folder name
    extracted_dir=$(tar -tzf "$f" | head -1 | cut -f2 -d"/")

     # Skip if directory already exists in the file
    if grep --text -qxF "$extracted_dir" extracted_dirs.txt 2>/dev/null; then
        continue
    fi

    # echo "$extracted_dir" | anew -q extracted_dirs.txt

    echo "$extracted_dir" >> extracted_dirs.txt

    cat extracted_dirs.txt | awk '!seen[$0]++' > extracted_dirs.txt.new
    mv extracted_dirs.txt.new extracted_dirs.txt

    
    tar -xzf "$f" -C ./../active_crawling_and_spidering/


    ~/scripts/param_extractor $(find ./../active_crawling_and_spidering/*traffic* -maxdepth 1 -type d  | grep --text -v './$' | tr  '\n' ' ') >> extracted_param_wordlist.txt
    awk '!seen[$0]++' extracted_param_wordlist.txt > extracted_param_wordlist.txt.new
    mv extracted_param_wordlist.txt.new extracted_param_wordlist.txt

    ~/scripts/key_value_pair_extractor $(find ./../active_crawling_and_spidering/*traffic* -maxdepth 1 -type d  | grep --text -v './$' | tr  '\n' ' ') >> key_value_pair_extractor.jsonl
    awk '!seen[$0]++' key_value_pair_extractor.jsonl > key_value_pair_extractor.jsonl.new
    mv key_value_pair_extractor.jsonl.new key_value_pair_extractor.jsonl

    ~/scripts/path_extractor_rust $(find ./../active_crawling_and_spidering/*traffic* -maxdepth 1 -type d  | grep --text -v './$' | tr  '\n' ' ') >> path_extractor_rust_output.txt
 
    awk '!seen[$0]++' path_extractor_rust_output.txt > path_extractor_rust_output.txt.new
    mv path_extractor_rust_output.txt.new path_extractor_rust_output.txt

    # ~/scripts/path_pattern_prepare <(rev path_wordlist.txt) | grep -F -i PAYLOADDDD | awk '{print $2}' | awk -F'/PAYLOADDDD' '{print $1}' | rev | grep -Fv DDDDAOLYAP | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr  | anew path_count.txt | awk '{print $2}' | anew extracted_path_and_param_wordlist.txt | anew -q path_wordlist.txt

    # ~/scripts/path_pattern_prepare path_wordlist.txt | grep -F -i PAYLOADDDD | awk '{print $2}' | awk -F'/PAYLOADDDD' '{print $1}' | grep -Fv PAYLOADDDD | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr  | anew path_count.txt | awk '{print $2}' | anew extracted_path_and_param_wordlist.txt | anew -q path_wordlist.txt

    # find ./../active_crawling_and_spidering/ -mindepth 1 -maxdepth 1 -type d | grep _traffic_ | xargs rm -rf

    # cat ./../active_crawling_and_spidering/*traffic*/index.txt  | awk '{print $2}' | unfurl paths | anew -q extracted_path_wordlist.txt

    cat ./../active_crawling_and_spidering/*traffic*/index.txt  | awk '{print $2}' | unfurl paths | awk '!seen[$0]++' >> extracted_path_wordlist.txt
    cat extracted_path_wordlist.txt | awk '!seen[$0]++' > extracted_path_wordlist.txt.new
    mv extracted_path_wordlist.txt.new extracted_path_wordlist.txt

    # Delete extracted folder
    # rm -rf "./../active_crawling_and_spidering/$extracted_dir"
    find ./../active_crawling_and_spidering -maxdepth 1 | grep --text -v ^./active_crawling_and_spidering$ | grep --text -Fv .tar.gz | grep --text -F -e main_ -e sub_ | xargs rm -rf
    
done

generate_path_pattern() {
    output_dir="$2"
    mkdir -p "$output_dir"
    input_file="$1"
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
    for output_file in $output_dir/*; do
      ~/scripts/path_pattern_prepare "$output_file"
      rm $output_file
    done
}

awk '{print $2}' path_extractor_rust_output.txt | rg --text -e '^.{1,400}$' >> extracted_path_wordlist.txt
cat extracted_path_wordlist.txt | awk '!seen[$0]++' > extracted_path_wordlist.txt.new
mv extracted_path_wordlist.txt.new extracted_path_wordlist.txt

# bash ~/scripts/directory_based_urls_extraction.sh 500 all ./../path_brute_force/*
# cat urls.txt | anew -q ./extracted_path_wordlist.txt
# path only
cat extracted_path_wordlist.txt <( cat extracted_path_wordlist.txt | unfurl paths) <( cat extracted_path_wordlist.txt | sed 's|\\||g') <( cat extracted_path_wordlist.txt | sed 's|\\||g' | unfurl paths) | rg --text -e '^.{0,200}$'  >> crude_path_wordlist.txt
cat crude_path_wordlist.txt | awk '!seen[$0]++' > crude_path_wordlist.txt.new
mv crude_path_wordlist.txt.new crude_path_wordlist.txt

cat <(cat crude_path_wordlist.txt | grep --text -v -i -e '^http://' -e '^https://' | perl -ne 'chomp; s{(?<=/)([^/]+)(?=/|$)}{ $1 =~ /[^A-Za-z0-9._-]/ ? "150310241060" : $1 }ge; print "$_\n"') <( cat crude_path_wordlist.txt | sed 's/\/PAYLOADDDD\//\/150310241060\//g' | sed 's/\/EXPR\//\/150310241060\//g') | grep -v --text "[^a-zA-Z0-9?\./&%_=-]"  | grep -Fv --text -e /PAYLOADDDD/ -e /EXPR/ | python3 -c "import sys, urllib.parse; print(urllib.parse.unquote(sys.stdin.read()), end='')" >> path_wordlist.txt
cat path_wordlist.txt | awk '!seen[$0]++' > path_wordlist.txt.new
mv path_wordlist.txt.new path_wordlist.txt

# both path and param
# cat <(grep -E '^[A-Za-z0-9_-]+$' extracted_param_wordlist.txt)  extracted_path_wordlist.txt <( cat extracted_path_wordlist.txt | unfurl paths) <( cat extracted_path_wordlist.txt | sed 's|\\||g') <( cat extracted_path_wordlist.txt | sed 's|\\||g' | unfurl paths) | rg --text -e '^.{0,200}$'  | anew -q crude_extracted_path_and_param_wordlist.txt
# cat <(cat crude_extracted_path_and_param_wordlist.txt | grep --text -v -i -e '^http://' -e '^https://' | perl -ne 'chomp; s{(?<=/)([^/]+)(?=/|$)}{ $1 =~ /[^A-Za-z0-9._-]/ ? "150310241060" : $1 }ge; print "$_\n"') <( cat crude_extracted_path_and_param_wordlist.txt | sed 's/\/PAYLOADDDD\//\/150310241060\//g' | sed 's/\/EXPR\//\/150310241060\//g') | grep -v --text "[^a-zA-Z0-9?\./&%_=-]"  | grep -Fv --text -e /PAYLOADDDD/ -e /EXPR/ | python3 -c "import sys, urllib.parse; print(urllib.parse.unquote(sys.stdin.read()), end='')" | anew -q extracted_path_and_param_wordlist.txt
cat ./../passive_crawling/passively_crawled_urls_*.txt | unfurl paths | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -n  > ./../passive_crawling/passively_crawled_paths.txt
cat <(awk '{for (i=0; i<$1; i++) print $2}' ./../passive_crawling/passively_crawled_paths.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./../passive_crawling/passively_crawled_paths.txt | unfurl paths) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt) | grep --text -v -F -i -f  /usr/share/seclists/Discovery/Web-Content/raft-large-extensions-lowercase.txt  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9/_ -]' | grep --text -vE '^[0-9/]+$' >> path_wordlist.txt
cat path_wordlist.txt | awk '!seen[$0]++' > path_wordlist.txt.new
mv path_wordlist.txt.new path_wordlist.txt

awk '{print $2}' ./../passive_crawling/passively_crawled_paths.txt > ./../passive_crawling/passively_crawled_paths_unique.txt
new_passive_urls_count=$(ls ./../passive_crawling/passively_crawled_urls_*.txt | wc -l)
if [ ! -f "passive_urls_count.txt" ] || [ "$(cat passive_urls_count.txt)" -ne "$new_passive_urls_count" ]; then
    echo $new_passive_urls_count > passive_urls_count.txt
    bash ~/scripts/directory_based_path_extraction.sh 10 ./../passive_crawling/passively_crawled_paths_unique.txt
fi
cat preliminary_extracted_path_wordlist.txt >> path_wordlist.txt
cat path_wordlist.txt | awk '!seen[$0]++' > path_wordlist.txt.new
mv path_wordlist.txt.new path_wordlist.txt

rev path_wordlist.txt > rev_path_wordlist.txt
generate_path_pattern rev_path_wordlist.txt path_count | grep --text -F -i PAYLOADDDD | awk '{print $2}' | awk -F'/PAYLOADDDD' '{print $1}' | rev | grep --text -Fv DDDDAOLYAP | sed 's|^/||' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr  >> path_count.txt 
cat path_count.txt | awk '!seen[$0]++' > path_count.txt.new
mv path_count.txt.new path_count.txt

cat path_count.txt | awk '{print $2}' >> path_wordlist.txt
cat path_wordlist.txt | awk '!seen[$0]++' > path_wordlist.txt.new
mv path_wordlist.txt.new path_wordlist.txt

generate_path_pattern path_wordlist.txt path_count | grep --text -F -i PAYLOADDDD | awk '{print $2}' | awk -F'/PAYLOADDDD' '{print $1}' | grep --text -Fv PAYLOADDDD | sed 's|^/||' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | sort -nr >> path_count.txt
cat path_count.txt | awk '!seen[$0]++' > path_count.txt.new
mv path_count.txt.new path_count.txt

cat path_count.txt | awk '{print $2}' >> path_wordlist.txt
cat path_wordlist.txt | awk '!seen[$0]++' > path_wordlist.txt.new
mv path_wordlist.txt.new path_wordlist.txt


bash ~/scripts/directory_based_path_extraction.sh 250 path_wordlist.txt >  path_wordlist.txt.new
mv path_wordlist.txt.new path_wordlist.txt


cat <(awk '{for (i=0; i<$1; i++) print $2}' ./path_extractor_rust_output.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./path_extractor_rust_output.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./path_extractor_rust_output.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt)  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9./_ -]' | grep --text -vE '^[0-9/]+$' >> path_wordlist.txt

cat <(awk '{for (i=0; i<$1; i++) print $2}' ./../passive_crawling/passively_crawled_paths.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./../passive_crawling/passively_crawled_paths.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt)  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9./_ -]' | grep --text -vE '^[0-9/]+$' >> path_wordlist.txt

cat <(awk '{for (i=0; i<$1; i++) print $2}' ./path_count.txt) <( awk '{for (i=0; i<$1; i++) print $2}' ./path_count.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./path_count.txt | sed 's|\\||g' | unfurl paths) <( awk '{for (i=0; i<$1; i++) print $2}' ./path_count.txt | sed 's|\\||g' ) | rg --text -e '^[^/]*(/[^/]*){0,3}$' | grep --text -E '^.{2,}$' | sed 's:/*$::' | sed 's:^/*::' | awk '{ count[$0]++ } END { for (line in count) print count[line], line }' | grep --text -v null | awk -v min="2" '$1 >= min {print $2}' | grep --text -i -F -f <(grep --text -E '^.{2,}$' /usr/share/seclists/Discovery/Web-Content/common.txt)  | grep --text -E '^.{1,20}$' | grep --text -v -E '[^a-zA-Z0-9./_ -]' | grep --text -vE '^[0-9/]+$' >> path_wordlist.txt

awk '!seen[$0]++' path_wordlist.txt > path_wordlist.txt.uniq
mv path_wordlist.txt.uniq path_wordlist.txt

cat path_wordlist.txt >  extracted_path_and_param_wordlist.txt
grep --text -E '^[A-Za-z0-9_-]+$' extracted_param_wordlist.txt | grep --color=always --text -F -f <(cat ~/documents/words.txt | awk 'length($0) > 3' ) >> extracted_path_and_param_wordlist.txt
cat extracted_path_and_param_wordlist.txt | awk '!seen[$0]++' > extracted_path_and_param_wordlist.txt.new
mv extracted_path_and_param_wordlist.txt.new extracted_path_and_param_wordlist.txt



