
import gzip
import xml.etree.ElementTree as ET
import pandas as pd
import os
from typing import Dict, List, Optional
from src.utils.file_utils import save_csv_from_list

# Check if lxml is available for faster parsing, otherwise use standard ElementTree
try:
    from lxml import etree
    USE_LXML = True
except ImportError:
    import xml.etree.ElementTree as etree
    USE_LXML = False

class QTripData:
    def __init__(self, person_id: str, start_time: float, main_mode: str):
        self.person_id = person_id
        self.start_time = start_time
        self.main_mode = main_mode
        self.veh_id_list: List[str] = []
        self.veh_type_list: List[str] = []

    def to_dict(self, travel_time: float):
        return {
            "personId": self.person_id,
            "vehTypeList": "|".join(self.veh_type_list),
            "vehIDList": "|".join(self.veh_id_list),
            "mainMode": self.main_mode,
            "startTime": self.start_time,
            "travelTime": travel_time
           
            
            
        }

class RidershipPrepareData:
    def __init__(self, events_path: str, vehicle_type_path: str):
        self.events_path = events_path
        self.vehicle_path = vehicle_type_path
        self.ridership_data: List[Dict] = []
        self._trip_map: Dict[str, QTripData] = {}
        self.veh_id_to_type_map: Dict[str, str] = {}
        self._load_vehicle_types()

    def _load_vehicle_types(self):
        """Loads vehicle types from the CSV file into a dictionary."""
        print(f"Loading vehicle types from: {self.vehicle_path}")
        if not os.path.exists(self.vehicle_path):
            print(f"Warning: Vehicle type file not found at {self.vehicle_path}. Vehicle types will be empty.")
            return
            
        try:
            df = pd.read_csv(self.vehicle_path)
            # Ensure columns exist. Assuming columns are 'id' and 'type_id' or similar based on previous context, 
            # but let's check standard names usually produced. 
            # The previous tool output showed keys from Vehicle class: 'id', 'type_id'.
            if 'id' in df.columns and 'type_id' in df.columns:
                 self.veh_id_to_type_map = pd.Series(df.type_id.values, index=df.id).to_dict()
            else:
                 print(f"Warning: Columns 'id' and 'type_id' not found in {self.vehicle_path}. Finding first two columns.")
                 if df.shape[1] >= 2:
                     self.veh_id_to_type_map = pd.Series(df.iloc[:, 1].values, index=df.iloc[:, 0]).to_dict()
                 
            print(f"Loaded {len(self.veh_id_to_type_map)} vehicle mappings.")
        except Exception as e:
            print(f"Error loading vehicle types: {e}")

    def process(self):
        """
        Extracts ridership trip data from MATSim events.
        """
        print(f"Processing events from: {self.events_path}")
        
        if not os.path.exists(self.events_path):
             raise FileNotFoundError(f"Events file not found at: {self.events_path}")

        # Determine open function based on extension
        open_func = gzip.open if self.events_path.endswith('.gz') else open
        mode = "rb" if self.events_path.endswith('.gz') else "rb" 
        
        try:
            with open_func(self.events_path, mode) as f:
                # Use iterparse
                # Standard ET.iterparse does not support 'tag' argument
                context = etree.iterparse(f, events=('end',))
                
                for event, elem in context:
                    if elem.tag == "event" or elem.tag.endswith("event"):
                        self._process_event(elem)
                        elem.clear()
                            
        except Exception as e:
            print(f"Error processing events: {e}")
            raise

        print(f"Extracted {len(self.ridership_data)} ridership records.")

    def _process_event(self, elem):
        e_type = elem.get("type")
        
        # 1. PersonDepartureEvent -> type="departure"
        if e_type == "departure":
            person_id = elem.get("person")
            if person_id.startswith("pt_"): return 
            
            if person_id in self._trip_map: return
            
            time = float(elem.get("time"))
            main_mode = elem.get("computationalRoutingMode")
                
            self._trip_map[person_id] = QTripData(person_id, time, main_mode)

        # 2. PersonEntersVehicleEvent -> type="PersonEntersVehicle"
        elif e_type == "PersonEntersVehicle":
            person_id = elem.get("person")
            if person_id.startswith("pt_"): return
            
            if person_id in self._trip_map:
                veh_id = elem.get("vehicle")
                self._trip_map[person_id].veh_id_list.append(veh_id)
                
                # Lookup vehicle type
                veh_type = self.veh_id_to_type_map.get(str(veh_id), "unknown")
                self._trip_map[person_id].veh_type_list.append(veh_type)

        # 3. ActivityStartEvent -> type="actstart"
        elif e_type == "actstart":
            person_id = elem.get("person")
            if person_id.startswith("pt_"): return
            
            act_type = elem.get("actType")
            if act_type == "pt interaction": return
            
            qtrip = self._trip_map.get(person_id)
            if not qtrip: return
            
            # If vehIDList is empty (pure walking), remove and don't write
            if not qtrip.veh_id_list:
                del self._trip_map[person_id]
                return
            
            current_time = float(elem.get("time"))
            travel_time = current_time - qtrip.start_time
            
            self.ridership_data.append(qtrip.to_dict(travel_time))
            
            del self._trip_map[person_id]

    def save_ridership_to_csv(self, output_path: str):
        print(f"Saving ridership data to: {output_path}")
        save_csv_from_list(self.ridership_data, output_path)
    
    def get_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.ridership_data)
