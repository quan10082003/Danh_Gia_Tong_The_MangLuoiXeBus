import os
import xml.etree.ElementTree as ET
from typing import List
from src.utils.file_utils import save_csv_from_list

class Node:
    def __init__(self, id: str, x: float, y: float):
        self.id: str = id
        self.x: float = x
        self.y: float = y

class Link:
    def __init__(self, id: str, from_node: str, to_node: str, modes: str):
        self.id: str = id
        self.from_node: str = from_node
        self.to_node: str = to_node
        self.modes: str = modes


class NetworkData:
    def __init__(self, network_path: str):
        self.network_path: str = network_path
        self.nodes_list: List[Node] = []
        self.link_list: List[Link] = []

    def process(self):
        """
        Trích xuất thông tin node và link trong network
        """
        try:
            tree = ET.parse(self.network_path)
            root = tree.getroot()

            # Extract Nodes
            for node in root.findall('nodes/node'):
                self.nodes_list.append(Node(
                    id=node.get('id'),
                    x=float(node.get('x')),
                    y=float(node.get('y'))
                ))
            # Extract Links
            for link in root.findall('links/link'):
                self.link_list.append(Link(
                    id=link.get('id'),
                    from_node=link.get('from'),
                    to_node=link.get('to'),
                    modes=link.get('modes')
                ))
            
            print(f"Extracted {len(self.nodes_list)} nodes and {len(self.link_list)} links.")
            
        except Exception as e:
            print(f"Error processing network: {e}")
            raise

    
    def save_nodes_to_csv(self, nodes_csv_path: str):
        print(f"Saving processed nodes to: {nodes_csv_path}")
        save_csv_from_list(self.nodes_list, nodes_csv_path)

    def save_links_to_csv(self, links_csv_path: str):
        print(f"Saving processed links to: {links_csv_path}")
        save_csv_from_list(self.link_list, links_csv_path)