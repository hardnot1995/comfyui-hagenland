# comfyui-hagenland/__init__.py

from .node import (
    VideoSequenceControllerNode,
    VideoSequenceFeedbackNode,
    VideoSequenceTriggerNode,
    ValueSchedulerNode,
    StringSchedulerNode,
    IntSchedulerNode,
    FloatSchedulerNode,
    ScheduledPromptNode
)

# Define NODE_CLASS_MAPPINGS so ComfyUI can find your custom nodes.
NODE_CLASS_MAPPINGS = {
    "VideoSequenceController": VideoSequenceControllerNode,
    "VideoSequenceFeedback": VideoSequenceFeedbackNode,
    "VideoSequenceTrigger": VideoSequenceTriggerNode,
    "ScheduledPrompt": ScheduledPromptNode,
    "ValueScheduler": ValueSchedulerNode,
    "StringScheduler": StringSchedulerNode,
    "IntScheduler": IntSchedulerNode,
    "FloatScheduler": FloatSchedulerNode,
}

# Optional: Add display names for the web UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoSequenceController": "Video Sequence Controller 🎥",
    "VideoSequenceFeedback": "Video Sequence Feedback 📝",
    "VideoSequenceTrigger": "Video Sequence Trigger ⚡",
    "ScheduledPrompt": "Scheduled Prompt 📝",
    "ValueScheduler": "Value Scheduler 📅 (*)",
    "StringScheduler": "String Scheduler 📅 (Abc)",
    "IntScheduler": "Int Scheduler 📅 (123)",
    "FloatScheduler": "Float Scheduler 📅 (1.23)",
}
