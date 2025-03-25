import os
import time
import shutil
import subprocess
import pandas as pd
import csv
from collections import defaultdict
import argparse

# Configuration
wrk_path = "../../wrk2/wrk"  # Path to wrk2
script_path = "./../wrk2/scripts/social-network/compose-post.lua"
url = "http://172.18.0.2:32721/wrk2-api/post/compose"
threads = 1 #Provar tipo t 10 i c 50
connections = 1

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Load testing script for social network.')
parser.add_argument('--query_rate', type=int, default=40, help='Max requests per second')
args = parser.parse_args()
query_rate = args.query_rate

steady_state_duration = 50  # Maintain max req/s for 5 minutes


def get_unique_filename(base_name="test"):
    """Generate a unique filename with a timestamp to prevent overwriting."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    new_name = f"{base_name}_{timestamp}.txt"
    return new_name

def check_and_rename_file(original_file="0.txt"):
    """Check if the file exists and rename it to avoid overwriting."""
    if os.path.exists(original_file):
        new_filename = get_unique_filename()
        shutil.move(original_file, new_filename)
        print(f"[INFO] WRK2 latency file renamed: {original_file} -> {new_filename}")
    else:
        print("[INFO] No WRK2 output file found.")


# Steady State Phase
print(f"\n🔥 Maintaining steady state at {query_rate} req/s for {steady_state_duration/60} minutes...")
command = f"{wrk_path} -D exp -t {threads} -c {connections} -d {steady_state_duration}s -P -s {script_path} {url} --timeout 1s -R {query_rate}"
print(command)
result = subprocess.run(command, shell=True, capture_output=True, text=True)

#time.sleep(cooldown)
check_and_rename_file()

print(f"\n🎯 Test completed!")
