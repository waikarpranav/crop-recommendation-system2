import numpy as np
import pandas as pd

def engineer_features(data):
    """
    Create domain-informed features based on agricultural science.
    Supports both single dictionary (for API) and DataFrame (for training).
    """
    if isinstance(data, dict):
        # Convert dict to DataFrame for easier calculation
        df = pd.DataFrame([data])
        is_dict = True
    else:
        df = data.copy()
        is_dict = False

    # NPK Ratio (critical for crop nutrition balance)
    df['NPK_ratio'] = (df['N'] + df['P'] + df['K']) / 3

    # Nutrient balance index (lower std means more balanced nutrients)
    # Using row-wise standard deviation for X features
    df['nutrient_balance'] = df[['N', 'P', 'K']].std(axis=1)

    # Temperature-Humidity index (stress indicator)
    df['temp_humidity_index'] = df['temperature'] * df['humidity'] / 100

    # Soil fertility score (pH optimal range 6-7)
    df['ph_optimality'] = 1 - abs(df['ph'] - 6.5) / 6.5

    # Water availability score
    df['water_stress_index'] = df['rainfall'] / (df['temperature'] + 1)

    # Growing degree days approximation (base temp 18)
    df['growing_degree_days'] = (df['temperature'] - 18).clip(lower=0) * 30

    # Nutrient sufficiency ratios
    df['N_P_ratio'] = df['N'] / (df['P'] + 1)
    df['N_K_ratio'] = df['N'] / (df['K'] + 1)

    if is_dict:
        return df.iloc[0].to_dict()
    return df
