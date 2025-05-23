import customtkinter as ctk
import os
import subprocess
import tkinter as tk
from tkinter import scrolledtext
import threading

class ScriptRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Script Runner")
        self.root.geometry("500x400")

        # Set CustomTkinter appearance
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Create main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabview (upper 2/3)
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, side="top")

        # Create console (lower 1/3)
        self.console = scrolledtext.ScrolledText(self.main_frame, height=200, wrap=tk.WORD, state='disabled')
        self.console.pack(fill="both", expand=False, padx=5, pady=5, side="bottom")

        # Load scripts and populate tabs
        self.scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
        self.load_scripts()

    def load_scripts(self):
        """Load scripts from the scripts folder and populate tabs."""
        if not os.path.exists(self.scripts_dir):
            self.log_to_console("Scripts directory not found!")
            return

        # Get list of subfolders and sort by number
        subfolders = [f for f in os.listdir(self.scripts_dir) if os.path.isdir(os.path.join(self.scripts_dir, f))]
        subfolders.sort(key=lambda x: int(x.split('_')[0]) if '_' in x else 999)

        for folder in subfolders:
            # Extract tab name (remove number and underscore)
            tab_name = ' '.join(folder.split('_')[1:]).replace('.py', '').title()
            self.tabview.add(tab_name)
            tab_frame = self.tabview.tab(tab_name)

            # Get scripts in the subfolder
            folder_path = os.path.join(self.scripts_dir, folder)
            scripts = [f for f in os.listdir(folder_path) if f.endswith('.py')]
            scripts.sort(key=lambda x: int(x.split('_')[0]) if '_' in x else 999)

            # Create buttons for each script, up to 3 per row
            row_frame = None
            for i, script in enumerate(scripts):
                # Create a new row frame for every 3 buttons
                if i % 3 == 0:
                    row_frame = ctk.CTkFrame(tab_frame, fg_color="transparent")
                    row_frame.pack(pady=5, fill="x")
                
                button_name = ' '.join(script.split('_')[1:]).replace('.py', '').title()
                script_path = os.path.join(folder_path, script)
                button = ctk.CTkButton(
                    master=row_frame,
                    text=button_name,
                    command=lambda path=script_path: self.run_script(path)
                )
                button.pack(pady=5, padx=10, side="left", expand=True, fill="x")

    def run_script(self, script_path):
        """Run a script in a separate thread and display output in console."""
        def script_thread():
            try:
                self.log_to_console(f"Running {os.path.basename(script_path)}...\n")
                result = subprocess.run(
                    ['python', script_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                self.log_to_console(result.stdout)
                if result.stderr:
                    self.log_to_console(f"Errors:\n{result.stderr}")
            except subprocess.TimeoutExpired:
                self.log_to_console(f"Error: {os.path.basename(script_path)} timed out after 30 seconds.")
            except Exception as e:
                self.log_to_console(f"Error running {os.path.basename(script_path)}: {str(e)}")

        threading.Thread(target=script_thread, daemon=True).start()

    def log_to_console(self, message):
        """Log messages to the console."""
        self.console.configure(state='normal')
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.configure(state='disabled')

if __name__ == "__main__":
    root = ctk.CTk()
    app = ScriptRunnerApp(root)
    root.mainloop()