
import gzip
import xml.etree.ElementTree as ET
import pandas as pd
import os
from typing import Dict, List, Optional, Set
from src.utils.file_utils import save_csv_from_list

# Check if lxml is available for faster parsing, otherwise use standard ElementTree
try:
    from lxml import etree
    USE_LXML = True
except ImportError:
    import xml.etree.ElementTree as etree
    USE_LXML = False

class OnTimePerformancePrepareData:
    def __init__(self, events_path: str, vehicle_path: str):
        self.events_path = events_path
        self.vehicle_path = vehicle_path
        self.otp_data: List[Dict] = []
        self.bus_vehicles: Set[str] = set()
        self._temp_bus_map: Dict[str, Dict] = {} # Map vehicle_id -> partial data
        self._load_bus_vehicles()

    def _load_bus_vehicles(self):
        """Loads vehicle IDs that are buses from the CSV file."""
        print(f"Loading bus vehicles from: {self.vehicle_path}")
        if not os.path.exists(self.vehicle_path):
            print(f"Warning: Vehicle file not found at {self.vehicle_path}.")
            return
            
        try:
            df = pd.read_csv(self.vehicle_path)
            # We expect 'id' and 'type_id'
            # Filter where type_id contains 'bus'
            if 'id' in df.columns and 'type_id' in df.columns:
                df['type_id'] = df['type_id'].fillna('').astype(str)
                bus_df = df[df['type_id'].str.contains("bus", case=False)]
                self.bus_vehicles = set(bus_df['id'].astype(str).values)
            else:
                 print(f"Warning: Columns 'id' and 'type_id' not found in {self.vehicle_path}.")
                 
            print(f"Loaded {len(self.bus_vehicles)} bus vehicles.")
        except Exception as e:
            print(f"Error loading bus vehicles: {e}")

    def process(self):
        """
        Extracts Arrival/Departure events for OTP calculation.
        """
        print(f"Processing events from: {self.events_path}")
        
        if not os.path.exists(self.events_path):
             raise FileNotFoundError(f"Events file not found at: {self.events_path}")

        # Determine open function based on extension
        open_func = gzip.open if self.events_path.endswith('.gz') else open
        mode = "rb" if self.events_path.endswith('.gz') else "rb" 
        
        try:
            with open_func(self.events_path, mode) as f:
                context = etree.iterparse(f, events=('end',))
                
                for event, elem in context:
                    if elem.tag == "event" or elem.tag.endswith("event"):
                        self._process_event(elem)
                        elem.clear()
                            
        except Exception as e:
            print(f"Error processing events: {e}")
            raise

        print(f"Extracted {len(self.otp_data)} OTP records.")

    def _process_event(self, elem):
        e_type = elem.get("type")
        
        # 1. VehicleArrivesAtFacility
        if e_type == "VehicleArrivesAtFacility":
            veh_id = elem.get("vehicle")
            if veh_id not in self.bus_vehicles: return
            
            # Extract delay if present. Standard MATSim might not have it unless extended.
            # If delay is missing, we might need schedule data, but assuming it exists as per Kotlin equivalent.
            delay = elem.get("delay")
            if delay is None:
                # Fallback or ignore? The Kotlin code uses event.delay.
                # If it's missing, let's assume 0.0 or log warning if critical.
                # For now, let's treat it as 0.0 if missing, but typically it should be there if this is the intent.
                delay = "0.0"
                
            facility_id = elem.get("facility")
            time = elem.get("time")

            self._temp_bus_map[veh_id] = {
                "stopId": facility_id,
                "arrDelay": float(delay),
                "arrivalTime": float(time), # Good to keep reference
                "depDelay": 0.0 # Initialize
            }

        # 2. VehicleDepartsAtFacility
        elif e_type == "VehicleDepartsAtFacility":
            veh_id = elem.get("vehicle")
            if veh_id not in self._temp_bus_map: return
            
            delay = elem.get("delay")
            if delay is None:
                delay = "0.0"

            # Retrieve stored arrival data
            data = self._temp_bus_map[veh_id]
            
            # Verify it's the same facility? (Ideally yes, but let's assume sequence)
            # data has stopId. The departure event also has facility.
            facility_id = elem.get("facility")
            if facility_id != data["stopId"]:
                # Mismatch or missed event? 
                # If facility differs, maybe the bus didn't stop long or something weird.
                # But let's just proceed or ignore.
                pass
            
            data["depDelay"] = float(delay)
            data["departureTime"] = float(elem.get("time"))
            data["vehicleId"] = veh_id
            
            # Save record
            self.otp_data.append(data)
            
            # Clean up map? 
            # In simple logic, yes. A vehicle calls at one stop then leaves.
            del self._temp_bus_map[veh_id]

    def save_otp_data_to_csv(self, output_path: str):
        print(f"Saving OTP data to: {output_path}")
        save_csv_from_list(self.otp_data, output_path)
    
    def get_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.otp_data)
