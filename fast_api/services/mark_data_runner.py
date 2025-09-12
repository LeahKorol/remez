from pipeline.mark_data import mark_data
import pandas as pd
import pickle
import os

def run_mark_data(df_drug, df_reac, df_demo, config_items, dir_out):
    """
    Runs mark_data on the given dataframes and saves output as pickle
    """
    df_marked = mark_data(df_drug=df_drug, df_reac=df_reac, df_demo=df_demo, config_items=config_items)
    
    os.makedirs(dir_out, exist_ok=True)
    output_file = os.path.join(dir_out, "marked_data.pkl")
    with open(output_file, "wb") as f:
        pickle.dump(df_marked, f)
    
    return df_marked
