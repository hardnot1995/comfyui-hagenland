# ComfyUI Video Sequence Controller 🔄

This custom ComfyUI node acts as a controller in a video generation workflow. It:
- Initializes using a starter image from the built-in image loader.
- Iteratively processes video segments, each time feeding the last frame back into the workflow.
- Generates unique filenames for each segment based on the iteration count.
- Creates a unique project folder named by combining a user-provided project name with a random number.
- Provides a reset input to restart the workflow if needed.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/comfyui_video_sequence_controller.git
