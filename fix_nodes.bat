@echo off
setlocal

echo Fixing ComfyUI custom nodes...

REM Stop any running ComfyUI instances
taskkill /f /im python.exe >nul 2>&1

REM Define paths
set COMFY_ROOT=C:\sd\ComfyUI_windows_portable
set CUSTOM_NODES=%COMFY_ROOT%\ComfyUI\custom_nodes
set SOURCE_DIR=%CUSTOM_NODES%\comfyui-hagenland
set BACKUP_DIR=%COMFY_ROOT%\node_backup

echo Creating backup of current nodes...
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
xcopy /E /I /Y "%SOURCE_DIR%" "%BACKUP_DIR%\comfyui-hagenland"

echo Cleaning up cache files...
for /d /r "%SOURCE_DIR%" %%d in (__pycache__) do (
    if exist "%%d" rd /s /q "%%d"
)

echo Updating node init files...

REM Fix main __init__.py - create with correct encoding
echo # comfyui-hagenland/__init__.py > "%SOURCE_DIR%\__init__.py.new"
echo. >> "%SOURCE_DIR%\__init__.py.new"
echo # Import your node classes from the node subpackage. >> "%SOURCE_DIR%\__init__.py.new"
echo try: >> "%SOURCE_DIR%\__init__.py.new"
echo     from node.video_sequence_controller import VideoSequenceControllerNode, VideoSequenceFeedbackNode, VideoSequenceTriggerNode, VideoSequenceMonitorNode >> "%SOURCE_DIR%\__init__.py.new"
echo except ImportError: >> "%SOURCE_DIR%\__init__.py.new"
echo     import sys, os >> "%SOURCE_DIR%\__init__.py.new"
echo     sys.path.append(os.path.dirname(os.path.abspath(__file__))) >> "%SOURCE_DIR%\__init__.py.new"
echo     from node.video_sequence_controller import VideoSequenceControllerNode, VideoSequenceFeedbackNode, VideoSequenceTriggerNode, VideoSequenceMonitorNode >> "%SOURCE_DIR%\__init__.py.new"
echo. >> "%SOURCE_DIR%\__init__.py.new"
echo. >> "%SOURCE_DIR%\__init__.py.new"
echo # Define NODE_CLASS_MAPPINGS so ComfyUI can find your custom nodes. >> "%SOURCE_DIR%\__init__.py.new"
echo NODE_CLASS_MAPPINGS = { >> "%SOURCE_DIR%\__init__.py.new"
echo     "VideoSequenceController": VideoSequenceControllerNode, >> "%SOURCE_DIR%\__init__.py.new"
echo     "VideoSequenceFeedback": VideoSequenceFeedbackNode, >> "%SOURCE_DIR%\__init__.py.new"
echo     "VideoSequenceTrigger": VideoSequenceTriggerNode, >> "%SOURCE_DIR%\__init__.py.new"
echo     "VideoSequenceMonitor": VideoSequenceMonitorNode >> "%SOURCE_DIR%\__init__.py.new"
echo } >> "%SOURCE_DIR%\__init__.py.new"
echo. >> "%SOURCE_DIR%\__init__.py.new"
echo # Optional: Add display names for the web UI >> "%SOURCE_DIR%\__init__.py.new"
echo NODE_DISPLAY_NAME_MAPPINGS = { >> "%SOURCE_DIR%\__init__.py.new"
echo     "VideoSequenceController": "Video Sequence Controller", >> "%SOURCE_DIR%\__init__.py.new"
echo     "VideoSequenceFeedback": "Video Sequence Feedback", >> "%SOURCE_DIR%\__init__.py.new"
echo     "VideoSequenceTrigger": "Video Sequence Trigger", >> "%SOURCE_DIR%\__init__.py.new"
echo     "VideoSequenceMonitor": "Video Sequence Monitor" >> "%SOURCE_DIR%\__init__.py.new"
echo } >> "%SOURCE_DIR%\__init__.py.new"

move /Y "%SOURCE_DIR%\__init__.py.new" "%SOURCE_DIR%\__init__.py"

REM Fix node/__init__.py
echo from .video_sequence_controller import VideoSequenceControllerNode, VideoSequenceFeedbackNode, VideoSequenceTriggerNode, VideoSequenceMonitorNode > "%SOURCE_DIR%\node\__init__.py"

echo Creating required directories...
if not exist "%COMFY_ROOT%\ComfyUI\hagenland_state" mkdir "%COMFY_ROOT%\ComfyUI\hagenland_state"
if not exist "%COMFY_ROOT%\ComfyUI\output" mkdir "%COMFY_ROOT%\ComfyUI\output"

echo Starting ComfyUI...
cd "%COMFY_ROOT%"
start cmd /k ".\python_embeded\python.exe .\ComfyUI\main.py --port 8188 --listen 0.0.0.0"

echo Done! ComfyUI should be starting now with fixed nodes.
echo If you still experience issues, please restart your computer and try again.

endlocal 