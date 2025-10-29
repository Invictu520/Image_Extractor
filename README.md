# 🎬 Video Frame Extractor

A simple Python script to automatically scan a folder for video files, extract all individual frames from each video, and save them as organized PNG images.

This script uses **OpenCV** to efficiently process video files.

---

## 🚀 Features

* **Multi-Format Support:** Scans for and processes common video formats (e.g., `.mp4`, `.avi`, `.mov`, `.mkv`).
* **Organized Output:** Creates a single `Extracted_Images` folder in the *parent directory* of your input folder to keep your source files clean.
* **Clear Naming Convention:** Saves extracted frames with a systematic filename that references the original video and the frame number (e.g., `my_video_name_frame_000001.jpg`).
* **Simple to Use:** Just run the script and provide the path to your video folder.

---

## 📋 Requirements

* Python 3.x
* OpenCV for Python

---

## 🛠️ Installation

1.  **Clone the repository (or download `extract_frames.py`):**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git)
    cd YOUR_REPOSITORY
    ```

2.  **Install the required package (OpenCV):**
    ```bash
    pip install opencv-python
    ```

---

## ▶️ How to Use

1.  Run the script from your terminal:
    ```bash
    python extract_frames.py
    ```

2.  When prompted, provide the full path to the folder containing your videos. You can often drag and drop the folder onto the terminal window to paste the path.

    ```
    Enter the full path to your video folder: /Users/yourname/Desktop/MyVideos
    ```

3.  The script will scan the folder, process all found videos, and save the extracted frames into the `Extracted_Images` folder.

---

## 📁 Example File Structure

Here is how the script organizes your files.

**Before:**
/User/Project/
└── MyVideos/
    ├── cool_video_1.mp4
    └── holiday_footage.mov


**After running the script:**
/User/Project/
├── MyVideos/
│   ├── cool_video_1.mp4
│   └── holiday_footage.mov
└── Extracted_Images/
    ├── cool_video_1_frame_000000.jpg
    ├── cool_video_1_frame_000001.jpg
    ├── cool_video_1_frame_000002.jpg
    ├── ...
    ├── holiday_footage_frame_000000.jpg
    ├── holiday_footage_frame_000001.jpg
    └── ...
