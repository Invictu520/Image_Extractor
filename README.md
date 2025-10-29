# 🎬 Video Frame Extractor with Optional GroundingDINO Cropping

A Python tool to automatically extract frames from videos — with an optional feature to use **GroundingDINO** for detecting and cropping specific objects (e.g., “orange”) in each extracted frame.

The script runs fully interactively: when you start it, it asks whether you want to only extract frames or also apply GroundingDINO-based object cropping.

---

## 🚀 Features

* **Two modes of operation:**
  1. **Frame Extraction Only** – Extract all frames from videos into organized folders.
  2. **GroundingDINO Cropping** – Detect a specific object from a text prompt (e.g., “orange”) and crop each frame around it.

* **Multi-format video support:** Works with `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`, `.mpeg`, and `.mpg`.
* **Clean and organized output:** Automatically creates subfolders for frames and cropped results.
* **Interactive use:** No command-line flags required — just answer simple prompts when you run the script.
* **Warning suppression:** Automatically hides irrelevant library warnings (like `timm` or PyTorch).

---

## 📋 Requirements

- Python 3.8 or newer  
- [OpenCV](https://pypi.org/project/opencv-python/)  
- [tqdm](https://pypi.org/project/tqdm/)  
- [GroundingDINO](https://github.com/IDEA-Research/GroundingDINO) (optional — only required for cropping mode)  

---

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/Invictu520/Image_Extractor.git
cd Image_Extractor
```

### 2. Install dependencies
If you plan to **only extract frames**:
```bash
pip install opencv-python tqdm
```

If you also want to use **GroundingDINO cropping**, install its dependencies as well:

#### a) Clone GroundingDINO inside your repository
```bash
git clone https://github.com/IDEA-Research/GroundingDINO.git
```

#### b) Install GroundingDINO
```bash
cd GroundingDINO
pip install -e .
```

#### c) Download pretrained model weights
```bash
mkdir weights
cd weights
wget https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth
cd ../..
```

> 💡 If `wget` is unavailable (Windows), use PowerShell:
> ```bash
> Invoke-WebRequest -Uri "https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth" -OutFile "groundingdino_swint_ogc.pth"
> ```

---

## ▶️ How to Use

You can run the script from either the **terminal** or any **Python IDE** (like PyCharm, VS Code, or Spyder).

### 💻 From the terminal

1. Navigate to the folder where `video_extractor.py` (or your main script) is located:
   ```bash
   cd ~/Desktop/Image_Extractor
   ```

2. Run it:
   ```bash
   python video_extractor.py
   ```

3. Follow the prompts:
   ```
   === 🎥 Frame Extraction & Optional GroundingDINO Cropping ===
   Enter the path to your video folder: D:\Videos\oranges
   Enter the output directory: D:\orange_job
   Do you want to use GroundingDINO for object localization and cropping? (y/n): y
   Enter your text prompt (e.g., 'orange'): orange
   Enter box threshold [default 0.35]:
   Enter text threshold [default 0.25]:
   Run on CPU or CUDA? [cpu/cuda, default=cpu]: cuda
   ```

4. When complete, you’ll be asked if you want to delete the raw frames:
   ```
   Delete raw frames after cropping? (y/n): y
   ```

---

### 🧠 Example File Structure

#### Before
```bash
/User/Project/
└── MyVideos/
    ├── oranges.mp4
    └── apples.mov
```

#### After (frame extraction only)
```bash
/User/Project/
├── MyVideos/
│   ├── oranges.mp4
│   └── apples.mov
└── Output/
    └── frames/
        ├── oranges/
        │   ├── oranges_frame_000000.jpg
        │   ├── oranges_frame_000001.jpg
        │   └── ...
        └── apples/
            ├── apples_frame_000000.jpg
            └── ...
```

#### After (with GroundingDINO)
```bash
/User/Project/
└── Output/
    ├── frames/                # temporary extracted frames (optional)
    └── cropped/               # final cropped images
        ├── oranges/
        │   ├── oranges_frame_000000.jpg
        │   ├── oranges_frame_000001.jpg
        │   └── ...
        └── apples/
            ├── apples_frame_000000.jpg
            └── ...
```

---

## ⚙️ Configuration (interactive)

When running GroundingDINO mode, you’ll be prompted to enter:

| Setting | Description | Default |
|----------|--------------|----------|
| **Text Prompt** | What object to detect (e.g., “orange”, “bottle”, “apple”) | `"orange"` |
| **Box Threshold** | Minimum confidence for object bounding boxes | `0.35` |
| **Text Threshold** | Minimum confidence for text–object match | `0.25` |
| **Device** | Compute device: `"cpu"` or `"cuda"` | `"cpu"` |

---

## ❓ Troubleshooting

- **GroundingDINO import error:** Make sure you installed it via `pip install -e .` inside the cloned GroundingDINO directory.  
- **Missing weights file:** Place the downloaded `.pth` file inside `GroundingDINO/weights/`.  
- **CUDA issues:** Run on CPU by selecting `cpu` when prompted.  

---

## 🏁 Summary

| Mode | Description | Output |
|------|--------------|--------|
| **Frame Extraction Only** | Extracts all frames from each video | `/Output/frames` |
| **GroundingDINO Cropping** | Detects an object and crops each frame accordingly | `/Output/cropped` |

---

## 🙌 Acknowledgements

This project uses the [GroundingDINO](https://github.com/IDEA-Research/GroundingDINO) model for object detection.
Special thanks to the IDEA-Research team for their open-source work.
