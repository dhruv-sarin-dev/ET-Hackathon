import os
import json
import uuid
import datetime
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from schema import DisruptionEvent, DisruptionReport, SupplyChainState

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
logger = logging.getLogger(__name__)

VALID_NODES = {'S1', 'S2', 'M1', 'M2', 'DC1', 'DC2', 'R1', 'R2', 'R3'}

def run_signal_agent(news_text: str):
    logger.info(f"Processing news: '{news_text}'")
    
    events_to_write = []
    
    if not os.environ.get("GOOGLE_API_KEY"):
        logger.warning("GOOGLE_API_KEY not found in environment. Using mocked Gemini response to verify pipeline.")
        events_to_write.append(DisruptionEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}", 
            impacted_node_id="DC1", 
            severity="High", 
            description="Mocked extraction: Port strike at Distributor North"
        ))
    else:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
            structured_llm = llm.with_structured_output(DisruptionReport)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an AI agent analyzing supply chain disruptions. "
                           "Given a news report, extract all concurrent disruption events into a report. "
                           "Map the entity to one of the following node IDs: "
                           "'S1' (Supplier Alpha), 'S2' (Supplier Beta), "
                           "'M1' (Factory Prime), 'M2' (Factory Secundus), "
                           "'DC1' (Distributor North), 'DC2' (Distributor South), "
                           "'R1' (Retail Hub A), 'R2' (Retail Hub B), 'R3' (Retail Hub C)."),
                ("human", "{news}")
            ])
            
            chain = prompt | structured_llm
            report: DisruptionReport = chain.invoke({"news": news_text})
            
            for ev in report.events:
                if not ev.event_id or ev.event_id == "":
                    ev.event_id = f"evt_{str(uuid.uuid4().hex)[:8]}"
                if ev.impacted_node_id not in VALID_NODES:
                    logger.warning(f"Hallucinated node_id detected: {ev.impacted_node_id}. Defaulting to safe state for this event.")
                    continue
                events_to_write.append(ev)
                logger.info(f"Extracted Disruption:\n{ev.model_dump_json(indent=2)}")
                
        except Exception as e:
            logger.error(f"LLM processing failed: {e}. Defaulting to safe state.")

    if events_to_write:
        _write_events_to_state(events_to_write)

def _write_events_to_state(events: list):
    state_file = "nexus_state.json"
    try:
        with open(state_file, 'r') as f:
            data = json.load(f)
            state = SupplyChainState(**data)
    except Exception as e:
        logger.error(f"Failed to load {state_file}: {e}")
        return
        
    state.active_disruptions.extend(events)
    state.timestamp = datetime.datetime.now().isoformat()
    
    with open(state_file, 'w') as f:
        f.write(state.model_dump_json(indent=2))
    
    logger.info("State updated with new disruption events.")
    
    logger.info("Triggering Graph Engine Math...")
    from graph_engine import SupplyChainGraph
    engine = SupplyChainGraph(state_file)
    engine.update_graph_from_state()

if __name__ == "__main__":
    # Simulate an incoming signal (Multi-disruption)
    mock_signal = "Breaking: A severe port strike has shut down Distributor North. Simultaneously, Factory Prime experienced a major power grid failure."
    run_signal_agent(mock_signal)