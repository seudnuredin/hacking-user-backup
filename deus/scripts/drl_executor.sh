python3.7 ~/scripts/determine_rate_limit.py -rl 150 -mr 50 -uf ./all_hosts.txt
sleep 10m
cat all_hosts.txt | grep -Fvx -f <(jq -r '.url' rate_limit_config_min_*.jsonl ) > all_hosts_part.txt
python3.7 ~/scripts/determine_rate_limit.py -rl 49 -mr 10 -uf ./all_hosts_part.txt
sleep 10m
cat all_hosts.txt | grep -Fvx -f <(jq -r '.url' rate_limit_config_min_*.jsonl ) > all_hosts_part.txt
python3.7 ~/scripts/determine_rate_limit.py -rl 9 -mr 1 -uf ./all_hosts_part.txt

cat rate_limit_config_min_*.jsonl > rate_limit_config_all.jsonl
