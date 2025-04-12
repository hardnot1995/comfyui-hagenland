import os
import shutil
import time

# Import your node class. Adjust the import if your file structure is different.
# For example, if your node is in a folder named "node", ensure your PYTHONPATH includes the parent directory.
from video_sequence_controller import VideoSequenceControllerNode, STATE_DIR

def test_single_segment():
    print("\n--- Testing Single Segment (total_number_of_segments=1) ---")
    print(f"Using state directory: {STATE_DIR}")
    # Create an instance of your node with appropriate parameters.
    node = VideoSequenceControllerNode(
        work_location_path="./test_output",
        total_number_of_segments=1,
        project_name="TestProject",
        reset_flag=True
    )
    
    # Create dummy image data (simply strings here for test purposes).
    starter_image = "dummy_starter_image"
    last_frame_image = "dummy_last_frame_image"

    # Call process_video_sequence with a segment count of 1.
    # Note that the function parameters must match the signature:
    # (starter_image, last_frame_image, work_location_path, total_number_of_segments, project_name, reset_flag)
    output = node.process_video_sequence(
        starter_image,
        last_frame_image,
        "./test_output",
        1,  # total_number_of_segments for the process call
        "TestProject",
        False  # reset_flag for this call (already reset at init)
    )
    print("Test Single Segment Output:", output)

def test_multiple_segments():
    print("\n--- Testing Multiple Segments (total_number_of_segments=3) ---")
    node = VideoSequenceControllerNode(
        work_location_path="./test_output",
        total_number_of_segments=3,
        project_name="TestProject",
        reset_flag=True
    )
    starter_image = "dummy_starter_image"
    last_frame_image = "dummy_last_frame_image"

    # Process segments repeatedly.
    for i in range(5):  # Do more iterations than the segment limit to test the finish flag.
        try:
            output = node.process_video_sequence(
                starter_image,
                last_frame_image,
                "./test_output",
                3,  # total_number_of_segments for this test
                "TestProject",
                False
            )
            print(f"Iteration {i+1} Output:", output)
        except Exception as e:
            # If your node were to throw an exception, it would be caught here.
            # In our current version, we are not throwing an exception since we've removed the halt method.
            print(f"Iteration {i+1} Exception: {e}")
            break

if __name__ == '__main__':
    # Delete the test output folder to start fresh.
    if os.path.exists("./test_output"):
        shutil.rmtree("./test_output")

    test_single_segment()
    test_multiple_segments()
