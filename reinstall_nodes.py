import os
import shutil
import sys

def reinstall_nodes():
    """
    Remove existing custom node directories and reinstall them fresh
    """
    comfyui_root = 'ComfyUI'
    custom_nodes_dir = os.path.join(comfyui_root, 'custom_nodes')
    
    # Paths to our source and destinations
    source_dir = os.path.join(custom_nodes_dir, 'comfyui-hagenland')  # Source is already in custom_nodes
    destination_hyphen = os.path.join(custom_nodes_dir, 'comfyui-hagenland')
    destination_underscore = os.path.join(custom_nodes_dir, 'comfyui_hagenland')
    
    # Create required directories
    os.makedirs(os.path.join(comfyui_root, 'hagenland_state'), exist_ok=True)
    os.makedirs(os.path.join(comfyui_root, 'output'), exist_ok=True)
    
    # If source doesn't exist, we can't continue
    if not os.path.exists(source_dir):
        print(f"Error: Source directory does not exist: {source_dir}")
        return
    
    # Remove underscore version if it exists (we'll leave the original hyphen version)
    print("Removing underscore version if it exists...")
    if os.path.exists(destination_underscore):
        try:
            shutil.rmtree(destination_underscore)
            print(f"Removed: {destination_underscore}")
        except Exception as e:
            print(f"Error removing {destination_underscore}: {e}")
    
    # Copy our custom node directory to the underscore version
    print("\nCopying custom nodes...")
    try:
        shutil.copytree(source_dir, destination_underscore)
        print(f"Copied to: {destination_underscore}")
        
        print("\nInstallation complete! Please restart ComfyUI.")
    except Exception as e:
        print(f"Error during copy: {e}")

if __name__ == "__main__":
    print("Starting reinstallation of custom nodes...")
    reinstall_nodes() 