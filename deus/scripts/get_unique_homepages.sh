rate=$1


rm urls.txt method_and_url_file_*

nohup rota --config /home/deus/documents/rota_config.yml -p 9239 > /dev/null 2>&1 &
# Capture its PID
rota_pid=$!
cat ./../hosts.txt > unchecked_urls.txt

# -rate and -t can be 500 if there's no rate limit


extracts_paths_and_get_retest_urls() {

    cat ffuf_output.json | grep -F '"status":3' > ffuf_output_2.json
    jq -r .redirectlocation ./ffuf_output_2.json | awk '!seen[$0]++' | sed 's|/aaaaaaaa||g' | anew -q retest_urls.txt

    cat ffuf_output.json | grep -F '"status":502' -e '"status":503' > ffuf_output_2.json
    jq -r .url ./ffuf_output_2.json | awk '!seen[$0]++' | sed 's|/aaaaaaaa||g' | anew -q retest_urls.txt

    cat ffuf_output.json | grep -Fv -e '"status":502' -e '"status":503' > ffuf_output_2.json
    mv ffuf_output_2.json ffuf_output.json

    rm method_and_url_file_*
    bash ~/scripts/path_brute_force_output_reader.sh all all 3 ./ffuf_output.json
    cat method_and_url_file_* | awk '{print $2}' | sed 's|/aaaaaaaa||g' | anew urls_old.txt | anew -q urls.txt

}

ffuf -u "FUZZ" -timeout 30 -json -w unchecked_urls.txt -mc all -s -rate $rate -t $rate -X GET -H "User-Agent: Mozilla/5.0 Windows NT 10.0 Win64 AppleWebKit/537.36 Chrome/69.0.3497.100" -noninteractive -x http://127.0.0.1:9239 > ./ffuf_output.json


rm retest_urls.txt
extracts_paths_and_get_retest_urls

ffuf -u "FUZZ/aaaaaaaa" -timeout 30 -json -w unchecked_urls.txt -mc all -s -rate $rate -t $rate -X GET -H "User-Agent: Mozilla/5.0 Windows NT 10.0 Win64 AppleWebKit/537.36 Chrome/69.0.3497.100" -noninteractive -x http://127.0.0.1:9239 > ./ffuf_output.json

extracts_paths_and_get_retest_urls

for i in {1..5}
do

    cat retest_urls.txt | grep -F -f <(cat ./../../domains.txt | unfurl format .%r.) > unchecked_urls.txt

    ffuf -u "FUZZ" -timeout 30 -json -w unchecked_urls.txt -mc all -s -rate $rate -t $rate -X GET -H "User-Agent: Mozilla/5.0 Windows NT 10.0 Win64 AppleWebKit/537.36 Chrome/69.0.3497.100" -noninteractive -x http://127.0.0.1:9239 > ./ffuf_output.json
    
    rm retest_urls.txt
    extracts_paths_and_get_retest_urls
    
    ffuf -u "FUZZ/aaaaaaaa" -timeout 30 -json -w unchecked_urls.txt -mc all -s -rate $rate -t $rate -X GET -H "User-Agent: Mozilla/5.0 Windows NT 10.0 Win64 AppleWebKit/537.36 Chrome/69.0.3497.100" -noninteractive -x http://127.0.0.1:9239 > ./ffuf_output.json

    extracts_paths_and_get_retest_urls
    
done

kill "$rota_pid"
