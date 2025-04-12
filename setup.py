from setuptools import setup, find_packages

setup(
    name='comfyui_video_sequence_controller',
    version='0.1.0',  # Plan v1
    packages=find_packages(),
    description='A ComfyUI custom node to control iterative video segment processing in a workflow.',
    author='hagenland',
    install_requires=[
        # List external dependencies if needed.
    ],
    entry_points={
        "comfyui.nodes": [
            "video_sequence_controller = node.video_sequence_controller:VideoSequenceControllerNode"
        ],
    },
)


entry_points={
    "comfyui.nodes": [
        "video_sequence_controller = node.video_sequence_controller:VideoSequenceControllerNode"
    ],
},
