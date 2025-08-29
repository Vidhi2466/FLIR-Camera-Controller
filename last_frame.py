import PySpin
import tkinter as tk
from tkinter import Label
from PIL import Image, ImageTk
import numpy as np
from screeninfo import get_monitors
import os


class CameraManager:
    """Handles camera initialization, configuration, and cleanup"""
    
    def __init__(self):
        self.system = None
        self.cam_list = None
        self.cam = None
        self.nodemap = None
        self.acquisition_started = False
        
    def initialize(self):
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        
        if self.cam_list.GetSize() == 0:
            raise RuntimeError("No camera detected.")
            
        self.cam = self.cam_list.GetByIndex(0)
        self.cam.Init()
        self.nodemap = self.cam.GetNodeMap()
        return True
        
    def configure_camera(self):
        """Configure camera settings"""
        def set_node(node_name, value, node_type):
            try:
                node = node_type(self.nodemap.GetNode(node_name))
                if PySpin.IsWritable(node):
                    if isinstance(value, str):
                        node.SetIntValue(node.GetEntryByName(value).GetValue())
                    else:
                        node.SetValue(value)
                    print(f"{node_name}: {value}")
            except Exception as e:
                print(f"Could not set {node_name}: {e}")

        # Camera configuration settings
        settings = {
            "AcquisitionMode": ("Continuous", PySpin.CEnumerationPtr),
            "AcquisitionFrameRateEnable": (True, PySpin.CBooleanPtr),
            "AcquisitionFrameRate": (50.0, PySpin.CFloatPtr),
            "ExposureMode": ("Timed", PySpin.CEnumerationPtr),
            "ExposureAuto": ("Continuous", PySpin.CEnumerationPtr),
            "ExposureTime": (1609.0, PySpin.CFloatPtr),
            "AutoExposureTimeLowerLimit": (100.0, PySpin.CFloatPtr),
            "AutoExposureTimeUpperLimit": (50000.0, PySpin.CFloatPtr),
            "GainAuto": ("Off", PySpin.CEnumerationPtr),
            "Gain": (0.0, PySpin.CFloatPtr),
            "GammaEnable": (False, PySpin.CBooleanPtr),
            "Gamma": (0.8, PySpin.CFloatPtr),
            "BlackLevelSelector": ("All", PySpin.CEnumerationPtr),
            "BlackLevel": (0.0, PySpin.CFloatPtr),
            "BalanceRatioSelector": ("Red", PySpin.CEnumerationPtr),
            "BalanceRatio": (1.7, PySpin.CFloatPtr),
            "BalanceWhiteAuto": ("Continuous", PySpin.CEnumerationPtr),
            "DeviceLinkThroughputLimit": (380000000, PySpin.CIntegerPtr),
            "PixelFormat": ("Mono8", PySpin.CEnumerationPtr),
        }

        # Apply settings
        for node_name, (value, node_type) in settings.items():
            set_node(node_name, value, node_type)

        print("Camera configuration complete!")
        serial_number = PySpin.CStringPtr(self.cam.GetTLDeviceNodeMap().GetNode("DeviceSerialNumber")).ToString()
        print("serial number: ",serial_number)
        
    def start_acquisition(self):
        self.cam.BeginAcquisition()
        self.acquisition_started = True
        
    def is_streaming(self):
        try:
            return self.cam.IsStreaming() if self.cam else False
        except:
            return False
            
    def cleanup(self):
        try:
            if self.acquisition_started and self.is_streaming():
                self.cam.EndAcquisition()
                print("✓ Acquisition ended.")
        except Exception as e:
            print(f" Error ending acquisition: {e}")
            
        try:
            if self.cam:
                self.cam.DeInit()
                print("✓ Camera deinitialized.")
        except Exception as e:
            print(f" Error deinitializing camera: {e}")
            
        try:
            if self.cam:
                del self.cam
            if self.cam_list:
                self.cam_list.Clear()
            if self.system:
                self.system.ReleaseInstance()
            print("✓ System resources released.")
        except Exception as e:
            print(f" System cleanup error: {e}")

    
    
class ImageProcessor:
    """Handles image format conversion and processing"""
    
    def __init__(self):
        self.processor = PySpin.ImageProcessor()
        
    def process_image(self, image, format_name):
        """Process image based on format and return numpy array"""
        converters = {
            "Mono8": lambda img: self._convert_to_array(img, np.uint8),
            "Mono12Packed": lambda img: self._convert_to_array(self.processor.Convert(img, PySpin.PixelFormat_Mono16), np.uint16, shift=4),
            "Mono16": lambda img: self._convert_to_array(img, np.uint16),
            "RGB8": lambda img: self._convert_to_array(img, np.uint8, is_color=True),
            "BGR8": lambda img: self._convert_to_array(img, np.uint8, is_color=True),
        }
        if format_name.startswith("Bayer"):
            return self._convert_to_array(self.processor.Convert(image, PySpin.PixelFormat_RGB8), np.uint8, is_color=True)
        return converters.get(format_name, lambda img: self._convert_to_array(self.processor.Convert(img, PySpin.PixelFormat_Mono8), np.uint8))(image)

    def _convert_to_array(self, image, dtype, is_color=False, shift=None):
        """Convert image data to numpy array"""
        width, height = image.GetWidth(), image.GetHeight()
        array = np.frombuffer(image.GetData(), dtype=dtype).reshape((height, width, 3) if is_color else (height, width))
        if shift:
            array = array >> shift
        image.Release()
        return array, is_color


class DisplayManager:
    """Handles display window and image visualization"""
    
    def __init__(self):
        self.display_window = None
        self.image_label = None
        self.root = tk.Tk()
        self.root.withdraw()
        
    def create_display_window(self):
        monitors = get_monitors()
        monitor = monitors[1] if len(monitors) > 1 else monitors[0]

        win_width = monitor.width
        win_height = monitor.height
        x_pos = monitor.x - 8
        y_pos = monitor.y

        self.display_window = tk.Toplevel()
        self.display_window.title("Last Frame - Secondary Monitor")
        self.display_window.geometry(f"{win_width}x{win_height}+{x_pos}+{y_pos}")

        self.image_label = Label(self.display_window, text="Waiting for frames...", bg="black", fg="white")
        self.image_label.pack(expand=True, fill="both")

        # Prevent closing until finished
        self.display_window.protocol("WM_DELETE_WINDOW", lambda: None)
        
    def update_display(self, image_array, is_color=False):
        """Update display with new image"""
        if not self.display_window or not self.image_label:
            return
            
        try:
            # Handle 16-bit data for display
            if image_array.dtype == np.uint16:
                display_array = (image_array / 256).astype(np.uint8)
            else:
                display_array = image_array
            
            pil_image = Image.fromarray(display_array)
            pil_image.thumbnail((1920, 1080))
            photo = ImageTk.PhotoImage(pil_image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
            self.display_window.update()
        except Exception as e:
            print(f"Display error: {e}")
            
    def cleanup(self):
        try:
            if self.display_window:
                self.display_window.destroy()
                print("✓ Display window destroyed.")
        except Exception as e:
            print(f" Error destroying display: {e}")
            
        try:
            if self.root:
                self.root.destroy()
                print("✓ Tkinter root destroyed.")
        except Exception as e:
            print(f" Error destroying root: {e}")


class FrameAnalyzer:
    """Handles frame analysis and statistics"""

    @staticmethod
    def print_matrix_info(image_array, frame_number, format_name):
        """Print detailed matrix information"""
        bit_depth, max_possible, scale_name = FrameAnalyzer._get_bit_depth_info(image_array.dtype, format_name)
        dimensions = f"{image_array.shape[1]}W x {image_array.shape[0]}H"
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            dimensions += f" x {image_array.shape[2]}C"

        print(f"\n-> Frame #{frame_number} Matrix Information:")
        print(f"   -> Dimensions: {dimensions}")
        print(f"   -> Data type: {image_array.dtype} ({bit_depth})")
        print(f"   -> Possible range: 0 - {max_possible}")
        print(f"   -> Actual value range: {image_array.min()} - {image_array.max()}")
        print(f"   -> Size: {image_array.size} pixels ({image_array.nbytes} bytes)")
        if max_possible != "Unknown":
            utilization = (image_array.max() / max_possible) * 100
            brightness = (image_array.mean() / max_possible) * 100
            print(f"   -> Dynamic range utilization: {utilization:.1f}% of {scale_name}")
            print(f"   -> Brightness: {brightness:.1f}% of {scale_name}")
        print(f"   -> Format: {format_name}")
        print("-" * 60)

    @staticmethod
    def _get_bit_depth_info(dtype, format_name):
        """Get bit depth information based on data type and format"""
        bit_depth_map = {
            np.uint8: ("8-bit", 255, "8-bit scale"),
            np.uint16: ("12-bit", 4095, "12-bit scale") if format_name in ["Mono12Packed", "Mono12"] else ("16-bit", 65535, "16-bit scale"),
        }
        return bit_depth_map.get(dtype, ("Unknown", "Unknown", "Unknown"))
    

class FrameCaptureManager:
    # Manages capturing, saving, analyzing, and displaying a single frame.

    def __init__(self, camera_manager, image_processor, display_manager, frames_folder, csv_folder):
        self.camera_manager = camera_manager
        self.image_processor = image_processor
        self.display_manager = display_manager
        self.frames_folder = frames_folder
        self.csv_folder = csv_folder

    def capture_and_process_frame(self, frame_number):
        if not self.display_manager.display_window:
            self.display_manager.create_display_window()

        self.camera_manager.start_acquisition()
        image = self.camera_manager.cam.GetNextImage()

        if image.IsIncomplete():
            image.Release()
            raise RuntimeError("Incomplete image received.")

        format_name = image.GetPixelFormatName()
        print(f"Image format: {format_name}")

        array, is_color = self.image_processor.process_image(image, format_name)
        print(f"Processed array shape: {array.shape if array is not None else 'None'}")

        # Save .npy
        np.save(os.path.join(self.frames_folder, f"last_frame_{frame_number:06d}.npy"), array)

        # Save .csv
        filepath_csv = os.path.join(self.csv_folder, f"last_frame_{frame_number:06d}.csv")
        if len(array.shape) == 3:
            reshaped = array.reshape(array.shape[0], -1)
            np.savetxt(filepath_csv, reshaped, delimiter=',', fmt='%d')
        else:
            np.savetxt(filepath_csv, array, delimiter=',', fmt='%d')

        # Analyze and display
        FrameAnalyzer.print_matrix_info(array, frame_number, format_name)
        self.display_manager.update_display(array, is_color)
        if self.display_manager.display_window:
            self.display_manager.display_window.update_idletasks()
            self.display_manager.display_window.update()

        image.Release()

        if self.camera_manager.acquisition_started and self.camera_manager.is_streaming():
            self.camera_manager.cam.EndAcquisition()
            self.camera_manager.acquisition_started = False

        return array, format_name
