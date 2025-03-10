import os
import time
import shutil
import subprocess
import pandas as pd
import csv
from collections import defaultdict

# Configuration
wrk_path = "../../wrk2/wrk"  # Path to wrk2
script_path = "./../wrk2/scripts/social-network/compose-post.lua"
url = "http://172.18.0.2:32684/wrk2-api/post/compose"
threads = 1
connections = 1
duration = 60  # Each test duration in seconds
ramp_up_start = 10  # Start at 10 req/s min for proper logging
ramp_up_end = 40  # Max req/s
step = 15  # Increase by 5 req/s each step
steady_state_duration = 300  # Maintain max req/s for 5 minutes
cooldown = 0  # Time to wait between tests


def get_unique_filename(base_name="test"):
    """Generate a unique filename with a timestamp to prevent overwriting."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    new_name = f"{base_name}_{timestamp}.txt"
    return new_name

def check_and_rename_file(original_file="u"):
    """Check if the file exists and rename it to avoid overwriting."""
    if os.path.exists(original_file):
        new_filename = get_unique_filename()
        shutil.move(original_file, new_filename)
        print(f"[INFO] WRK2 latency file renamed: {original_file} -> {new_filename}")
    else:
        print("[INFO] No WRK2 output file found.")


# # Run a slightly longer warm-up test to ensure WRK2 records latency stats
# print("\n⚡ Running Warm-up WRK2 test at 5 req/s to ensure latency logging works...")
# command = f"{wrk_path} -D exp -t {threads} -c {connections} -d {duration + 10}s -p -s {script_path} {url} -T 1s -R {ramp_up_start}"
# subprocess.run(command, shell=True, capture_output=True, text=True)

# # Ensure latency file exists and has data
# time.sleep(5)
# check_and_rename_file()

# Ramp Up Phase
for rps in range(ramp_up_start, ramp_up_end + step, step):
    print(f"\n🚀 Running WRK2 test at {rps} req/s (Ramp Up)...")
    
    command = f"{wrk_path} -D exp -t {threads} -c {connections} -d {duration}s -p -s {script_path} {url} -T 1s -R {rps}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    #print(f"\nCompleted {rps} req/s. Sleeping {cooldown}s before next step...")
    #time.sleep(cooldown)
    # Check and rename the newly generated WRK2 output file
    check_and_rename_file()

# Steady State Phase
print(f"\n🔥 Maintaining steady state at {ramp_up_end} req/s for {steady_state_duration/60} minutes...")
command = f"{wrk_path} -D exp -t {threads} -c {connections} -d {steady_state_duration}s -p -s {script_path} {url} -T 1s -R {ramp_up_end}"
result = subprocess.run(command, shell=True, capture_output=True, text=True)

#time.sleep(cooldown)
check_and_rename_file()
print(f"\nFinished steady state, starting to cooldown...")

# Cooldown Phase
for rps in range(ramp_up_end - step, ramp_up_start - step, -step):
    print(f"\n🔻 Running WRK2 test at {rps} req/s (Cooldown)...")
    
    command = f"{wrk_path} -D exp -t {threads} -c {connections} -d {duration}s -p -s {script_path} {url} -T 1s -R {rps}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    #print(f"\nCompleted {rps} req/s. Sleeping {cooldown}s before next step...")
    #time.sleep(cooldown)
    check_and_rename_file()


print(f"\n🎯 Test completed!")