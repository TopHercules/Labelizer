import os
import pandas as pd

directory = './Data'
header = ['MAC', 'TS', 'AX', 'AY', 'AZ']

for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path, header=None)
        df.columns = header
        df.to_csv(file_path, index=False)