
import xml.etree.ElementTree as ET
import pandas as pd
import math
import os
import argparse
from typing import Set, List, Dict, Tuple

class ServiceCoveragePrepareData:
    """
    Extracts bus stop locations from schedule and reads pre-processed population home locations.
    """
    def __init__(self, schedule_path: str, homes_csv_path: str):
        self.schedule_path = schedule_path
        self.homes_csv_path = homes_csv_path
        self.stop_locations: List[Tuple[float, float]] = [] # [(x, y)]
        self.home_locations: List[Tuple[float, float]] = [] # [(x, y)]

    def process(self):
        print("--- Processing Service Coverage Data ---")
        self._extract_active_stops()
        self._load_population_homes()

    def _extract_active_stops(self):
        """
        Extracts coordinates of stops that are actually used in transit routes.
        """
        print(f"Reading Transit Schedule: {self.schedule_path}")
        if not os.path.exists(self.schedule_path):
             print(f"Error: Schedule file not found at {self.schedule_path}")
             return

        try:
            tree = ET.parse(self.schedule_path)
            root = tree.getroot()
            
            # Map all stop facilities: id -> (x, y)
            all_stops_map = {}
            ns = {'ns': 'http://www.matsim.org/files/dtd'} if 'http' in root.tag else {}
            
            stops_container = root.find("transitStops", ns) if ns else root.find("transitStops")
            if stops_container is None: stops_container = root
            
            for stop in stops_container.findall("stopFacility", ns) if ns else stops_container.findall("stopFacility"):
                s_id = stop.get("id")
                x = float(stop.get("x"))
                y = float(stop.get("y"))
                all_stops_map[s_id] = (x, y)
            
            print(f"  Found {len(all_stops_map)} total stop facilities.")

            # Find used stops in lines
            active_stop_ids = set()
            lines = root.findall("transitLine", ns) if ns else root.findall("transitLine")
            for line in lines:
                routes = line.findall("transitRoute", ns) if ns else line.findall("transitRoute")
                for route in routes:
                    profile = route.find("routeProfile", ns) if ns else route.find("routeProfile")
                    if profile is not None:
                        stops = profile.findall("stop", ns) if ns else profile.findall("stop")
                        for s in stops:
                            ref_id = s.get("refId")
                            active_stop_ids.add(ref_id)
            
            print(f"  Found {len(active_stop_ids)} active stops used in routes.")
            
            for s_id in active_stop_ids:
                if s_id in all_stops_map:
                    self.stop_locations.append(all_stops_map[s_id])
                else:
                    print(f"Warning: Stop refId {s_id} used in route but not found.")
                    
        except Exception as e:
            print(f"Error reading schedule: {e}")

    def _load_population_homes(self):
        """
        Loads home coordinates from the pre-processed CSV file (PlanInputProcessor).
        """
        print(f"Reading Home Locations CSV: {self.homes_csv_path}")
        if not os.path.exists(self.homes_csv_path):
             print(f"Error: Homes CSV file not found at {self.homes_csv_path}")
             return

        try:
            df = pd.read_csv(self.homes_csv_path)
            if 'x' in df.columns and 'y' in df.columns:
                # Convert DataFrame to list of tuples
                self.home_locations = list(zip(df['x'], df['y']))
                print(f"  Loaded {len(self.home_locations)} home locations.")
            else:
                print(f"Error: Missing 'x' or 'y' columns in {self.homes_csv_path}")
                
        except Exception as e:
            print(f"Error loading homes CSV: {e}")

    def calculate_coverage(self, radius: float = 400.0) -> Dict[str, any]:
        """
        Calculates percentage of population covered by active stops.
        """
        print(f"Calculating coverage with radius {radius}m...")
        if not self.home_locations or not self.stop_locations:
            return {"covered_pop": 0, "total_pop": 0, "percentage": 0.0}

        try:
            from scipy.spatial import cKDTree
            tree = cKDTree(self.stop_locations)
            dists, _ = tree.query(self.home_locations, k=1, distance_upper_bound=radius)
            import numpy as np
            # Note: dists are infinite if unbound, so check against radius explicitly or infinity
            covered_count = np.sum(dists <= radius)
            
        except ImportError:
            print("Warning: Scipy not found. Using slower naive calculation.")
            covered_count = 0
            for hx, hy in self.home_locations:
                is_covered = False
                for sx, sy in self.stop_locations:
                    dist = math.sqrt((hx - sx)**2 + (hy - sy)**2)
                    if dist <= radius:
                        is_covered = True
                        break
                if is_covered:
                    covered_count += 1

        total_pop = len(self.home_locations)
        percentage = (covered_count / total_pop * 100) if total_pop > 0 else 0.0
        
        print(f"  Covered Population: {covered_count} / {total_pop}")
        print(f"  Coverage Percentage: {percentage:.2f}%")
        
        return {
            "covered_pop": int(covered_count),
            "total_pop": total_pop,
            "percentage": percentage
        }

def start_scoring(schedule_path: str, homes_csv_path: str, radius: float):
    processor = ServiceCoveragePrepareData(schedule_path, homes_csv_path)
    processor.process()
    return processor.calculate_coverage(radius)

def main():
    parser = argparse.ArgumentParser(description="Calculate Service Coverage Score")
    parser.add_argument("--schedule", required=True, help="Path to transit schedule XML")
    parser.add_argument("--homes_csv", required=True, help="Path to pre-processed homes CSV")
    parser.add_argument("--radius", type=float, default=400.0, help="Coverage radius in meters")
    
    args = parser.parse_args()
    
    start_scoring(args.schedule, args.homes_csv, args.radius)

if __name__ == "__main__":
    main()
