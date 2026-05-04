import pandas as pd

def export_to_csv(curves, filepath):
    """Exports structured curve data directly to a CSV file."""
    df_dict = {}
    for name, data in curves.items():
        df_dict[f"{name}_X"] = pd.Series(data['x'])
        df_dict[f"{name}_Y"] = pd.Series(data['y'])
    df = pd.DataFrame(df_dict)
    df.to_csv(filepath, index=False)
