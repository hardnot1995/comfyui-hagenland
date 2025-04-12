import os
import random
import time
from typing import Any, Dict

class VideoSequenceControllerNode:
    NODE_NAME = "Video Sequence Controller 🔄"
    NODE_GROUP = "Video"
    CATEGORY = "🔄Hagenland"
    DESCRIPTION = "Controls iterative processing of video segments by routing the last frame back into the workflow."

    DEBUG_MODE = True  # For testing delays.

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "starter_image": ("IMAGE", {}),  # The first image to start processing.
                "work_location_path": ("STRING", {"default": "./ComfyUI/output/"}),
                "total_number_of_segments": ("INT", {"default": 10, "min": 1}),
                "project_name": ("STRING", {"default": "VidSeqProject"}),
                "reset_flag": ("BOOLEAN", {"default": False}),
                "manual_step": ("INT", {"default": 0, "min": 0, "max": 9999, "step": 1}, "Current Step (Manual Override)"),
                "use_manual_step": ("BOOLEAN", {"default": False})
            },
            "optional": {
                "last_frame_image": ("IMAGE", {})  # Make it optional so node can execute without it
            }
        }

    # Outputs: image, work_path_image, work_path_video, current_step, is_finished.
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "INT", "BOOLEAN")
    RETURN_NAMES = ("image", "work_path_image", "work_path_video", "current_step", "is_finished")
    FUNCTION = "process_video_sequence"

    def __init__(self, **kwargs):
        self.current_step = 0
        self.work_folder = None
        work_loc = kwargs.get("work_location_path", "").strip()
        self.work_location_path = work_loc if work_loc else "./ComfyUI/output/"
        self.total_number_of_segments = kwargs.get("total_number_of_segments", 10)
        self.project_name = kwargs.get("project_name", "VidSeqProject")
        self.reset_flag = kwargs.get("reset_flag", False)
        self.manual_step = kwargs.get("manual_step", 0)
        self.use_manual_step = kwargs.get("use_manual_step", False)
        self.last_output_image = None
        self.initialized = False

        print(f"[VideoSequenceController] Project: {self.project_name} | Work Location: {self.work_location_path}")

    def initialize_project_folder(self, project_name: str, work_location_path: str):
        rand_num = random.randint(100, 10000)
        project_dir_name = f"{project_name}_{rand_num}"
        self.work_folder = os.path.join(work_location_path, project_dir_name)
        os.makedirs(self.work_folder, exist_ok=True)
        print(f"[VideoSequenceController] Created project folder: {self.work_folder}")
        self.initialized = True

    def reset(self, project_name: str, work_location_path: str):
        self.current_step = 0
        self.last_output_image = None
        self.initialize_project_folder(project_name, work_location_path)
        print("[VideoSequenceController] Node reset: iteration count set to 0 and project folder regenerated.")

    def process_video_sequence(self, starter_image, work_location_path, total_number_of_segments, 
                               project_name, reset_flag, manual_step, use_manual_step, last_frame_image=None):
        """
        Iterative processing with support for both starter_image and last_frame_image inputs.
        """
        if self.DEBUG_MODE:
            time.sleep(1)
        else:
            time.sleep(0.02)

        if reset_flag:
            self.reset(project_name, work_location_path)

        # Set up image to output and determine step
        output_image = None

        if use_manual_step:
            self.current_step = manual_step
            if self.current_step == 0:
                output_image = starter_image
            elif last_frame_image is not None:
                output_image = last_frame_image
            else:
                output_image = self.last_output_image
        elif not self.initialized or self.current_step == 0:
            # First execution - use starter_image
            self.initialize_project_folder(project_name, work_location_path)
            output_image = starter_image
            self.last_output_image = starter_image
            self.current_step = 1
            print(f"[VideoSequenceController] First execution: Using starter_image for step {self.current_step}")
        elif last_frame_image is not None:
            # Subsequent execution with valid last_frame_image
            output_image = last_frame_image
            self.last_output_image = last_frame_image
            self.current_step += 1
            print(f"[VideoSequenceController] Received last_frame_image: Advancing to step {self.current_step}")
        else:
            # No new last_frame_image, use previous output (don't increment)
            output_image = self.last_output_image
            print(f"[VideoSequenceController] No new last_frame_image: Maintaining step {self.current_step}")

        # Check if we're finished
        is_finished = (self.current_step >= total_number_of_segments)
        
        # Handle finished state
        if is_finished:
            print("[VideoSequenceController] Process complete! Reached total segments limit.")
            # Instead of returning None, return a "dummy" image with a text overlay
            # This prevents errors in downstream nodes while signaling completion
            output_image = self.last_output_image  # Continue passing the last valid image
        
        # Prepare output paths
        work_path_base = os.path.join(self.work_folder, f"segment_{self.current_step:03d}")
        work_path_image = work_path_base
        work_path_video = work_path_base

        # Prepare outputs
        outputs = (output_image, work_path_image, work_path_video, self.current_step, is_finished)
        
        image_status = "True" if output_image is not None else "False"
        print(f"[VideoSequenceController] Outputs for segment {self.current_step}: image_output: {image_status}, work_path_image: {work_path_image}, work_path_video: {work_path_video}, current_step: {self.current_step}, is_finished: {is_finished}")

        return outputs

# Registration: In your package-level __init__.py, add:
# NODE_CLASS_MAPPINGS = {
#     "VideoSequenceController": VideoSequenceControllerNode
# }