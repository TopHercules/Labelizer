import os
import pandas as pd

directory = './Data'
header = ['TAG', 'TS', 'ax', 'ay', 'az']

for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path, header=None)
        # print(df.head(1).values[0])
        if df.head(1).values[0][0] == 'TAG':
            continue
        df.columns = header
        df.to_csv(file_path, index=False)