import subprocess
import os
import sys

#############################################################
#                   CONFIGURATION                           #
#############################################################
# CHANGE THIS VALUE to set your filter text
FILTER_TEXT = "validate"
#############################################################

def run_logcat_monitor():
    """
    Runs the ADB logcat monitor with the configured filter.
    """
    # Get the path to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Calculate the path to the utils directory
    # Assuming directory structure: project_root/scripts/another_folder/run_logcat.py
    #                               project_root/utils/adb_monitor.py
    utils_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "utils"))
    
    # Path to the main Python script
    monitor_script = os.path.join(utils_dir, "adb_monitor.py")
    
    # Check if the script exists
    if not os.path.isfile(monitor_script):
        print(f"Error: Monitor script not found at {monitor_script}")
        return False
    
    # Run the monitor script with the filter parameter from configuration
    print(f"Running ADB monitor with filter: {FILTER_TEXT}")
    try:
        # Run the Python script with the filter parameter
        subprocess.Popen([sys.executable, monitor_script, "-f", FILTER_TEXT])
        return True
    except Exception as e:
        print(f"Error running ADB monitor: {e}")
        return False

if __name__ == "__main__":
    # Run the logcat monitor with the configured filter
    run_logcat_monitor()