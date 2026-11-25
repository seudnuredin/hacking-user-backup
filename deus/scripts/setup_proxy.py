import subprocess
import socket
# smartproxy_proxy_server_ip = socket.gethostbyname("isp.smartproxy.com")
proxies = list()

with open('/home/deus/documents/proxies.txt') as proxy_file:
    for proxy in proxy_file:
        proxy = proxy.replace("\n","")
        if proxy != "":
            proxy = proxy.split(':')
            # proxies.append([smartproxy_proxy_server_ip,proxy[1]])
            proxies.append([proxy[0],proxy[1]])

proxied_massdns_content = ['#!/bin/bash']
proxychains_content = ['dynamic_chain','proxy_dns','remote_dns_subnet 224','tcp_read_time_out 15000','tcp_connect_time_out 8000','','[ProxyList]']

subprocess.run(f"rm /home/deus/scripts/proxied_massdns* /home/deus/documents/proxychains*.conf",shell=True)

for i in range(0,len(proxies)):
    #proxied_massdns2
    #proxychains1.conf
    with open(f"/home/deus/scripts/proxied_massdns{i}","w") as proxied_massdns:
        for line in proxied_massdns_content:
            proxied_massdns.write(line + "\n")
        proxied_massdns.write(f"proxychains4 -f /home/deus/documents/proxychains{i}.conf -q /usr/bin/massdns \"$@\""  + "\n")
        subprocess.run(f"chmod +x /home/deus/scripts/proxied_massdns{i}",shell=True)
    with open(f"/home/deus/documents/proxychains{i}.conf","w") as proxychains:
        for line in proxychains_content:
            proxychains.write(line + "\n")
        proxychains.write("http ip port".replace("ip",proxies[i][0]).replace("port",proxies[i][1]) + "\n")


