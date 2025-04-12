# Debugging script for VideoSequence nodes
import os
import time
import json

def debug_video_sequence_nodes():
    """Check if nodes are properly initialized and if state files are being created"""
    print("\n----- VIDEO SEQUENCE NODE DEBUGGING -----")
    
    # Check state directory
    state_dir = "hagenland_state"
    if not os.path.exists(state_dir):
        print(f"ERROR: State directory '{state_dir}' doesn't exist!")
        return
    
    print(f"State directory '{state_dir}' exists.")
    
    # List files in state directory
    state_files = os.listdir(state_dir)
    print(f"Found {len(state_files)} files in state directory:")
    
    # Analyze state files
    state_json_files = [f for f in state_files if f.endswith('_state.json')]
    feedback_files = [f for f in state_files if f.endswith('_feedback.txt')]
    
    print(f"- State JSON files: {len(state_json_files)}")
    for f in state_json_files:
        try:
            file_path = os.path.join(state_dir, f)
            modified_time = time.ctime(os.path.getmtime(file_path))
            size = os.path.getsize(file_path)
            
            # Try to read the state
            with open(file_path, 'r') as json_file:
                state = json.load(json_file)
                print(f"  * {f} (Modified: {modified_time}, Size: {size} bytes)")
                print(f"    - current_step: {state.get('current_step', 'N/A')}")
                print(f"    - total_segments: {state.get('total_segments', 'N/A')}")
        except Exception as e:
            print(f"  * {f} - ERROR reading file: {str(e)}")
    
    print(f"- Feedback files: {len(feedback_files)}")
    for f in feedback_files:
        try:
            file_path = os.path.join(state_dir, f)
            modified_time = time.ctime(os.path.getmtime(file_path))
            size = os.path.getsize(file_path)
            print(f"  * {f} (Modified: {modified_time}, Size: {size} bytes)")
        except Exception as e:
            print(f"  * {f} - ERROR reading file: {str(e)}")
    
    # Check debug log
    debug_log_path = os.path.join(state_dir, "debug_log.txt")
    if os.path.exists(debug_log_path):
        print(f"\nDebug log exists. Last 10 lines:")
        try:
            with open(debug_log_path, 'r') as log_file:
                lines = log_file.readlines()
                for line in lines[-10:]:
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"ERROR reading debug log: {str(e)}")
    else:
        print(f"\nERROR: Debug log '{debug_log_path}' doesn't exist!")
    
    print("\n----- END OF DEBUGGING -----\n")

if __name__ == "__main__":
    debug_video_sequence_nodes() 