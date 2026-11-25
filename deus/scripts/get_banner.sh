
rota --config /home/deus/documents/rota_config.yml -p 9555 > /dev/null 2>&1 &
rota_pid=$!

# bash ~/scripts/directory_based_urls_extraction.sh ./../path_brute_force/* 

cat ./../hosts.txt ./../path_brute_force/path_brute_force_with_pattern/all_directories.txt | sort -u > urls.txt

~/scripts/wappalyzer -file=./urls.txt -proxy=http://127.0.0.1:9555 -rate 10 > banners_non_browser_based_output.txt

cat banners_non_browser_based_output.txt | grep -oP '"\K[^"]*(?=")' | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | anew -q banners.txt

wappalyzer -i ./urls.txt -t 10 > banners_browser_based_output.txt

cat banners_browser_based_output.txt |  grep -P '\x1b\[[0-9;]*[a-zA-Z]' | cut -d ' ' -f 2- | sed  '1d' | tr ',' '\n' | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' | anew -q banners.txt


cat banners.txt | anew banner_queries_old.txt > banner_queries.txt
cat banners.txt | tr ' ' '\n' | anew banner_queries_old.txt | anew -q banner_queries.txt
cat banners.txt | tr ':' '\n' | anew banner_queries_old.txt | anew -q banner_queries.txt

kill "$rota_pid"
