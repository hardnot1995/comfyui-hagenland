# comfyui-hagenland/__init__.py

# Import your node classes from the node subpackage.
try:
    from node.video_sequence_controller import VideoSequenceControllerNode, VideoSequenceFeedbackNode, VideoSequenceTriggerNode
except ImportError:
    import sys, os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from node.video_sequence_controller import VideoSequenceControllerNode, VideoSequenceFeedbackNode, VideoSequenceTriggerNode


# Define NODE_CLASS_MAPPINGS so ComfyUI can find your custom nodes.
NODE_CLASS_MAPPINGS = {
    "VideoSequenceController": VideoSequenceControllerNode,
    "VideoSequenceFeedback": VideoSequenceFeedbackNode,
    "VideoSequenceTrigger": VideoSequenceTriggerNode
}

# Optional: Add display names for the web UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoSequenceController": "Video Sequence Controller 🔄",
    "VideoSequenceFeedback": "Video Sequence Feedback 🔄",
    "VideoSequenceTrigger": "Video Sequence Trigger ➡️"
}
