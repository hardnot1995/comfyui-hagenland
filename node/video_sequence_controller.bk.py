import os
import random
import time
import base64
from io import BytesIO
from typing import Any, Dict
from PIL import Image  # Make sure PIL is installed.

def pil_to_base64(image: Image.Image) -> str:
    """Convert a PIL Image to a base64-encoded PNG string."""
    if image is None:
        return None
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

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
                "total_number_of_segments": ("INT", {"default": 10}),
                "project_name": ("STRING", {"default": "VidSeqProject"}),
                "reset_flag": ("BOOLEAN", {"default": False})
            },
            "optional": {
                "last_frame_image": ("IMAGE", {"default": None, "forceInput": False})
            }
        }

    # Outputs: image (as a base64 string), work_path_image, work_path_video, current_step, is_finished.
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
        self.last_output_image = None  # Store the last valid image (as a PIL Image).
        
        print(f"[VideoSequenceController] Project: {self.project_name} | Work Location: {self.work_location_path}")

    def initialize_project_folder(self, project_name: str, work_location_path: str):
        rand_num = random.randint(100, 10000)
        project_dir_name = f"{project_name}_{rand_num}"
        self.work_folder = os.path.join(work_location_path, project_dir_name)
        os.makedirs(self.work_folder, exist_ok=True)
        print(f"[VideoSequenceController] Created project folder: {self.work_folder}")

    def reset(self, project_name: str, work_location_path: str):
        self.current_step = 0
        self.last_output_image = None
        self.initialize_project_folder(project_name, work_location_path)
        print("[VideoSequenceController] Node reset: iteration count set to 0 and project folder regenerated.")

    def process_video_sequence(self, starter_image, last_frame_image, work_location_path, total_number_of_segments, project_name, reset_flag):
        """
        Iterative processing function:
        
        - Step 1: If current_step==0, use starter_image and increment.
        - Subsequent steps: Only when a valid last_frame_image is provided (not None), update and increment.
        - When current_step reaches total_number_of_segments, output image = None and is_finished = True.
        
        Returns:
          (image, work_path_image, work_path_video, current_step, is_finished)
          
        The image output is converted to a base64-encoded PNG string for JSON serialization.
        """
        if self.DEBUG_MODE:
            time.sleep(1)
        else:
            time.sleep(0.02)
        
        if reset_flag:
            self.reset(project_name, work_location_path)
        
        if self.current_step == 0 or self.work_folder is None:
            self.initialize_project_folder(project_name, self.work_location_path)
        
        if self.current_step == 0:
            current_image = starter_image
            self.last_output_image = starter_image
            self.current_step += 1
        else:
            if last_frame_image is not None:
                current_image = last_frame_image
                self.last_output_image = last_frame_image
                self.current_step += 1
            else:
                current_image = self.last_output_image
                print("[VideoSequenceController] Waiting for new last_frame_image; retaining previous output without increment.")
        
        is_finished = (self.current_step >= total_number_of_segments)
        if is_finished:
            current_image = None  # On finish, do not pass any new image.
        
        work_path_base = os.path.join(self.work_folder, f"segment_{self.current_step:03d}")
        work_path_image = work_path_base
        work_path_video = work_path_base
        
        # Convert the image to a base64 string if it is a PIL Image.
        if current_image is not None and isinstance(current_image, Image.Image):
            converted_image = pil_to_base64(current_image)
        else:
            converted_image = current_image  # May be None or already a string.
        
        outputs = (converted_image, work_path_image, work_path_video, self.current_step, is_finished)
        image_status = "True" if converted_image is not None else "False"
        print(f"[VideoSequenceController] Outputs for segment {self.current_step}: image_output: {image_status}, work_path_image: {work_path_image}, work_path_video: {work_path_video}, current_step: {self.current_step}, is_finished: {is_finished}")
        
        return outputs

# Registration: In your package-level __init__.py, add:
# NODE_CLASS_MAPPINGS = {
#     "VideoSequenceController": VideoSequenceControllerNode
# }
