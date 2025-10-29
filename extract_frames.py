#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import cv2
from tqdm import tqdm
import shutil
import warnings

# Suppress noisy library warnings before user input
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Try importing GroundingDINO (optional dependency)
try:
    from groundingdino.util.inference import load_model, load_image, predict
except Exception:
    load_model = None
    load_image = None
    predict = None


VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpeg', '.mpg'}


def extract_frames(input_videos_dir, output_frames_dir, image_ext="png", every_nth=1, per_video_subfolders=True):
    """Extract frames from all videos in a folder."""
    os.makedirs(output_frames_dir, exist_ok=True)
    video_files = [f for f in os.listdir(input_videos_dir) if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS]
    if not video_files:
        print("No videos found.")
        return
    for filename in tqdm(video_files, desc="Extracting frames"):
        base, _ = os.path.splitext(filename)
        video_path = os.path.join(input_videos_dir, filename)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Could not open {video_path}")
            continue
        out_dir = os.path.join(output_frames_dir, base) if per_video_subfolders else output_frames_dir
        os.makedirs(out_dir, exist_ok=True)
        frame_idx = 0
        saved_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if every_nth <= 1 or (frame_idx % every_nth == 0):
                out_path = os.path.join(out_dir, f"{base}_frame_{saved_idx:06d}.{image_ext}")
                cv2.imwrite(out_path, frame)
                saved_idx += 1
            frame_idx += 1
        cap.release()
    print(f"✅ Frames extracted to {output_frames_dir}")


def ensure_dino():
    """Check if GroundingDINO is installed."""
    if load_model is None or load_image is None or predict is None:
        print("❌ GroundingDINO not available — please install or check imports.")
        sys.exit(1)


def run_dino_crop(images_root, crops_out,
                  caption="orange", box_threshold=0.35, text_threshold=0.25,
                  model_config="GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py",
                  model_weights="GroundingDINO/weights/groundingdino_swint_ogc.pth",
                  device="cpu"):
    """Run GroundingDINO detection and crop around largest detected object."""
    ensure_dino()
    os.makedirs(crops_out, exist_ok=True)

    print("\n🔧 Loading GroundingDINO model...")
    model = load_model(model_config, model_weights)

    image_paths = []
    for root, _, files in os.walk(images_root):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_paths.append(os.path.join(root, f))
    if not image_paths:
        print("No images found for DINO.")
        return

    for fpath in tqdm(image_paths, desc="Cropping with GroundingDINO"):
        try:
            _, img_tensor = load_image(fpath)
        except Exception as e:
            print(f"Failed to load {fpath}: {e}")
            continue

        boxes, _, _ = predict(
            model=model,
            image=img_tensor,
            device=device,
            caption=caption,
            box_threshold=box_threshold,
            text_threshold=text_threshold
        )

        bgr = cv2.imread(fpath)
        if bgr is None:
            continue
        H, W = bgr.shape[:2]
        if len(boxes) == 0:
            continue

        # Select the largest detection box
        areas = [(b[2] * b[3]) for b in boxes]
        idx = int(max(range(len(areas)), key=lambda i: areas[i]))
        cx, cy, w, h = boxes[idx].tolist()
        x1 = int((cx - w / 2) * W)
        y1 = int((cy - h / 2) * H)
        x2 = int((cx + w / 2) * W)
        y2 = int((cy + h / 2) * H)
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(W, x2), min(H, y2)

        crop = bgr[y1:y2, x1:x2]

        rel = os.path.relpath(fpath, images_root)
        base = os.path.splitext(os.path.basename(rel))[0]
        out_dir = os.path.join(crops_out, os.path.dirname(rel))
        os.makedirs(out_dir, exist_ok=True)
        crop_path = os.path.join(out_dir, f"{base}.jpg")
        cv2.imwrite(crop_path, crop)

    print(f"\n✅ Cropped images saved to: {crops_out}")


def main():
    print("=== 🎥 Frame Extraction & Optional GroundingDINO Cropping ===")
    videos_dir = input("Enter the path to your video folder: ").strip('"').strip("'")
    out_dir = input("Enter the output directory: ").strip('"').strip("'")

    # Ask if user wants to use GroundingDINO
    use_dino = input("Do you want to use GroundingDINO for object localization and cropping? (y/n): ").strip().lower()

    frames_dir = os.path.join(out_dir, "frames")
    extract_frames(videos_dir, frames_dir, image_ext="jpg", every_nth=1)

    if use_dino == "y":
        # Ask for detection parameters interactively
        caption = input("Enter your text prompt (e.g., 'orange'): ").strip() or "orange"

        box_threshold_str = input("Enter box threshold [default 0.35]: ").strip()
        box_threshold = float(box_threshold_str) if box_threshold_str else 0.35

        text_threshold_str = input("Enter text threshold [default 0.25]: ").strip()
        text_threshold = float(text_threshold_str) if text_threshold_str else 0.25

        device = input("Run on CPU or CUDA? [cpu/cuda, default=cpu]: ").strip().lower() or "cpu"

        crops_dir = os.path.join(out_dir, "cropped")

        run_dino_crop(
            frames_dir, crops_dir,
            caption=caption,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
            device=device
        )

        cleanup = input("Delete raw frames after cropping? (y/n): ").strip().lower()
        if cleanup == "y":
            shutil.rmtree(frames_dir, ignore_errors=True)
            print("🧹 Raw frames deleted.")
    else:
        print("Skipping DINO detection — only frames extracted.")


if __name__ == "__main__":
    main()
