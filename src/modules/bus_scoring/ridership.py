import pandas as pd
import argparse

def calculate_bus_ridership(legs_path: str, vehicles_path: str) -> int:
    """
    Simpler version: logic calculating bus ridership.
    """
    # 1. Load data
    legs_df = pd.read_csv(legs_path, sep=';', usecols=['person', 'vehicle_id']) # Optimize columns
    vehicles_df = pd.read_csv(vehicles_path) # Default sep=,

    # 2. Filter Bus Vehicles
    # Fill NA to avoid errors, check string contains "bus"
    vehicles_df['type_id'] = vehicles_df['type_id'].fillna('').astype(str)
    bus_vehicles = vehicles_df[vehicles_df['type_id'].str.contains("bus", case=False)]
    print(f"[Ridership] Found {len(bus_vehicles)} bus vehicles.")

    # 3. Join & Count
    # Inner join keeps only legs that used a bus
    bus_legs = legs_df.merge(bus_vehicles, left_on='vehicle_id', right_on='id', how='inner')
    unique_persons = bus_legs['person'].nunique()
    
    print(f"[Ridership] Unique persons on bus: {unique_persons}")
    return unique_persons

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--legs", required=True)
    parser.add_argument("--vehicles", required=True)
    args = parser.parse_args()
    
    count = calculate_bus_ridership(args.legs, args.vehicles)
    print(f"RESULT={count}")

if __name__ == "__main__":
    main()
