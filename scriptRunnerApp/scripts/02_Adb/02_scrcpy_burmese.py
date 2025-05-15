import subprocess
import os
import sys

def run_scrcpy():
    """
    Runs scrcpy.exe with specified parameters.
    Script location: scripts\folder\script.py
    Target: utils\scrcpy\scrcpy-win64-v3.2\scrcpy.exe
    """
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Navigate to the project root (assuming scripts\folder\script.py structure)
    # Need to go up two levels from scripts\folder to reach project root
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    
    # Define the path to scrcpy.exe
    scrcpy_path = os.path.join(project_root, "utils", "scrcpy", "scrcpy-win64-v3.2", "scrcpy.exe")
    
    # Verify that scrcpy.exe exists at the specified path
    if not os.path.isfile(scrcpy_path):
        print(f"Error: scrcpy.exe not found at {scrcpy_path}")
        print("Please check the path and make sure scrcpy is installed correctly.")
        return False
    
    # Define the command to run
    command = [scrcpy_path, "-s", "localhost", "--no-audio", "-m2560"]
    
    print(f"Starting scrcpy from: {scrcpy_path}")
    print(f"Command: {' '.join(command)}")
    
    try:
        # Run scrcpy.exe
        process = subprocess.Popen(command)
        
        # You can choose to wait for the process to complete or continue with your script
        process.wait()  # Uncomment to wait for scrcpy to exit
        
        return True
    except Exception as e:
        print(f"Error running scrcpy: {e}")
        return False

if __name__ == "__main__":
    success = run_scrcpy()
    if success:
        print("scrcpy launched successfully.")
    else:
        print("Failed to launch scrcpy.")