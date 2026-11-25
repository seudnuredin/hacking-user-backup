import subprocess
import os

print("1. Perform CORS based search")
print("2. Collect sources")
print("3. Perform sources based search")

choice = int(input("Choice: "))

if choice == 1:
    subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/cors_based.py'],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a'),
                 preexec_fn=os.setpgrp
                 )
elif choice == 2:
    subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/source_collector.py'],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a'),
                 preexec_fn=os.setpgrp
                 )
elif choice == 3:
    subprocess.Popen(['bash', '-c',f'python3 /home/deus/scripts/source_based.py'],
                 stdout=open('logfile.log', 'a'),
                 stderr=open('logfile.log', 'a'),
                 preexec_fn=os.setpgrp
                 )
