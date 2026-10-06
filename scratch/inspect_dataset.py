import json
import pandas as pd

with open('IN-FINews  Dataset.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

df = pd.DataFrame(data)

with open('scratch/inspect_output_utf8.txt', 'w', encoding='utf-8') as f:
    f.write(f"Number of records: {len(df)}\n")
    f.write(f"Columns: {df.columns.tolist()}\n")
    f.write(f"Data types:\n{df.dtypes}\n")
    f.write(f"\nSample records:\n{df.head(2).to_dict(orient='records')}\n")
    f.write(f"\nMissing values:\n{df.isnull().sum()}\n")
    f.write(f"\nUnique dates: {df['Date'].nunique()}\n")
    if 'Date' in df.columns:
        f.write(f"Date range: {df['Date'].min()} to {df['Date'].max()}\n")
    for col in df.columns:
        if col not in ['Content', 'Title', 'Description', 'URL']:
            f.write(f"Unique {col}: {df[col].nunique()}\n")
    f.write(f"\nDuplicate records: {df.duplicated().sum()}\n")
