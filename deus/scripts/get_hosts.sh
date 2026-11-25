
rate=$1


nohup rota --config /home/deus/documents/rota_config.yml -p 9239 > /dev/null 2>&1 &

rota_pid=$!


# cat ./all_subtarget_domains.txt | anew -q unchecked_hosts.txt

get_retest_hosts() {

    jq -r .redirectlocation <(grep -F '"status":3' $1) | awk '!seen[$0]++' | sed 's|/aaaaaaaa||g' > retest_hosts.txt

    jq -r .url <( grep -F -e '"status":502' $1 ) | awk '!seen[$0]++' | sed 's|/aaaaaaaa||g' | anew -q retest_hosts.txt

    # /home/deus/scripts/filter <(jq -r .url ./$1 | unfurl domains) unchecked_hosts.txt | awk '!seen[$0]++' | anew -q retest_hosts.txt

    /home/deus/scripts/filter <(jq -r .url ./$1 | sed 's|/aaaaaaaa||g' ) unchecked_hosts.txt | awk '!seen[$0]++' | anew -q retest_hosts.txt

    cat retest_hosts.txt | grep -F -f <(cat ./all_subtarget_domains.txt | unfurl format .%r.) | anew -q unchecked_hosts.txt

}

mkdir ./get_hosts
extract_hosts() {

    cp <(grep -Fv -e '"status":502' -e '"status":503' $1) $1.new
    mv $1.new $1

    rm ./get_hosts/method_and_url_file*
    (
      cd ./get_hosts || exit 1
      bash ~/scripts/path_brute_force_output_reader.sh all all 10 ./../$1
    )
    cat ./get_hosts/method_and_url_file* | awk '{print $2}' | unfurl format %s://%d%:%P | anew -q hosts.txt

}

rm unchecked_hosts.txt

cat ./all_hosts.txt | anew -q unchecked_hosts.txt

for i in {1..5}
do

    cp unchecked_hosts.txt unchecked_hosts_$i.txt

    ffuf -u "FUZZ" -timeout 10 -json -w unchecked_hosts_$i.txt -mc all -s -rate $rate -t $rate -X GET -H "User-Agent: Mozilla/5.0 Windows NT 10.0 Win64 AppleWebKit/537.36 Chrome/69.0.3497.100" -noninteractive -x http://127.0.0.1:9239 > ./ffuf_output_$i.json
    
    get_retest_hosts ./ffuf_output_$i.json
    extract_hosts ./ffuf_output_$i.json
    

done

rm unchecked_hosts.txt

cat ./all_hosts.txt | anew -q unchecked_hosts.txt

for i in {1..5}
do

    cp unchecked_hosts.txt unchecked_hosts_$i.txt
    
    ffuf -u "FUZZ/aaaaaaaa" -timeout 10 -json -w unchecked_hosts_$i.txt -mc all -s -rate $rate -t $rate -X GET -H "User-Agent: Mozilla/5.0 Windows NT 10.0 Win64 AppleWebKit/537.36 Chrome/69.0.3497.100" -noninteractive -x http://127.0.0.1:9239 > ./ffuf_output_$i.json

    get_retest_hosts ./ffuf_output_$i.json
    extract_hosts ./ffuf_output_$i.json
    
done


kill "$rota_pid"
