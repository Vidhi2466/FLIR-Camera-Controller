import tkinter as tk
from tkinter import messagebox
from last_frame import CameraManager, ImageProcessor, DisplayManager, FrameCaptureManager
import os


class CameraGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Camera Controller - Primary Monitor")
        self.root.geometry("400x200")

        self.camera_manager, self.image_processor, self.display_manager = CameraManager(), ImageProcessor(), DisplayManager()
        self.frame_number, self.last_frame_array, self.original_format_name = 1, None, "Unknown"

        self.frames_folder, self.csv_folder = "frames", "csv_data"
        os.makedirs(self.frames_folder, exist_ok=True); os.makedirs(self.csv_folder, exist_ok=True)

        self.create_widgets()

    def create_widgets(self):
        for text, command in [(" Open Camera", self.initialize_camera), 
                              (" Obtain Last Frame", self.get_last_frame), 
                              (" Close Camera", self.close_camera)]:
            tk.Button(self.root, text=text, width=25, height=2, command=command).pack(pady=10)

    def initialize_camera(self):
        try:
            self.camera_manager.initialize(); self.camera_manager.configure_camera(); self.display_manager.create_display_window()
            messagebox.showinfo("Success", "Camera initialized successfully.")
        except Exception as e:
            messagebox.showerror("Initialization Error", str(e))
        

    def get_last_frame(self):
        try:
            frame_manager = FrameCaptureManager(self.camera_manager, self.image_processor, self.display_manager, self.frames_folder, self.csv_folder)
            self.last_frame_array, self.original_format_name = frame_manager.capture_and_process_frame(self.frame_number); self.frame_number += 1
        except Exception as e:
            import traceback; traceback.print_exc(); messagebox.showerror("Capture Error", str(e))


    def close_camera(self):
        try:
            self.camera_manager.cleanup(); self.display_manager.cleanup()
            messagebox.showinfo("Closed", "Camera closed and display cleaned up.")
        except Exception as e:
            messagebox.showerror("Cleanup Error", str(e))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = CameraGUI()
    app.run()


