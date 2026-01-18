import pandas as pd
import argparse
import sys
import os
from typing import Dict


def calculate_bus_ridership(ridership_csv_path: str, homes_csv_path: str = None) -> Dict[str, any]:
    """
    Calculates the number of unique persons who used a bus based on prepare ridership data.
    If homes_csv_path is provided, calculates percentage of total population using bus.
    
    Returns:
        Dict: {
            "unique_persons_bus": int,
            "total_population": int,
            "ridership_percentage": float
        }
    """
    print(f"[Ridership Scoring] Loading data from: {ridership_csv_path}")
    result = {"unique_persons_bus": 0, "total_population": 0, "ridership_percentage": 0.0}
    
    if not os.path.exists(ridership_csv_path):
        print(f"Error: File not found at {ridership_csv_path}")
        return result
        
    try:
        # 1. Count Bus Users
        df = pd.read_csv(ridership_csv_path)
        
        if 'vehTypeList' not in df.columns or 'personId' not in df.columns:
            print(f"Error: Missing required columns 'personId' or 'vehTypeList'")
            return result
            
        df['vehTypeList'] = df['vehTypeList'].fillna('').astype(str)
        bus_trips = df[df['vehTypeList'].str.contains("bus", case=False)]
        unique_persons = bus_trips['personId'].nunique()
        result["unique_persons_bus"] = unique_persons
        
        print(f"[Ridership Scoring] Unique persons using bus: {unique_persons}")
        
        # 2. Total Population (if provided)
        if homes_csv_path:
            if os.path.exists(homes_csv_path):
                # Count lines - 1 (header) to avoid loading everything if only count needed
                # However, PlanInputProcessor output format is CSV.
                try:
                    with open(homes_csv_path, 'r', encoding='utf-8') as f:
                        row_count = sum(1 for row in f) - 1 # subtracting header
                    result["total_population"] = max(0, row_count)
                except:
                    # Fallback to pandas if simple count fails
                     pop_df = pd.read_csv(homes_csv_path)
                     result["total_population"] = len(pop_df)
                     
                if result["total_population"] > 0:
                    result["ridership_percentage"] = (unique_persons / result["total_population"]) * 100
                    print(f"[Ridership Scoring] Total Pop: {result['total_population']}, Usage: {result['ridership_percentage']:.2f}%")
            else:
                print(f"[Ridership Scoring] Warning: Homess CSV not found: {homes_csv_path}")

        return result
        
    except Exception as e:
        print(f"Error calculating ridership: {e}")
        return result

def main():
    parser = argparse.ArgumentParser(description="Calculate Bus Ridership Score")
    parser.add_argument("--ridership_csv", required=True, help="Path to the prepared ridership CSV file")
    parser.add_argument("--homes_csv", help="Path to pre-processed homes CSV (for total population)")
    args = parser.parse_args()
    
    res = calculate_bus_ridership(args.ridership_csv, args.homes_csv)
    print(f"RESULT={res}")

if __name__ == "__main__":
    main()
