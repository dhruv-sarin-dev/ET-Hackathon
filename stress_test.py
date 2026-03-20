import random
import time
import concurrent.futures
import logging
from graph_engine import SupplyChainGraph
from schema import DisruptionEvent

# Setup cool terminal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("ChaosLogger")

# --- TEST 1: CHAOS ENGINEERING (The Simian Army) ---
def chaos_monkey_strike(iteration):
    """Randomly kills 1 to 3 nodes and checks if the system survives."""
    try:
        # Instantiate a fresh engine per thread because NetworkX graphs mutated 
        # asynchronously are not thread-safe.
        engine = SupplyChainGraph()
        
        # Disable file IO for pure memory load testing so we don't corrupt nexus_state.json
        engine._save_state = lambda: None
        engine._sync_state = lambda: None
        
        all_nodes = list(engine.graph.nodes())
        
        # Ensure we don't accidentally pick the Retailers as a dead node for this test
        # so we can test routing from Suppliers -> Retailers
        retailers = [n for n, attr in engine.graph.nodes(data=True) if attr.get("type") == "retailer"]
        for r in retailers:
            if r in all_nodes:
                all_nodes.remove(r)
            
        num_to_kill = random.randint(1, 3)
        dead_nodes = set(random.sample(all_nodes, num_to_kill))
        
        # Inject disruptions directly into the memory state
        for idx, node in enumerate(dead_nodes):
            engine.state.active_disruptions.append(DisruptionEvent(
                event_id=f"chaos_{iteration}_{idx}", 
                impacted_node_id=node, 
                severity="High", 
                description="Chaos Monkey Strike"
            ))
            
        # Try to calculate blast radius and reroute
        engine.update_graph_from_state()
        
        reroutes = engine.state.active_reroutes
        
        if len(reroutes) > 0:
            return f"Iter {iteration}: SURVIVED. Nuked {dead_nodes}. Found routes to {len(reroutes)} retailers."
        else:
            return f"Iter {iteration}: NO ROUTE. Nuked {dead_nodes}. System handled it gracefully."
    except Exception as e:
        return f"Iter {iteration}: CRITICAL FAILURE. Nuked {dead_nodes}. Error: {str(e)}"

# --- TEST 2: LOAD TESTING (Concurrency) ---
def run_combined_stress_test(num_requests=5000):
    logger.info("🔥 INITIATING CHAOS ENGINEERING & LOAD TEST 🔥")
    
    start_time = time.time()
    successful_runs = 0
    failures = 0
    
    # We use ThreadPoolExecutor to simulate massive concurrent disruptions
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        # Map the chaos_monkey_strike function to run num_requests times in parallel
        futures = {executor.submit(chaos_monkey_strike, i): i for i in range(num_requests)}
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if "CRITICAL FAILURE" in result:
                    logger.error(result)
                    failures += 1
                else:
                    successful_runs += 1
            except Exception as exc:
                logger.error(f"Thread crashed: {exc}")
                failures += 1

    end_time = time.time()
    duration = end_time - start_time
    throughput = num_requests / duration

    logger.info("==================================================")
    logger.info("📊 STRESS TEST RESULTS 📊")
    logger.info(f"Total Concurrent Attacks: {num_requests}")
    logger.info(f"Successful Graceful Handlings: {successful_runs}")
    logger.info(f"Critical System Crashes: {failures}")
    logger.info(f"Total Time: {duration:.2f} seconds")
    logger.info(f"Throughput: {throughput:.2f} calculations / second")
    logger.info("==================================================")

if __name__ == "__main__":
    # Blast it 10,000 times across 100 parallel threads
    run_combined_stress_test(num_requests=10000)