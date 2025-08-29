# FLIR Blackfly S Camera Controller 📸

A Python-based graphical user interface (GUI) for controlling a FLIR Blackfly S camera. This application allows for camera initialization, single-frame capture, real-time display on a secondary monitor, and data storage in both NumPy (`.npy`) and CSV (`.csv`) formats.

The application is built using `tkinter` for the GUI and leverages the `PySpin` (Spinnaker SDK) library for camera interaction, `NumPy` for data manipulation, and `Pillow` for display.

---
## 📋 Camera Specifications

This code was developed for the following camera model, based on the provided documentation:

| Specification         | Details                                       |
| --------------------- | --------------------------------------------- |
| **Model** | Blackfly S BFS-U3-51S5C-C                       |
| **Sensor** | Sony IMX250                                   |
| **Resolution** | 2448 x 2048                                   |
| **Megapixels** | 5.0 MP                                        |
| **Spectrum** | Color                                         |
| **Interface** | USB 3.0                                       |
| **Max Frame Rate** | 75 FPS                                        |
| **Sensor Type** | CMOS, Global Shutter                          |
| **Digitization Depth**| 10-bit, 12-bit                                |

---
## ✨ Features

* **Simple GUI**: Easy-to-use interface with buttons to open, close, and capture frames from the camera.
* **Secondary Monitor Display**: Automatically displays the last captured frame on a secondary monitor for easy viewing.
* **Frame Analysis**: Prints detailed matrix information for each captured frame to the console, including dimensions, data type, dynamic range utilization, and brightness.
* **Dual-Format Saving**: Each captured frame is saved simultaneously as:
    * A **NumPy array (`.npy`)** for efficient data analysis in Python.
    * A **Comma-Separated Values file (`.csv`)** for compatibility with spreadsheets and other software.
* **Robust Configuration**: The `CameraManager` class sets specific camera parameters like frame rate, exposure, and gain.

---
## 🔧 Code Structure

The project's logic is split into two main files: `GUI.py` for the user interface and `last_frame.py` for all the backend functionality.

### `last_frame.py`

This file contains the core logic, organized into a modular, class-based structure. Each class has a specific responsibility:

* **`CameraManager`**: Handles all direct communication with the camera hardware using the `PySpin` library. Its responsibilities include discovering, initializing, configuring camera settings (e.g., `AcquisitionFrameRate`, `ExposureTime`, `Gain`), and properly de-initializing the camera.
* **`ImageProcessor`**: Responsible for converting raw image data received from the camera into a standardized NumPy array. It handles various pixel formats (like `Mono8`, `Mono12Packed`, and Bayer formats) and ensures the output is ready for analysis and display.
* **`DisplayManager`**: Manages all visual output. It creates a `tkinter` window, intelligently places it on a secondary monitor if one is available, and updates it with the most recently captured frame. It also handles the conversion of high-bit-depth NumPy arrays into 8-bit images suitable for display using the `Pillow` library.
* **`FrameAnalyzer`**: A utility class with static methods to analyze a captured frame. After a frame is converted to a NumPy array, this class prints detailed statistics to the console, including image dimensions, data type, and pixel value range.
* **`FrameCaptureManager`**: Acts as the orchestrator for the entire capture-to-save workflow. It uses the other classes to acquire an image, process it, save it, display it, and trigger its analysis.

---
### 🖥️ Monitor Configuration Note

By default, the application is optimized for a **dual-monitor setup**. The code automatically attempts to open the frame display window on your secondary monitor.

If you are using a **single-monitor setup**, or wish to force the display onto your primary monitor, you must make a small change in the `last_frame.py` file.

* **File**: `last_frame.py`
* **Class**: `DisplayManager`
* **Method**: `create_display_window`

**Change this line:**
```python
monitor = monitors[1] if len(monitors) > 1 else monitors[0]
```


**To this:**
```python
monitor = monitors[0]
```
This change ensures the display window will always open on your main monitor.

---
## ⚙️ Setup and Installation

### 1. Prerequisites
[Before running the software, you must install the **FLIR Spinnaker SDK**.] `PySpin` is a Python wrapper for this SDK and requires it to function.

* Download the latest SDK from the [FLIR website](https://www.flir.com/mv-techsupport/downloads).
* Ensure the camera is properly connected to a USB 3.0 port on your computer.

### 2. Clone the Repository
```bash
git clone <your-repository-url>
cd FLIR-Camera-Controller
```

### 3. Install Python Dependencies
This project requires Python 3. The necessary libraries are listed in the `requirements.txt` file. Install them using pip:
```bash
pip install -r requirements.txt
```

---
## 🚀 Usage

1.  Ensure your FLIR camera is connected and the Spinnaker SDK is installed.
2.  Run the main GUI script from your terminal:
    ```bash
    python GUI.py
    ```
   
3.  The control window will appear on your primary monitor.
    * **Open Camera**: Initializes the camera with the predefined settings.
    * **Obtain Last Frame**: Captures a single frame, displays it, saves it to the `frames/` and `csv_data/` folders, and prints analysis to the console.
    * **Close Camera**: Properly de-initializes the camera and closes the display window.

### Output
The script will automatically create two folders in the project directory:
* `frames/`: Contains the captured images saved as `.npy` files.
* `csv_data/`: Contains the captured images saved as `.csv` files.