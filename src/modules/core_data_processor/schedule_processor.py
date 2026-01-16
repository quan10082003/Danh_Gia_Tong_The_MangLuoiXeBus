import xml.etree.ElementTree as ET
import os
from typing import List, Optional, Dict
from src.utils.file_utils import save_csv_from_list

class Stop:
    def __init__(self, id: str, x: float, y: float, link_ref_id: str, name: Optional[str] = None):
        self.stop_id: str = id
        self.x: float = x
        self.y: float = y
        self.link_ref_id: str = link_ref_id
        self.name: Optional[str] = name

class RouteStop:
    def __init__(self, route_id: str, sequence_id: int, stop_ref_id: str, 
                 departure_offset: Optional[str] = None, arrival_offset: Optional[str] = None, 
                 await_departure: Optional[str] = None):
        self.route_id: str = route_id
        self.sequence_id: int = sequence_id
        self.stop_ref_id: str = stop_ref_id
        self.departure_offset: Optional[str] = departure_offset
        self.arrival_offset: Optional[str] = arrival_offset
        self.await_departure: Optional[str] = await_departure

class RouteLink:
    def __init__(self, route_id: str, sequence_id: int, link_ref_id: str):
        self.route_id: str = route_id
        self.sequence_id: int = sequence_id
        self.link_ref_id: str = link_ref_id

class TransitRoute:
    def __init__(self, id: str, transport_mode: str, line_id: str):
        self.route_id: str = id
        self.transport_mode: str = transport_mode
        self.line_id: str = line_id
        self.stops: List[RouteStop] = []
        self.links: List[RouteLink] = []

class TransitScheduleData:
    def __init__(self, schedule_path: str):
        self.schedule_path: str = schedule_path
        self.stops_list: List[Stop] = []
        self.routes_list: List[TransitRoute] = [] # Stores route metadata
        
        # Flattened lists for CSV export
        self.flat_route_stops: List[RouteStop] = []
        self.flat_route_links: List[RouteLink] = []

    def process(self):
        if not os.path.exists(self.schedule_path):
            raise FileNotFoundError(f"Transit schedule file not found at: {self.schedule_path}")

        try:
            tree = ET.parse(self.schedule_path)
            root = tree.getroot()
            
            # Helper to strip namespace if present
            def get_tag_name(element):
                return element.tag.split('}')[-1] if '}' in element.tag else element.tag

            print("Extracting Stops...")
            # 1. Extract Stop Facilities
            # Use iter to find all descendants regardless of namespace/depth if needed, 
            # but findall with wildcard namespace is safer if structure is known
            for elem in root.iter():
                if get_tag_name(elem) == 'stopFacility':
                    self.stops_list.append(Stop(
                        id=elem.get('id'),
                        x=float(elem.get('x')),
                        y=float(elem.get('y')),
                        link_ref_id=elem.get('linkRefId'),
                        name=elem.get('name')
                    ))

            print(f"Extracted {len(self.stops_list)} stops.")

            print("Extracting Lines and Routes...")
            # 2. Extract Transit Lines & Routes
            for line in root.iter():
                if get_tag_name(line) == 'transitLine':
                    line_id = line.get('id')
                    
                    for route in line.iter():
                        if get_tag_name(route) == 'transitRoute':
                            route_id = route.get('id')
                            
                            # Find transport mode
                            transport_mode = "unknown"
                            for child in route:
                                if get_tag_name(child) == 'transportMode':
                                    transport_mode = child.text.strip()
                                    break
                            
                            transit_route = TransitRoute(route_id, transport_mode, line_id)
                            self.routes_list.append(transit_route)

                            # Profile (Stops)
                            for child in route:
                                if get_tag_name(child) == 'routeProfile':
                                    seq = 0
                                    for stop in child:
                                        if get_tag_name(stop) == 'stop':
                                            r_stop = RouteStop(
                                                route_id=route_id,
                                                sequence_id=seq,
                                                stop_ref_id=stop.get('refId'),
                                                departure_offset=stop.get('departureOffset'),
                                                arrival_offset=stop.get('arrivalOffset'),
                                                await_departure=stop.get('awaitDeparture')
                                            )
                                            transit_route.stops.append(r_stop)
                                            self.flat_route_stops.append(r_stop)
                                            seq += 1
                                    break
                            
                            # Network Route (Links)
                            for child in route:
                                if get_tag_name(child) == 'route':
                                    seq = 0
                                    for link in child:
                                        if get_tag_name(link) == 'link':
                                            r_link = RouteLink(
                                                route_id=route_id,
                                                sequence_id=seq,
                                                link_ref_id=link.get('refId')
                                            )
                                            transit_route.links.append(r_link)
                                            self.flat_route_links.append(r_link)
                                            seq += 1
                                    break

            print(f"Extracted {len(self.routes_list)} routes.")
            
        except Exception as e:
            print(f"Error processing transit schedule: {e}")
            raise

    def save_stops_to_csv(self, output_path: str):
        print(f"Saving stops to: {output_path}")
        save_csv_from_list(self.stops_list, output_path)

    def save_routes_to_csv(self, output_path: str):
        print(f"Saving routes to: {output_path}")
        # For routes csv, we usually want metadata (id, line, mode)
        # We can create temporary dicts or use the objects if we ignore the list fields
        # Ideally, we create a DTO or just select fields.
        # Let's create a list of dicts for safety to avoid dumping the whole lists of objects inside
        data = []
        for r in self.routes_list:
            data.append({
                'route_id': r.route_id,
                'line_id': r.line_id,
                'transport_mode': r.transport_mode
            })
        save_csv_from_list(data, output_path)

    def save_route_stops_to_csv(self, output_path: str):
        print(f"Saving route stops to: {output_path}")
        save_csv_from_list(self.flat_route_stops, output_path)

    def save_route_links_to_csv(self, output_path: str):
        print(f"Saving route links to: {output_path}")
        save_csv_from_list(self.flat_route_links, output_path)
