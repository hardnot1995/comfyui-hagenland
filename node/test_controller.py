import os
import torch
import numpy as np
from video_sequence_controller import VideoSequenceControllerNode, VideoSequenceTriggerNode, STATE_DIR

def test_controller():
    """Test the VideoSequenceController directly"""
    print("\n----- TESTING CONTROLLER NODE -----")
    
    # Print the state directory being used
    print(f"Using state directory: {STATE_DIR}")
    
    # Create a dummy image
    test_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
    test_image[0, :, :, 1] = 0.8  # Green image
    
    # Initialize the trigger node
    trigger = VideoSequenceTriggerNode()
    unique_id, reset_flag = trigger.trigger("Test Sequence", False)
    
    print(f"Trigger generated unique_id: {unique_id}")
    
    # Initialize the controller node
    controller = VideoSequenceControllerNode()
    print(f"Controller initialized with ID: {controller.node_id}")
    
    # Process with the controller
    try:
        result = controller.process(
            unique_id=unique_id,
            reset_flag=reset_flag,
            starter_image=test_image,
            work_location_path="output",
            total_number_of_segments=5,
            project_name="TestProject",
            manual_step=0,
            use_manual_step=False
        )
        
        output_image, work_path_image, work_path_video, current_step, is_finished = result
        
        print(f"Controller processing successful:")
        print(f"- current_step: {current_step}")
        print(f"- is_finished: {is_finished}")
        print(f"- work_path_image: {work_path_image}")
        
        # Check state file
        state_path = controller._get_state_path(unique_id)
        if os.path.exists(state_path):
            print(f"State file created at: {state_path}")
        else:
            print(f"ERROR: State file not created at: {state_path}")
            
    except Exception as e:
        print(f"ERROR executing controller.process: {str(e)}")
        import traceback
        traceback.print_exc()
        
    print("----- TEST COMPLETE -----\n")

if __name__ == "__main__":
    test_controller() 