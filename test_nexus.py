import pytest
import os
import json
import datetime
from graph_engine import SupplyChainGraph
from schema import SupplyChainState, DisruptionEvent

@pytest.fixture
def clean_engine(tmp_path):
    test_state_file = tmp_path / "test_state.json"
    
    # Initialize empty state
    state = SupplyChainState(timestamp=datetime.datetime.now().isoformat())
    with open(test_state_file, 'w') as f:
        f.write(state.model_dump_json(indent=2))
        
    engine = SupplyChainGraph(str(test_state_file))
    return engine, str(test_state_file)

def test_calculate_impact_blast_radius(clean_engine):
    """Test that isolating a retailer triggers a cascade failure."""
    engine, state_file = clean_engine
    
    # R1 is connected only to DC1. If DC1 goes down, R1 should cascade fail.
    disruption = DisruptionEvent(event_id="evt_t1", impacted_node_id="DC1", severity="High", description="Unit Test")
    engine.state.active_disruptions.append(disruption)
    
    with open(state_file, 'w') as f:
        f.write(engine.state.model_dump_json(indent=2))
        
    engine.update_graph_from_state()
    
    assert "DC1" not in engine.graph.nodes()
    assert "R1" in engine.state.failed_nodes_cascade
    assert "R1" not in engine.graph.nodes()

def test_find_reroute_avoids_dead_node(clean_engine):
    """Test that finding a new route properly avoids a disconnected node."""
    engine, state_file = clean_engine
    
    # R3 is connected to DC1 and DC2. If DC1 fails, it should route S -> M -> DC2 -> R3.
    disruption = DisruptionEvent(event_id="evt_t2", impacted_node_id="DC1", severity="High", description="Unit Test")
    engine.state.active_disruptions.append(disruption)
    
    with open(state_file, 'w') as f:
        f.write(engine.state.model_dump_json(indent=2))
        
    engine.update_graph_from_state()
    
    # Check active reroutes for R3
    reroute = next((r for r in engine.state.active_reroutes if r.new_path[-1] == "R3"), None)
    
    assert reroute is not None, "A valid reroute should exist for R3"
    assert "DC1" not in reroute.new_path, "Dead node DC1 should not be in the new path"
    assert "DC2" in reroute.new_path, "New path must route through DC2"

def test_no_path_scenario_graceful_handling(clean_engine):
    """Test handling of true isolation where no path exists but node survives cascade check."""
    engine, state_file = clean_engine
    
    # Remove both Manufacturers. DC's remain, Retailers survive cascade check (in_degree > 0).
    # But path from Suppliers -> Retailers is entirely severed.
    engine.state.active_disruptions.extend([
        DisruptionEvent(event_id="evt_t3a", impacted_node_id="M1", severity="High", description="Unit Test"),
        DisruptionEvent(event_id="evt_t3b", impacted_node_id="M2", severity="High", description="Unit Test")
    ])
    
    with open(state_file, 'w') as f:
        f.write(engine.state.model_dump_json(indent=2))
        
    # The math must not throw an unhandled nx.NetworkXNoPath exception
    try:
        engine.update_graph_from_state()
        success_no_crash = True
    except Exception as e:
        success_no_crash = False
        print(f"Failed with exception: {e}")
        
    assert success_no_crash, "Engine crashed when facing NO_ROUTE_AVAILABLE scenario."
    
    # Verify no alternative routes were generated for retailers because they are isolated
    assert len(engine.state.active_reroutes) == 0, "Should not generate reroutes when no path exists"
