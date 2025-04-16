import os
import random
import time
import uuid
import json
import traceback # Re-add traceback for exception handling
from typing import Any, Dict, List
import numpy as np # Keep numpy as it is used elsewhere
import logging
import folder_paths # Needed for Lora list

# Get the absolute path to the ComfyUI root directory
# First, get the directory of the current file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get the custom_nodes/comfyui-hagenland directory
CUSTOM_NODE_DIR = os.path.dirname(CURRENT_DIR)
# Use custom_node_dir as the root instead of going up two levels
# ROOT_DIR = os.path.dirname(os.path.dirname(CUSTOM_NODE_DIR))
ROOT_DIR = CUSTOM_NODE_DIR
# Define the state directory in the ComfyUI root
STATE_DIR = os.path.join(ROOT_DIR, "hagenland_state")

# Create the state directory if it doesn't exist
os.makedirs(STATE_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

class VideoSequenceTriggerNode:
    """Forces execution of the video sequence workflow in proper order"""
    NODE_NAME = "Video Sequence Trigger ➡️"
    NODE_GROUP = "Video"
    CATEGORY = "🔄Hagenland"
    DESCRIPTION = "Starts a video sequence workflow and ensures proper execution order."
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "display_name": ("STRING", {"default": "My Video Sequence"}),
                "reset": ("BOOLEAN", {"default": False})
            }
        }
    
    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("unique_id", "reset_flag")
    FUNCTION = "trigger"
    
    def __init__(self):
        self.node_id = str(uuid.uuid4())
        print(f"[VideoSequenceTrigger] Initialized with node_id: {self.node_id}")
        self.state_dir = STATE_DIR # Use global state dir
        os.makedirs(self.state_dir, exist_ok=True)
        print(f"[VideoSequenceTrigger] Using state directory: {self.state_dir}")
        self.last_generated_ids = {} # Dictionary to store {display_name: unique_id}
        
    def _get_debug_path(self):
        """Path for debug log"""
        return os.path.join(self.state_dir, "debug_log.txt")
        
    def _log_debug(self, message):
        """Write to debug log file"""
        try:
            with open(self._get_debug_path(), 'a') as f:
                f.write(f"{time.time()}: {message}\n")
        except Exception as e:
            print(f"[VideoSequenceTrigger] Error writing debug log: {str(e)}")
    
    def trigger(self, display_name, reset):
        """Generate a unique ID and reset flag for the workflow"""
        # Always write debug info
        self._log_debug(f"Trigger executed with display_name={display_name}, reset={reset}")
        print(f"[VideoSequenceTrigger] Triggering workflow: {display_name}, reset={reset}")
        
        # Check if we should reuse the existing ID
        if not reset and display_name in self.last_generated_ids:
            unique_id = self.last_generated_ids[display_name]
            print(f"[VideoSequenceTrigger] Reusing existing ID for '{display_name}': {unique_id}")
            self._log_debug(f"Reusing existing ID: {unique_id}")
        else:
            # Generate a new ID
            unique_id = f"{display_name}_{str(uuid.uuid4())[:8]}"
            self.last_generated_ids[display_name] = unique_id # Store the new ID
            print(f"[VideoSequenceTrigger] Generated NEW ID for '{display_name}': {unique_id}")
            self._log_debug(f"Generated NEW ID: {unique_id}")
            # If resetting, also clear any potentially existing feedback/state files for the *new* ID
            if reset:
                 print(f"[VideoSequenceTrigger] Reset requested, clearing old files for potential new ID: {unique_id}")
                 self._clear_files_for_id(unique_id)

        return (unique_id, reset)

    # Helper function to clear files (optional but good practice on reset)
    def _clear_files_for_id(self, unique_id):
        safe_id = "".join(c if c.isalnum() else "_" for c in unique_id)
        try:
            state_path = os.path.join(self.state_dir, f"{safe_id}_state.json")
            if os.path.exists(state_path):
                 os.remove(state_path)
                 print(f"[VideoSequenceTrigger] Removed state file: {state_path}")
            # Clear potential feedback files too (assuming max steps or search pattern)
            # This is a bit broad, might need refinement based on actual feedback file naming
            for step in range(1, 100): # Assume max 100 steps for cleanup
                 feedback_flag_path = os.path.join(self.state_dir, f"{safe_id}_feedback_step_{step}.txt")
                 feedback_image_path = os.path.join(self.state_dir, f"{safe_id}_feedback_image_step_{step}.png")
                 if os.path.exists(feedback_flag_path):
                     os.remove(feedback_flag_path)
                 if os.path.exists(feedback_image_path):
                     os.remove(feedback_image_path)
        except Exception as e:
            print(f"[VideoSequenceTrigger] Error during file cleanup for {unique_id}: {e}")


class VideoSequenceControllerNode:
    NODE_NAME = "VideoSequenceController"
    NODE_GROUP = "Video"
    CATEGORY = "🔄Hagenland/Video Sequence"
    DESCRIPTION = "Controls iterative processing of video segments by routing the last frame back into the workflow."

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "unique_id": ("STRING", {}),
                "reset_flag": ("BOOLEAN", {}),
                "starter_image": ("IMAGE", {}),
                "work_location_path": ("STRING", {"default": "output"}),
                "number_of_followup_segments": ("INT", {"default": 10, "min": 1}),
                "project_name": ("STRING", {"default": "VidSeqProject"}),
                "manual_step": ("INT", {"default": 0, "min": 0, "max": 9999, "step": 1}),
                "use_manual_step": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                # Revert dependency input to IMAGE
                "feedback_dependency": ("IMAGE", {}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "INT", "BOOLEAN", "INT")
    RETURN_NAMES = ("image", "work_path_image", "work_path_video", "current_step", "is_finished", "run_number")
    FUNCTION = "process"

    def __init__(self):
        self.node_id = str(uuid.uuid4())
        # Create necessary folders (using the global STATE_DIR)
        self.state_dir = STATE_DIR
        os.makedirs(self.state_dir, exist_ok=True)
        print(f"[VideoSequenceController] Initialized with ID: {self.node_id}")
        print(f"[VideoSequenceController] Using state directory: {self.state_dir}")
        
    def _get_debug_path(self):
        """Path for debug log"""
        return os.path.join(self.state_dir, "debug_log.txt")
        
    def _log_debug(self, message):
        """Write to debug log file"""
        try:
            with open(self._get_debug_path(), 'a') as f:
                f.write(f"{time.time()}: {message}\n")
        except Exception as e:
            print(f"[VideoSequenceController] Error writing debug log: {str(e)}")

    def _get_state_path(self, unique_id):
        """Get the path for state file"""
        safe_id = "".join(c if c.isalnum() else "_" for c in unique_id)
        return os.path.join(self.state_dir, f"{safe_id}_state.json")

    def _load_state(self, unique_id):
        """Load state from file"""
        try:
            state_path = self._get_state_path(unique_id)
            if os.path.exists(state_path):
                with open(state_path, 'r') as f:
                    state = json.load(f)
                print(f"[VideoSequenceController] Loaded state for {unique_id}")
                self._log_debug(f"Loaded state: {state}")
                return state
        except Exception as e:
            print(f"[VideoSequenceController] Error loading state: {str(e)}")
            self._log_debug(f"Error loading state: {str(e)}")
        return None

    def _save_state(self, unique_id, state):
        """Save state to file"""
        try:
            state_path = self._get_state_path(unique_id)
            with open(state_path, 'w') as f:
                json.dump(state, f)
            print(f"[VideoSequenceController] Saved state for {unique_id}")
            self._log_debug(f"Saved state: {state}")
        except Exception as e:
            print(f"[VideoSequenceController] Error saving state: {str(e)}")
            self._log_debug(f"Error saving state: {str(e)}")

    def _check_feedback(self, unique_id, current_step):
        """ Check if feedback *flag* file exists for the step that just finished (current_step - 1) """
        # We are checking if feedback for the *previous* step (current_step - 1) has arrived
        # But the feedback node will likely signal based on the step it *received* (current_step)
        # Let's assume feedback node signals completion *of* current_step
        feedback_step_to_check = current_step # Check feedback for the step we are currently on
        feedback_path = self._get_feedback_path(unique_id, feedback_step_to_check)
        has_feedback = os.path.exists(feedback_path)
        self._log_debug(f"Checking feedback flag for step {feedback_step_to_check} at {feedback_path}, result: {has_feedback}")
        if has_feedback:
            try:
                # Consume the flag file
                os.remove(feedback_path)
                print(f"[VideoSequenceController] Consumed feedback flag for step {feedback_step_to_check}")
                self._log_debug(f"Consumed feedback flag for step {feedback_step_to_check}")
            except Exception as e:
                print(f"[VideoSequenceController] Error removing feedback flag file {feedback_path}: {str(e)}")
        return has_feedback

    def initialize_project_folder(self, project_name, work_location_path):
        """Create an output folder for this project"""
        try:
            timestamp = int(time.time())
            project_dir_name = f"{project_name}_{timestamp}"
            work_folder = os.path.join(work_location_path, project_dir_name)
            os.makedirs(work_folder, exist_ok=True)
            print(f"[VideoSequenceController] Created project folder: {work_folder}")
            self._log_debug(f"Created project folder: {work_folder}")
            return work_folder
        except Exception as e:
            print(f"[VideoSequenceController] Error creating project folder: {str(e)}")
            self._log_debug(f"Error creating project folder: {str(e)}")
            fallback_folder = os.path.join("output", f"{project_name}_{int(time.time())}")
            os.makedirs(fallback_folder, exist_ok=True)
            return fallback_folder

    def save_image_tensor(self, image_tensor, save_path):
        """Save a tensor as an image file"""
        try:
            from PIL import Image
            import numpy as np
            
            # Convert tensor to numpy
            if image_tensor.shape[0] == 1:  # Batch size 1
                img = image_tensor[0].cpu().numpy()
            else:
                img = image_tensor.cpu().numpy()
            
            # Ensure correct range
            if img.max() <= 1.0:
                img = (img * 255).astype(np.uint8)
            else:
                img = img.astype(np.uint8)
            
            # Ensure folder exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save image
            pil_image = Image.fromarray(img)
            pil_image.save(save_path)
            print(f"[VideoSequenceController] Saved image to {save_path}")
            self._log_debug(f"Saved image to {save_path}")
            return True
        except Exception as e:
            print(f"[VideoSequenceController] Error saving image: {str(e)}")
            self._log_debug(f"Error saving image: {str(e)}")
            return False

    def process(self, unique_id, reset_flag, starter_image, work_location_path,
                number_of_followup_segments, project_name, manual_step, use_manual_step, feedback_dependency=None):
        """
        Main processing function that handles state management and workflow control.
        """
        try:
            print(f"[Controller] Processing entry for unique_id: {unique_id}, reset: {reset_flag}")
            self._log_debug(f"Starting process with unique_id: {unique_id}, reset: {reset_flag}")

            state_path = self._get_state_path(unique_id)
            print(f"[Controller] State directory: {self.state_dir}")
            print(f"[Controller] State file path: {state_path}")

            state = self._load_state(unique_id)
            output_image = starter_image # Default output
            current_step = 1 # Default step

            # === Case 1: Hard Reset or First Run ===
            if state is None or reset_flag:
                print(f"[Controller] Initializing new state (first run or hard reset) for {unique_id}")
                work_folder = self.initialize_project_folder(project_name, work_location_path)
                image_folder = os.path.join(work_folder, 'images')
                video_folder = os.path.join(work_folder, 'videos')
                os.makedirs(image_folder, exist_ok=True)
                os.makedirs(video_folder, exist_ok=True)

                state = {
                    'unique_id': unique_id,
                    'project_name': project_name,
                    'work_folder': work_folder,
                    'work_folder_image': image_folder,
                    'work_folder_video': video_folder,
                    'total_segments': number_of_followup_segments,
                    'current_step': 1,
                    'is_finished': False,
                    'run_count': 1,
                    'start_time': time.time(),
                    'last_update': time.time()
                }
                print(f"[Controller] New state created, starting at step 1")
                if starter_image is not None:
                    print(f"[Controller] Saving starter image as frame_000001.png")
                    self.save_image_tensor(starter_image, os.path.join(state['work_folder_image'], f"frame_000001.png"))
                else:
                    print(f"[Controller] Warning: No starter image provided for initialization.")
                current_step = 1
                output_image = starter_image

            # === Case 2: Auto-Restart After Finishing ===
            elif state.get('is_finished', False) and not reset_flag:
                print(f"[Controller] Workflow previously finished for {unique_id}. Auto-restarting sequence...")
                old_run_count = state.get('run_count', 0)
                # --- START FIX: Reuse existing folder on auto-restart ---
                work_folder = state.get('work_folder')
                if not work_folder or not os.path.exists(work_folder):
                    print("[Controller] Warning: Previous work_folder not found or invalid in state. Re-initializing.")
                    work_folder = self.initialize_project_folder(project_name, work_location_path)
                else:
                    print(f"[Controller] Reusing existing work folder: {work_folder}")
                # --- END FIX ---
                image_folder = os.path.join(work_folder, 'images')
                video_folder = os.path.join(work_folder, 'videos')
                os.makedirs(image_folder, exist_ok=True) # Ensure they exist 
                os.makedirs(video_folder, exist_ok=True)

                state = {
                    'unique_id': unique_id,
                    'project_name': project_name,
                    'work_folder': work_folder,
                    'work_folder_image': image_folder,
                    'work_folder_video': video_folder,
                    'total_segments': number_of_followup_segments,
                    'current_step': 1,
                    'is_finished': False,
                    'run_count': old_run_count + 1,
                    'start_time': time.time(),
                    'last_update': time.time()
                }
                print(f"[Controller] State reset for auto-restart, starting at step 1")

                if starter_image is not None:
                    print(f"[Controller] Saving NEW starter image as frame_000001.png for restart")
                    # Consider clearing old frames in image_folder here if desired
                    self.save_image_tensor(starter_image, os.path.join(state['work_folder_image'], f"frame_000001.png"))
                else:
                    print(f"[Controller] Warning: No starter image provided for auto-restart.")
                current_step = 1
                output_image = starter_image # Use the new starter image

            # === Case 3: Workflow In Progress ===
            elif not state.get('is_finished', False):
                print(f"[Controller] Continuing existing sequence for {unique_id}: step={state['current_step']}/{state['total_segments']}")
                current_step = state['current_step'] # Start with the current step from state

                if use_manual_step:
                    state['current_step'] = max(1, min(manual_step, state['total_segments']))
                    current_step = state['current_step']
                    print(f"[Controller] Manual step override to: {current_step}")
                    prev_image_path = os.path.join(state['work_folder_image'], f"frame_{current_step-1:06d}.png")
                    if current_step > 1 and os.path.exists(prev_image_path):
                        output_image = self.load_image_tensor(prev_image_path)
                    else:
                        output_image = starter_image
                else:
                    # Normal feedback check
                    has_feedback = self._check_feedback(unique_id, current_step)
                    if has_feedback:
                        print(f"[Controller] Feedback received for step {current_step}.")
                        feedback_image_path = self._get_feedback_image_path(unique_id, current_step)
                        if os.path.exists(feedback_image_path):
                            print(f"[Controller] Loading feedback image: {feedback_image_path}")
                            loaded_feedback_image = self.load_image_tensor(feedback_image_path)
                            if loaded_feedback_image is not None:
                                output_image = loaded_feedback_image # This becomes the output for the *next* step
                                # Save with correct frame number BEFORE incrementing step
                                frame_save_path = os.path.join(state['work_folder_image'], f"frame_{current_step:06d}.png")
                                print(f"[Controller] Saving feedback result as official frame: {frame_save_path}")
                                self.save_image_tensor(output_image, frame_save_path)
                                try:
                                    os.remove(feedback_image_path) # Clean up feedback image
                                except Exception as e:
                                    print(f"[Controller] Error removing feedback image file {feedback_image_path}: {e}")
                            else:
                                print(f"[Controller] Error loading feedback image {feedback_image_path}. Using previous frame or starter.")
                                prev_image_path = os.path.join(state['work_folder_image'], f"frame_{current_step-1:06d}.png")
                                if current_step > 1 and os.path.exists(prev_image_path):
                                     output_image = self.load_image_tensor(prev_image_path)
                                else:
                                     output_image = starter_image
                        else:
                            print(f"[Controller] Warning: Feedback flag found, but feedback image missing: {feedback_image_path}. Using previous frame or starter.")
                            prev_image_path = os.path.join(state['work_folder_image'], f"frame_{current_step-1:06d}.png")
                            if current_step > 1 and os.path.exists(prev_image_path):
                                 output_image = self.load_image_tensor(prev_image_path)
                            else:
                                 output_image = starter_image

                        # Increment step *after* processing feedback and saving the frame for the current step
                        current_step += 1
                        state['current_step'] = current_step # Update state for saving
                        print(f"[Controller] Incrementing to step {current_step}/{state['total_segments']}")
                    else:
                        # No feedback yet, hold step and re-output previous image
                        print(f"[Controller] No feedback yet for step {current_step}. Holding at step {current_step}. Re-outputting previous frame.")
                        prev_image_path = os.path.join(state['work_folder_image'], f"frame_{current_step-1:06d}.png")
                        if current_step > 1 and os.path.exists(prev_image_path):
                             output_image = self.load_image_tensor(prev_image_path)
                        else:
                             output_image = starter_image # Should be frame_000001 if current_step is 1
            else: # Should not happen if logic above is correct, but handle just in case
                 print(f"[Controller] Unexpected state condition encountered for {unique_id}. State: {state}")
                 current_step = state.get('current_step', 1)
                 output_image = starter_image # Fallback


            # === Final State Update and Return ===
            state['last_update'] = time.time()
            # Finished state is correctly determined *before* saving
            is_finished = (current_step > state['total_segments'])
            state['is_finished'] = is_finished
            self._save_state(unique_id, state)

            if is_finished:
                 # Log the step number that was just completed
                 print(f"[Controller] Process complete after finishing step {current_step-1}. Final state saved.")
            else:
                 # Log the step we are preparing for
                 print(f"[Controller] Preparing for step {current_step}. Outputting image result from step {current_step-1} to processing chain.")

            if output_image is None:
                print("[Controller] Warning: output_image is None, falling back to starter_image.")
                output_image = starter_image
            if output_image is None:
                 print("[Controller] Critical Warning: starter_image is also None. Creating blank image.")
                 import torch
                 output_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32)

            # --- Add Debugging --- 
            if output_image is not None:
                print(f"[Controller DEBUG] Returning image with shape: {output_image.shape}, dtype: {output_image.dtype}, min: {output_image.min()}, max: {output_image.max()}")
            else:
                print(f"[Controller DEBUG] Returning image is None (This shouldn't happen due to fallback)")
            # --- End Debugging ---

            # Always return the step number just completed
            final_step_number = current_step - 1
            current_run_number = state.get('run_count', 1)
            print(f"[Controller] Returning - Image: {type(output_image)}, Step: {final_step_number}, Finished: {is_finished}, Run: {current_run_number}")
            self._log_debug(f"Returning final results - Step: {final_step_number}, Finished: {is_finished}, Run: {current_run_number}")
            return (
                output_image,
                state['work_folder_image'],
                state['work_folder_video'],
                final_step_number, # Report the step number just completed
                is_finished,
                current_run_number # Add run number to output
            )

        except Exception as e:
            error_msg = f"Error in process: {str(e)}"
            print(f"[VideoSequenceController] {error_msg}")
            self._log_debug(error_msg)
            traceback.print_exc()
            import torch
            error_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            error_image[:, :, :, 0] = 1.0 # Red
            return (error_image, "output/error", "output/error", 0, True, 1)


    # Helper to load image tensor (assuming torch, PIL) - ADD this method
    def load_image_tensor(self, image_path):
        try:
            from PIL import Image
            import numpy as np
            import torch

            if not os.path.exists(image_path):
                 print(f"[VideoSequenceController] Error loading image: File not found at {image_path}")
                 return None

            pil_image = Image.open(image_path).convert('RGB')
            img = np.array(pil_image).astype(np.float32) / 255.0
            tensor = torch.from_numpy(img)[None,] # Add batch dimension
            return tensor
        except Exception as e:
            print(f"[VideoSequenceController] Error loading image from {image_path}: {e}")
            self._log_debug(f"Error loading image from {image_path}: {e}")
            return None

    # Need to modify feedback check/retrieval paths slightly
    def _get_feedback_path(self, unique_id, for_step):
        """ Get path for feedback *flag* file for a specific step """
        safe_id = "".join(c if c.isalnum() else "_" for c in unique_id)
        # Feedback *for* step N means step N completed and sent its result back
        return os.path.join(self.state_dir, f"{safe_id}_feedback_step_{for_step}.txt")

    def _get_feedback_image_path(self, unique_id, for_step):
        """ Get path for feedback *image* file for a specific step """
        safe_id = "".join(c if c.isalnum() else "_" for c in unique_id)
        return os.path.join(self.state_dir, f"{safe_id}_feedback_image_step_{for_step}.png")


class VideoSequenceFeedbackNode:
    NODE_NAME = "VideoSequenceFeedback"
    CATEGORY = "🔄Hagenland/Video Sequence"
    # Revert output to IMAGE
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("processed_image",)
    FUNCTION = "process_feedback"

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "processed_image": ("IMAGE", {}),
                "unique_id": ("STRING", {})
            }
        }
    
    def __init__(self):
        self.node_id = str(uuid.uuid4())
        self.state_dir = STATE_DIR # Use global state dir
        os.makedirs(self.state_dir, exist_ok=True)
        print(f"[VideoSequenceFeedback] Initialized with ID: {self.node_id}")
        print(f"[VideoSequenceFeedback] Using state directory: {self.state_dir}")


    def _get_debug_path(self):
        return os.path.join(self.state_dir, "debug_log.txt")

    def _log_debug(self, message):
        try:
            with open(self._get_debug_path(), 'a') as f:
                f.write(f"{time.time()}: [Feedback] {message}\\n")
        except Exception as e:
            print(f"[VideoSequenceFeedback] Error writing debug log: {str(e)}")

    # Need corresponding path methods from Controller
    def _get_state_path(self, unique_id):
        safe_id = "".join(c if c.isalnum() else "_" for c in unique_id)
        return os.path.join(self.state_dir, f"{safe_id}_state.json")

    def _load_state(self, unique_id):
         try:
            state_path = self._get_state_path(unique_id)
            if os.path.exists(state_path):
                with open(state_path, 'r') as f:
                    return json.load(f)
         except Exception as e:
            print(f"[VideoSequenceFeedback] Error loading state for {unique_id}: {e}")
         return None

    def _get_feedback_path(self, unique_id, for_step):
        """ Get path for feedback *flag* file """
        safe_id = "".join(c if c.isalnum() else "_" for c in unique_id)
        return os.path.join(self.state_dir, f"{safe_id}_feedback_step_{for_step}.txt")

    def _get_feedback_image_path(self, unique_id, for_step):
         """ Get path for feedback *image* file """
         safe_id = "".join(c if c.isalnum() else "_" for c in unique_id)
         return os.path.join(self.state_dir, f"{safe_id}_feedback_image_step_{for_step}.png")

    # Add the save_image_tensor method here too (or import if modularized)
    def save_image_tensor(self, image_tensor, save_path):
        """Save a tensor as an image file"""
        try:
            from PIL import Image
            import numpy as np

            if image_tensor is None:
                 print(f"[VideoSequenceFeedback] Cannot save None image tensor.")
                 return False

            # Convert tensor to numpy
            if image_tensor.shape[0] == 1:  # Batch size 1
                img = image_tensor[0].cpu().numpy()
            else: # Handle potential batch > 1, just take first image
                print(f"[VideoSequenceFeedback] Warning: Received batch size > 1 ({image_tensor.shape[0]}), using first image for feedback.")
                img = image_tensor[0].cpu().numpy()

            # Ensure correct range
            if img.max() <= 1.0:
                img = (img * 255).astype(np.uint8)
            else:
                img = img.astype(np.uint8)

            # Ensure folder exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Save image
            pil_image = Image.fromarray(img)
            pil_image.save(save_path)
            print(f"[VideoSequenceFeedback] Saved feedback image to {save_path}")
            self._log_debug(f"Saved feedback image to {save_path}")
            return True
        except Exception as e:
            print(f"[VideoSequenceFeedback] Error saving feedback image: {str(e)}")
            self._log_debug(f"Error saving feedback image: {str(e)}")
            return False

    def process_feedback(self, processed_image, unique_id):
        """
        Receives the processed image, saves it as feedback, and signals the controller.
        """
        try:
            print(f"[VideoSequenceFeedback] Received feedback for {unique_id}")
            self._log_debug(f"Received feedback for {unique_id}")

            # Load state to find current step
            state = self._load_state(unique_id)
            if not state:
                 print(f"[VideoSequenceFeedback] Error: Could not load state for {unique_id}. Cannot process feedback.")
                 return (processed_image,) # Return input image as fallback

            current_step = state.get('current_step', 1)
            if state.get('is_finished', False):
                 print(f"[VideoSequenceFeedback] Workflow {unique_id} already marked as finished. Ignoring feedback.")
                 return (processed_image,)

            print(f"[VideoSequenceFeedback] Current step from state: {current_step}")

            # 1. Save the received image to the feedback image path
            feedback_image_path = self._get_feedback_image_path(unique_id, current_step)
            print(f"[VideoSequenceFeedback] Attempting to save feedback image to: {feedback_image_path}")
            save_success = self.save_image_tensor(processed_image, feedback_image_path)
            print(f"[VideoSequenceFeedback] Image save success: {save_success}")

            # 2. Create the feedback flag file to signal controller
            if save_success:
                feedback_flag_path = self._get_feedback_path(unique_id, current_step)
                print(f"[VideoSequenceFeedback] Attempting to create feedback flag at: {feedback_flag_path}")
                try:
                    with open(feedback_flag_path, 'w') as f:
                        f.write(f"Feedback for step {current_step} received at {time.time()}")
                    print(f"[VideoSequenceFeedback] Successfully created feedback flag for step {current_step} at {feedback_flag_path}")
                    self._log_debug(f"Created feedback flag for step {current_step} at {feedback_flag_path}")
                except Exception as e:
                    print(f"[VideoSequenceFeedback] Error creating feedback flag file {feedback_flag_path}: {e}")
            else:
                 print(f"[VideoSequenceFeedback] Skipping feedback flag creation due to image save error.")


            # Return the original processed image
            return (processed_image,)

        except Exception as e:
            error_msg = f"Error in process_feedback: {str(e)}"
            print(f"[VideoSequenceFeedback] {error_msg}")
            self._log_debug(error_msg)
            traceback.print_exc()
            return (processed_image,) # Fallback, return original image


# --- Prompt Scheduling Nodes ---

class ScheduledPromptNode:
    NODE_NAME = "Scheduled Prompt 📝"
    CATEGORY = "🔄Hagenland/Scheduling"
    DESCRIPTION = "Holds a prompt text. Connect to a PromptScheduler input slot."

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "prompt_text": ("STRING", {"multiline": True, "default": ""})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt_string",)
    FUNCTION = "get_prompt"

    def get_prompt(self, prompt_text):
        # Directly return the text
        output_prompt = prompt_text
        prompt_preview = prompt_text[:50].replace("\n", " ") + ("..." if len(prompt_text) > 50 else "")
        print(f"[ScheduledPrompt] Returning: '{prompt_preview}'")
        return (output_prompt,)

class ValueSchedulerNode:
    NODE_NAME = "ValueScheduler"
    CATEGORY = "🔄Hagenland/Scheduling"
    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("active_value",)
    FUNCTION = "schedule_value"

    MAX_SCHEDULED_INPUTS = 16

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        inputs = {
            "required": {
                "current_step": ("INT", {"default": 1, "min": 1}),
            },
            "optional": {
                # Explicitly add step 0 with custom name
                "value_input_0 (starter image)": ("*", {})
            }
        }
        # Start loop from 1 for remaining inputs
        for i in range(1, cls.MAX_SCHEDULED_INPUTS + 1):
            inputs["optional"][f"value_input_{i}"] = ("*", {})
        return inputs

    def schedule_value(self, current_step, **kwargs):
        # Logic needs to check for both possible key names for step 0
        logger.info(f"[{self.NODE_NAME}] Scheduling for step: {current_step}")
        active_value = None # Default to None
        if current_step >= 0:
            for i in range(current_step, -1, -1):
                # Construct potential input name(s)
                input_name = f"value_input_0 (starter image)" if i == 0 else f"value_input_{i}"
                value_from_kw = kwargs.get(input_name, None)

                if value_from_kw is not None:
                    active_value = value_from_kw
                    logger.info(f"[{self.NODE_NAME}] Found active value at step {i} (using key '{input_name}') Type={type(active_value)}")
                    break
        logger.info(f"[{self.NODE_NAME}] Final active value for step {current_step}: Type={type(active_value)}")
        return (active_value,)


# --- TYPE-SPECIFIC SCHEDULERS ---

# String Scheduler
class StringSchedulerNode:
    NODE_NAME = "StringScheduler"
    CATEGORY = "🔄Hagenland/Scheduling"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("active_string",)
    FUNCTION = "schedule_string"

    MAX_SCHEDULED_INPUTS = 16

    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "current_step": ("INT", {"default": 1, "min": 1}),
            },
            "optional": {
                 "value_input_0 (starter image)": ("STRING", {"multiline": True, "default": ""})
            }
        }
        # Start loop from 1
        for i in range(1, cls.MAX_SCHEDULED_INPUTS + 1):
            inputs["optional"][f"value_input_{i}"] = ("STRING", {"multiline": True, "default": ""})
        return inputs

    def schedule_string(self, current_step, **kwargs):
        # Logic needs to check for both possible key names for step 0
        logger.info(f"[{self.NODE_NAME}] Scheduling for step: {current_step}")
        active_value = "" # Default
        if current_step >= 0:
            for i in range(current_step, -1, -1):
                input_name = f"value_input_0 (starter image)" if i == 0 else f"value_input_{i}"
                value_from_kw = kwargs.get(input_name, None)

                if value_from_kw is not None:
                    active_value = value_from_kw
                    logger.info(f"[{self.NODE_NAME}] Found active value '{active_value[:50]}...' at step {i} (using key '{input_name}')")
                    break
        logger.info(f"[{self.NODE_NAME}] Final active value for step {current_step}: '{active_value[:50]}...'")
        return (active_value,)

# Integer Scheduler
class IntSchedulerNode:
    NODE_NAME = "IntScheduler"
    CATEGORY = "🔄Hagenland/Scheduling"
    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("active_int",)
    FUNCTION = "schedule_int"

    MAX_SCHEDULED_INPUTS = 16

    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "current_step": ("INT", {"default": 1, "min": 1}),
            },
            "optional": {
                 "value_input_0 (starter image)": ("INT", {"default": 0, "min": -99999999, "max": 99999999})
            }
        }
        # Start loop from 1
        for i in range(1, cls.MAX_SCHEDULED_INPUTS + 1):
            inputs["optional"][f"value_input_{i}"] = ("INT", {"default": 0, "min": -99999999, "max": 99999999})
        return inputs

    def schedule_int(self, current_step, **kwargs):
        # Logic needs to check for both possible key names for step 0
        logger.info(f"[{self.NODE_NAME}] Scheduling for step: {current_step}")
        active_value = 0 # Default value if no non-zero is found
        found_non_zero = False

        if current_step >= 0:
            for i in range(current_step, -1, -1):
                # Check both possible input names for step 0
                input_name = f"value_input_0 (starter image)" if i == 0 else f"value_input_{i}"
                value_from_kw = kwargs.get(input_name, None)

                if value_from_kw is not None:
                    # Check if this value is non-zero
                    if value_from_kw != 0:
                        active_value = value_from_kw
                        logger.info(f"[{self.NODE_NAME}] Found active non-zero value {active_value} at step {i} (using key '{input_name}')")
                        found_non_zero = True
                        break # Found the most recent non-zero, stop searching

        # active_value holds the last non-zero found, or 0 if none were found.
        if not found_non_zero:
             logger.info(f"[{self.NODE_NAME}] No non-zero value found up to step {current_step}. Returning default {active_value}.")
        else:
             logger.info(f"[{self.NODE_NAME}] Final active value for step {current_step}: {active_value}")

        return (active_value,)

# Float Scheduler
class FloatSchedulerNode:
    NODE_NAME = "FloatScheduler"
    CATEGORY = "🔄Hagenland/Scheduling"
    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("active_float",)
    FUNCTION = "schedule_float"

    MAX_SCHEDULED_INPUTS = 16

    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "current_step": ("INT", {"default": 1, "min": 1}),
            },
            "optional": {
                 "value_input_0 (starter image)": ("FLOAT", {"default": 0.0, "min": -99999999.0, "max": 99999999.0, "step": 0.01})
            }
        }
        # Start loop from 1
        for i in range(1, cls.MAX_SCHEDULED_INPUTS + 1):
            inputs["optional"][f"value_input_{i}"] = ("FLOAT", {"default": 0.0, "min": -99999999.0, "max": 99999999.0, "step": 0.01})
        return inputs

    def schedule_float(self, current_step, **kwargs):
        # Logic needs to check for both possible key names for step 0
        logger.info(f"[{self.NODE_NAME}] Scheduling for step: {current_step}")
        active_value = 0.0 # Default
        found = False
        if current_step >= 0:
            for i in range(current_step, -1, -1):
                input_name = f"value_input_0 (starter image)" if i == 0 else f"value_input_{i}"
                value_from_kw = kwargs.get(input_name, None)

                if value_from_kw is not None:
                    active_value = value_from_kw
                    logger.info(f"[{self.NODE_NAME}] Found active value {active_value} at step {i} (using key '{input_name}')")
                    found = True
                    break
        if not found:
             logger.info(f"[{self.NODE_NAME}] No value found up to step {current_step}, returning default {active_value}")
        else:
             logger.info(f"[{self.NODE_NAME}] Final active value for step {current_step}: {active_value}")
        return (active_value,)


# Registration: In your package-level __init__.py, add:
# NODE_CLASS_MAPPINGS = {
#     "VideoSequenceController": VideoSequenceControllerNode,
#     "VideoSequenceFeedback": VideoSequenceFeedbackNode,
#     "VideoSequenceTrigger": VideoSequenceTriggerNode,
#     "StepScheduler": StepSchedulerNode,
# }

NODE_CLASS_MAPPINGS = {
    "VideoSequenceController": VideoSequenceControllerNode,
    "VideoSequenceFeedback": VideoSequenceFeedbackNode,
    "VideoSequenceTrigger": VideoSequenceTriggerNode,
    "ValueScheduler": ValueSchedulerNode,
    "StringScheduler": StringSchedulerNode,
    "IntScheduler": IntSchedulerNode,
    "FloatScheduler": FloatSchedulerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoSequenceController": "Video Sequence Controller 🎥",
    "VideoSequenceFeedback": "Video Sequence Feedback 📝",
    "VideoSequenceTrigger": "Video Sequence Trigger ⚡",
    "ValueScheduler": "Value Scheduler 📅 (*)",
    "StringScheduler": "String Scheduler 📅 (Abc)",
    "IntScheduler": "Int Scheduler 📅 (123)",
    "FloatScheduler": "Float Scheduler 📅 (1.23)",
}