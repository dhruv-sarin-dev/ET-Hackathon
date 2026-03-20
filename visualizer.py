import logging
import plotly.graph_objects as go
import networkx as nx
from graph_engine import SupplyChainGraph

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
logger = logging.getLogger(__name__)

def draw_network():
    baseline_engine = SupplyChainGraph()
    active_engine = SupplyChainGraph()
    active_engine.update_graph_from_state()
    
    G_base = baseline_engine.graph
    pos = baseline_engine.pos
    
    failed_nodes = set(active_engine.state.failed_nodes_cascade)
    for d in active_engine.state.active_disruptions:
        failed_nodes.add(d.impacted_node_id)
        
    reroute_edges = set()
    for route in active_engine.state.active_reroutes:
        path = route.new_path
        for i in range(len(path)-1):
            reroute_edges.add((path[i], path[i+1]))
            reroute_edges.add((path[i+1], path[i]))
    
    edge_traces = []
    
    for edge in G_base.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        
        is_reroute = (edge[0], edge[1]) in reroute_edges or (edge[1], edge[0]) in reroute_edges
        is_impacted = edge[0] in failed_nodes or edge[1] in failed_nodes
        
        if is_impacted:
            color = 'red'
            width = 6
        elif is_reroute:
            color = 'yellow'
            width = 8
        else:
            color = 'rgba(150, 150, 150, 0.4)'
            width = 2
            
        edge_traces.append(
            go.Scatter3d(
                x=[x0, x1, None], y=[y0, y1, None], z=[z0, z1, None],
                line=dict(width=width, color=color),
                hoverinfo='none',
                mode='lines'
            )
        )
        
    node_x = []
    node_y = []
    node_z = []
    node_text = []
    node_color = []
    
    layer_map = {"supplier": 0, "manufacturer": 1, "distributor": 2, "retailer": 3}
    colors = ['blue', 'green', 'orange', 'purple']
    
    for node, data in G_base.nodes(data=True):
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        node_text.append(f"{node} ({data.get('label', '')})")
        
        if node in failed_nodes:
            node_color.append('red')
        else:
            layer = layer_map.get(data.get("type", "supplier"), 0)
            node_color.append(colors[layer])
        
    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition='top center',
        textfont={"color": 'white', "size": 14},
        marker={
            "showscale": False,
            "color": node_color,
            "size": 24,
            "line_width": 2,
            "line_color": 'white'
        })
            
    fig = go.Figure(data=edge_traces + [node_trace],
             layout=go.Layout(
                title='NexusGraph Supply Chain Dashboard (Phase 8)',
                showlegend=False,
                margin={"b": 0, "l": 0, "r": 0, "t": 40},
                scene={
                    "aspectmode": 'data',
                    "camera": {"eye": {"x": 1.6, "y": -1.6, "z": 0.6}},
                    "xaxis": {"showgrid": True, "gridcolor": 'rgba(255,255,255,0.2)', "title": 'Tier Stage'},
                    "yaxis": {"showgrid": True, "gridcolor": 'rgba(255,255,255,0.2)', "title": ''},
                    "zaxis": {"showgrid": True, "gridcolor": 'rgba(255,255,255,0.2)', "title": ''},
                    "bgcolor": 'rgba(10, 10, 20, 1)'
                },
                paper_bgcolor='rgba(10, 10, 20, 1)',
                font={"color": 'white'}
             ))
    file_name = "nexus_dashboard.html"
    fig.write_html(file_name)
    logger.info(f"Generated Enhanced Phase 8 Dashboard at {file_name}")

if __name__ == "__main__":
    draw_network()