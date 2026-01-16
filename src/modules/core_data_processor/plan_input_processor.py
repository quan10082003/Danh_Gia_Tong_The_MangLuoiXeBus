
import xml.etree.ElementTree as ET
import os
from typing import List
from src.utils.file_utils import save_csv_from_list

class PlanHomeLocation:
    def __init__(self, person_id: str, x: float, y: float):
        self.person_id = person_id
        self.x = x
        self.y = y

class PlanInputData:
    def __init__(self, plans_path: str):
        self.plans_path = plans_path
        self.home_locations: List[PlanHomeLocation] = []

    def process(self):
        """
        Parses the plans XML to find Home activity locations for each person.
        Only considers the 'selected' plan.
        """
        print(f"Processing plans from: {self.plans_path}")
        if not os.path.exists(self.plans_path):
            raise FileNotFoundError(f"Plans file not found: {self.plans_path}")

        try:
            # Use iterparse with start/end events to track context (person -> selected plan -> act)
            context = ET.iterparse(self.plans_path, events=("start", "end"))
            context = iter(context)
            event, root = next(context) # get root element

            current_person_id = None
            in_selected_plan = False
            
            # We only need one home location per person (usually they are the same in one plan)
            # This flag ensures we don't capture multiple 'home' acts for the same person if not needed
            # Or we can capture the first one we find in the selected plan.
            found_home_for_current_person = False

            for event, elem in context:
                if event == "start":
                    if elem.tag == "person" or elem.tag.endswith("person"):
                        current_person_id = elem.get("id")
                        found_home_for_current_person = False
                    
                    elif elem.tag == "plan" or elem.tag.endswith("plan"):
                        if elem.get("selected") == "yes":
                            in_selected_plan = True
                        else:
                            in_selected_plan = False
                            
                    elif elem.tag == "act" or elem.tag.endswith("act"):
                        if in_selected_plan and not found_home_for_current_person:
                            act_type = elem.get("type")
                            if act_type == "home":
                                try:
                                    x = float(elem.get("x"))
                                    y = float(elem.get("y"))
                                    self.home_locations.append(PlanHomeLocation(current_person_id, x, y))
                                    found_home_for_current_person = True # Stop looking for home for this person
                                except (ValueError, TypeError):
                                    # Handle missing or invalid x/y
                                    pass

                elif event == "end":
                    if elem.tag == "plan" or elem.tag.endswith("plan"):
                        in_selected_plan = False
                    
                    elif elem.tag == "person" or elem.tag.endswith("person"):
                        current_person_id = None
                        found_home_for_current_person = False
                        elem.clear() # Clear memory
                        
            print(f"Extracted home locations for {len(self.home_locations)} persons.")

        except Exception as e:
            print(f"Error processing plans: {e}")
            raise

    def save_to_csv(self, output_path: str):
        print(f"Saving home locations to: {output_path}")
        save_csv_from_list(self.home_locations, output_path)
