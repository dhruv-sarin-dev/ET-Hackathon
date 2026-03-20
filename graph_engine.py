import json
import networkx as nx
from typing import List, Dict, Any
import datetime
import logging
from schema import SupplyChainState, AlternateRoute

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
logger = logging.getLogger(__name__)

class SupplyChainGraph:
    def __init__(self, state_file: str = "nexus_state.json"):
        self.state_file = state_file
        self.graph = nx.DiGraph()
        self.state: SupplyChainState = SupplyChainState(timestamp=datetime.datetime.now().isoformat())
        self._build_baseline_graph()
        self._sync_state()

    def _build_baseline_graph(self):
        # 3-tier supply chain: Suppliers -> Manufacturing -> Distribution -> Retail
        
        # Suppliers
        self.graph.add_node("S1", type="supplier", label="Supplier Alpha")
        self.graph.add_node("S2", type="supplier", label="Supplier Beta")
        
        # Manufacturers
        self.graph.add_node("M1", type="manufacturer", label="Factory Prime")
        self.graph.add_node("M2", type="manufacturer", label="Factory Secundus")
        
        # Distribution Centers
        self.graph.add_node("DC1", type="distributor", label="Distributor North")
        self.graph.add_node("DC2", type="distributor", label="Distributor South")
        
        # Retailers
        self.graph.add_node("R1", type="retailer", label="Retail Hub A")
        self.graph.add_node("R2", type="retailer", label="Retail Hub B")
        self.graph.add_node("R3", type="retailer", label="Retail Hub C")

        # Edges (Source -> Target, weight=estimated_delay_hours under normal conditions)
        # S -> M
        self.graph.add_edge("S1", "M1", weight=24)
        self.graph.add_edge("S1", "M2", weight=36)
        self.graph.add_edge("S2", "M1", weight=48)
        self.graph.add_edge("S2", "M2", weight=24)
        
        # M -> DC
        self.graph.add_edge("M1", "DC1", weight=12)
        self.graph.add_edge("M1", "DC2", weight=18)
        self.graph.add_edge("M2", "DC1", weight=24)
        self.graph.add_edge("M2", "DC2", weight=12)
        
        # DC -> R
        self.graph.add_edge("DC1", "R1", weight=6)
        self.graph.add_edge("DC1", "R2", weight=8)
        self.graph.add_edge("DC2", "R2", weight=10)
        self.graph.add_edge("DC2", "R3", weight=6)
        self.graph.add_edge("DC1", "R3", weight=14)
        
        # Phase 8: Deterministic 3D Spatial Optimization
        self.pos = {
            "S1": (0, 5, 5),
            "S2": (0, -5, -5),
            
            "M1": (10, 5, -5),
            "M2": (10, -5, 5),
            
            "DC1": (20, 8, 0),
            "DC2": (20, -8, 0),
            
            "R1": (30, 10, 5),
            "R2": (30, 0, -5),
            "R3": (30, -10, 5)
        }

    def _sync_state(self):
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                self.state = SupplyChainState(**data)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            self.state = SupplyChainState(timestamp=datetime.datetime.now().isoformat())

    def update_graph_from_state(self):
        """Removes disrupted nodes from the NetworkX graph and recalculates routing"""
        self._sync_state()
        
        new_failed_nodes = set()
        
        # Remove directly impacted nodes via disruptions
        for disruption in self.state.active_disruptions:
            node = disruption.impacted_node_id
            if self.graph.has_node(node):
                logger.warning(f"Removing missing node: {node} ({disruption.severity} severity)")
                self.graph.remove_node(node)
                new_failed_nodes.add(node)
                
        # Calculate downstream cascade if necessary (simplified: if a retailer has no incoming paths, it fails)
        for node in list(self.graph.nodes()):
            if self.graph.nodes[node].get("type") == "retailer":
                if self.graph.in_degree(node) == 0:
                    logger.error(f"Cascade failure detected at {node} (No inbound routes)")
                    new_failed_nodes.add(node)
                    self.graph.remove_node(node)

        self.state.failed_nodes_cascade = list(set(self.state.failed_nodes_cascade) | new_failed_nodes)
        
        # Once modified, re-route essential critical pathways.
        self._calculate_reroutes()
        self._save_state()

    def _calculate_reroutes(self):
        """Identifies any lost optimal paths from Suppliers to Retailers and finds alternates"""
        self.state.active_reroutes = []
        
        suppliers = [n for n, attr in self.graph.nodes(data=True) if attr.get("type") == "supplier"]
        retailers = [n for n, attr in self.graph.nodes(data=True) if attr.get("type") == "retailer"]
        
        for r in retailers:
            best_path = None
            best_weight = float('inf')
            
            for s in suppliers:
                try:
                    # Enforced NetworkXNoPath graceful handling
                    path = nx.shortest_path(self.graph, source=s, target=r, weight='weight')
                    val = nx.path_weight(self.graph, path, weight='weight')
                    if val < best_weight:
                        best_weight = val
                        best_path = path
                except nx.NetworkXNoPath:
                    # No route available between s and r
                    pass
                        
            if best_path:
                path_str = ' -> '.join([str(n) for n in best_path])
                logger.info(f"Optimal active path for {r}: {path_str} (ETA {best_weight}h)")
                self.state.active_reroutes.append(AlternateRoute(
                    original_path=[],
                    new_path=best_path,
                    estimated_delay_hours=int(best_weight)
                ))
            else:
                logger.critical(f"NO_ROUTE_AVAILABLE to {r}!")

    def _save_state(self):
        """Writes the updated state back to the JSON ledger"""
        self.state.timestamp = datetime.datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            f.write(self.state.model_dump_json(indent=2))
        logger.info("State synced back to ledger.")

if __name__ == "__main__":
    engine = SupplyChainGraph()
    logger.info("Baseline graph initialized.")
    engine.update_graph_from_state()