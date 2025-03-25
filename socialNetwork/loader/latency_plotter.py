import os
import pandas as pd
import argparse

import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--folder', type=str, required=True, help='Path to the data folder')
args = parser.parse_args()

folder = args.folder

if not os.path.exists(folder):
    os.makedirs(folder)

for root, dirs, files in os.walk(folder):
    for file in files:
        if file.endswith('.txt'):
            file_path = os.path.join(root, file)
            data = pd.read_csv(file_path, header=None, names=['latency'])
            
            plt.figure()
            plt.plot(data.index, data['latency'])
            plt.xlabel('Sample Number')
            plt.ylabel('Data latency')
            plt.title(f'Latency Plot for {file}')
            
            plot_file_path = os.path.join(folder, f"{os.path.splitext(file)[0]}.png")
            plt.savefig(plot_file_path)
            plt.close()