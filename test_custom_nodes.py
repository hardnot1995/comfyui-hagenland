import os
import sys
import importlib.util

# Add ComfyUI to the path
sys.path.append(os.path.abspath('./ComfyUI'))

# Try to import the custom nodes
def test_import():
    try:
        # Try direct import
        print("Attempting direct import...")
        from custom_nodes.comfyui_hagenland import NODE_CLASS_MAPPINGS
        print("Success! Found nodes:", list(NODE_CLASS_MAPPINGS.keys()))
    except ImportError as e:
        print(f"Direct import failed: {e}")
        
        try:
            # Try import with spec
            print("\nAttempting import with spec...")
            spec = importlib.util.spec_from_file_location(
                'comfyui_hagenland', 
                './ComfyUI/custom_nodes/comfyui-hagenland/__init__.py'
            )
            if spec is None:
                print("Failed: spec is None, file may not exist")
            else:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print("Success! Found nodes:", list(module.NODE_CLASS_MAPPINGS.keys()))
        except Exception as e:
            print(f"Import with spec failed: {e}")
            
            try:
                # Try alternate hyphenated directory name
                print("\nAttempting with alternate directory name...")
                spec = importlib.util.spec_from_file_location(
                    'comfyui_hagenland', 
                    './ComfyUI/custom_nodes/comfyui_hagenland/__init__.py'
                )
                if spec is None:
                    print("Failed: spec is None, file may not exist")
                else:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    print("Success! Found nodes:", list(module.NODE_CLASS_MAPPINGS.keys()))
            except Exception as e:
                print(f"Alternate directory name import failed: {e}")

if __name__ == "__main__":
    print("Current working directory:", os.getcwd())
    print("Checking custom nodes directory exists...")
    
    custom_nodes_path = os.path.join('.', 'ComfyUI', 'custom_nodes')
    if os.path.exists(custom_nodes_path):
        print(f"Custom nodes directory exists at: {os.path.abspath(custom_nodes_path)}")
        
        # List contents of custom_nodes directory
        print("\nContents of custom_nodes directory:")
        for item in os.listdir(custom_nodes_path):
            item_path = os.path.join(custom_nodes_path, item)
            if os.path.isdir(item_path):
                print(f"  📁 {item}")
            else:
                print(f"  📄 {item}")
                
        # Specifically check for our custom nodes
        hagenland_path = os.path.join(custom_nodes_path, 'comfyui-hagenland')
        if os.path.exists(hagenland_path):
            print(f"\nFound hagenland directory at: {hagenland_path}")
            
            # List contents of hagenland directory
            print("Contents of hagenland directory:")
            for item in os.listdir(hagenland_path):
                item_path = os.path.join(hagenland_path, item)
                if os.path.isdir(item_path):
                    print(f"  📁 {item}")
                else:
                    print(f"  📄 {item}")
            
            # Check for init file
            init_path = os.path.join(hagenland_path, '__init__.py')
            if os.path.exists(init_path):
                print(f"\nFound __init__.py at: {init_path}")
                
                # Print content of init file
                print("Content of __init__.py:")
                with open(init_path, 'r') as f:
                    print(f.read())
                
                # Try to import
                test_import()
            else:
                print(f"ERROR: __init__.py not found at: {init_path}")
        else:
            print(f"\nERROR: hagenland directory not found at: {hagenland_path}")
            
            # Check for alternative names
            for item in os.listdir(custom_nodes_path):
                if 'hagenland' in item.lower():
                    print(f"Found similar directory: {item}")
    else:
        print(f"ERROR: Custom nodes directory not found at: {os.path.abspath(custom_nodes_path)}") 