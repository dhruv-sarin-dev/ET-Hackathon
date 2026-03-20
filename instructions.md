CRITICAL EXECUTION LOOP (The "State Update" Rule):
You are a stateful agent. You do not rely on chat history.
At the end of EVERY single task or code modification, you MUST execute the update_state tool (or run a python script to overwrite build_state.json).
You will update:

build_progress: Mark the current task as "COMPLETED" and summarize exactly what code you wrote.

handoff_instructions.current_pointer: Change this to the very next logical task required to finish the system.

architectural_discoveries: Add any new constraints, package dependencies, or logic rules you figured out during this step.

NEVER end a turn without updating the JSON. The JSON is your only permanent memory.