import subprocess
import os
import sys
import argparse

def launch_adb_monitor(filter_text):
    """
    Launch ADB logcat monitor with specified filter text.
    
    Args:
        filter_text (str): Text to filter logcat output (required)
    """
    if not filter_text:
        print("Error: Filter text is required")
        return False
        
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the batch file (in the same directory)
    batch_path = os.path.join(script_dir, 'adb_monitor.bat')
    
    # Check if the batch file exists
    if not os.path.isfile(batch_path):
        print(f"Error: Batch file not found at {batch_path}")
        return False
    
    # Launch the batch file with the filter parameter
    cmd = ['cmd', '/c', 'start', 'cmd', '/k', batch_path, filter_text]
    
    print(f"Launching monitor with filter: {filter_text}")
    try:
        subprocess.Popen(cmd)
        return True
    except Exception as e:
        print(f"Error launching batch file: {e}")
        return False

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='ADB Logcat Monitor')
    parser.add_argument('--filter', '-f', type=str, required=True,
                        help='Text to filter in logcat (required)')
    
    # Parse command line arguments
    args = parser.parse_args()
    
    # Launch the monitor with the specified filter
    launch_adb_monitor(args.filter)