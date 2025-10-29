#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import cv2
import re
from tqdm.auto import tqdm   # adapts to terminal/VSCode/Jupyter, etc.
import shutil
import warnings
from math import ceil


FNAME_RE = re.compile(r"^(?P<base>.+)_frame_(?P<idx>\d{6})\.(?:jpg|jpeg|png)$", re.IGNORECASE)
# Suppress noisy library warnings before user input
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# --- Ensure GroundingDINO in import path ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DINO_DIR = os.path.join(SCRIPT_DIR, "GroundingDINO")
if os.path.isdir(DINO_DIR) and DINO_DIR not in sys.path:
    sys.path.insert(0, DINO_DIR)

# --- Try importing GroundingDINO (optional dependency) ---
try:
    from groundingdino.util.inference import load_model, load_image, predict
except Exception as e:
    print(f"⚠️ Could not import GroundingDINO: {e}")
    load_model = None
    load_image = None
    predict = None

VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpeg', '.mpg'}


def dir_has_images(path, exts=(".png", ".jpg", ".jpeg")):
    if not os.path.isdir(path):
        return False
    for _, _, files in os.walk(path):
        if any(f.lower().endswith(exts) for f in files):
            return True
    return False

def has_any_files(root_dir):
    """Return True if directory exists and contains at least one file."""
    if not os.path.isdir(root_dir):
        return False
    for _, _, files in os.walk(root_dir):
        if files:
            return True
    return False
def _existing_indices(out_dir, base):
    """Return sorted list of saved indices for this video (based on filename pattern)."""
    if not os.path.isdir(out_dir):
        return []
    idxs = []
    for f in os.listdir(out_dir):
        m = FNAME_RE.match(f)
        if m and m.group("base") == base:
            idxs.append(int(m.group("idx")))
    return sorted(idxs)

def _save_frame(cap, frame_number, out_path):
    """Seek to frame_number and save a single frame; returns True if saved."""
    # Try to seek. Some codecs have imperfect seeking; we read once after set.
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ok, frame = cap.read()
    if not ok or frame is None:
        return False
    cv2.imwrite(out_path, frame)
    return True
def _scan_existing(out_dir, base):
    """
    Return (saved_idx, existing_count, max_idx) where:
      - saved_idx is the next index to write (max_idx+1 if any, else 0)
      - existing_count is number of matching frame files
      - max_idx is the highest found index (or -1 if none)
    """
    if not os.path.isdir(out_dir):
        return 0, 0, -1

    existing = []
    for f in os.listdir(out_dir):
        m = FNAME_RE.match(f)
        if m and m.group("base") == base:
            existing.append(int(m.group("idx")))
    if not existing:
        return 0, 0, -1
    max_idx = max(existing)
    return max_idx + 1, len(existing), max_idx


def extract_frames(input_videos_dir, output_frames_dir, image_ext="png", every_nth=1,
                   per_video_subfolders=True, overwrite=False):
    """
    Extract frames with gap-filling:
    - Fully extracted videos: skip (unless overwrite=True)
    - Partially extracted: fill only the missing indices
    - New videos: extract all needed indices
    Uses one global tqdm for frames that will actually be written in this run.
    """
    os.makedirs(output_frames_dir, exist_ok=True)
    video_files = [f for f in os.listdir(input_videos_dir)
                   if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS]
    if not video_files:
        print("No videos found.")
        return

    # Build a plan of what to write: for each video, which indices (i) to save now
    plan = []  # items: dict(base, video_path, out_dir, targets=[i,...], total_frames_known)
    total_to_write = 0

    for filename in video_files:
        base, _ = os.path.splitext(filename)
        video_path = os.path.join(input_videos_dir, filename)
        out_dir = os.path.join(output_frames_dir, base) if per_video_subfolders else output_frames_dir
        os.makedirs(out_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            tqdm.write(f"Could not open {video_path}")
            continue

        total_frames_val = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        total_frames_known = total_frames_val and total_frames_val > 0
        total_frames = int(total_frames_val) if total_frames_known else 0

        # Compute which save indices *should* exist: i = 0..expected_saves-1
        if total_frames_known:
            expected_saves = ceil(total_frames / max(every_nth, 1))
            should_exist = set(range(expected_saves))
        else:
            # Unknown length → we can't know all targets. In this case,
            # we will *resume* from max existing and not fill earlier gaps.
            expected_saves = None
            should_exist = None

        existing = set(_existing_indices(out_dir, base))

        if overwrite:
            # Write all indices from scratch
            targets = sorted(range(expected_saves)) if expected_saves is not None else []
        else:
            if expected_saves is not None:
                # Fill exactly the missing indices
                targets = sorted(should_exist - existing)
                if not targets:
                    tqdm.write(f"✅ Skipping '{filename}' (complete: {len(existing)}/{expected_saves})")
            else:
                # Unknown total length: resume only from the end (can't safely fill gaps)
                start_idx = (max(existing) + 1) if existing else 0
                targets = list(range(start_idx, start_idx + 0))  # placeholder; we’ll handle resume sequentially
                if start_idx == 0 and existing:
                    tqdm.write(f"⚠️ '{filename}': unknown length; can't fill earlier gaps. Resuming from {start_idx}.")
                elif not existing:
                    tqdm.write(f"ℹ️ '{filename}': unknown length; extracting from start.")

        # Update totals
        if expected_saves is not None:
            total_to_write += len(targets)
            plan.append({
                "filename": filename,
                "base": base,
                "video_path": video_path,
                "out_dir": out_dir,
                "targets": targets,             # indices i (mapped to frame_number = i*every_nth)
                "expected_saves": expected_saves,
                "total_frames_known": True,
            })
        else:
            # Unknown length → sequential resume from start_idx (or 0)
            # We'll compute target frames on the fly while reading.
            plan.append({
                "filename": filename,
                "base": base,
                "video_path": video_path,
                "out_dir": out_dir,
                "targets": None,                # sentinel → sequential path
                "expected_saves": None,
                "total_frames_known": False,
                "existing_max": max(existing) if existing else -1,
            })

        cap.release()

    if not plan:
        print("Nothing to do — all videos fully extracted or unreadable.")
        return

    # One global bar: starts with known number of writes (unknown-length work will grow it)
    pbar = tqdm(total=total_to_write, desc="Saving frames", dynamic_ncols=True, leave=True, mininterval=0.1)

    for job in plan:
        filename = job["filename"]
        base = job["base"]
        out_dir = job["out_dir"]
        video_path = job["video_path"]
        pbar.set_postfix_str(base)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            tqdm.write(f"Could not open {video_path}")
            continue

        if job["total_frames_known"]:
            # Fill specific missing indices by random-access seek
            for i in job["targets"]:
                frame_number = i * every_nth
                out_path = os.path.join(out_dir, f"{base}_frame_{i:06d}.{image_ext}")
                ok = _save_frame(cap, frame_number, out_path)
                if ok:
                    pbar.update(1)
            cap.release()
        else:
            # Unknown total length: resume sequentially from existing_max+1
            start_i = (job.get("existing_max", -1) + 1)
            # Seek to first frame we plan to save
            start_frame = start_i * every_nth
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            i = start_i
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                # Save every_nth starting here
                out_path = os.path.join(out_dir, f"{base}_frame_{i:06d}.{image_ext}")
                cv2.imwrite(out_path, frame)
                i += 1
                pbar.total += 1  # grow bar since we didn't know upfront
                pbar.update(1)
                # Skip ahead by (every_nth-1) frames if needed
                if every_nth > 1:
                    # fast-forward by reading & discarding or seeking
                    next_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) + (every_nth - 1)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, next_pos)
            cap.release()

    pbar.close()
    print(f"✅ Frames extracted (including gap-fills) to {output_frames_dir}")


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
        crop_path = os.path.join(out_dir, f"{base}.png")
        cv2.imwrite(crop_path, crop)

    print(f"\n✅ Cropped images saved to: {crops_out}")


def main():
    print("=== 🎥 Frame Extraction & Optional GroundingDINO Cropping ===")
    videos_dir = input("Enter the path to your video folder: ").strip('"').strip("'")
    out_dir = input("Enter the output directory: ").strip('"').strip("'")

    # Ask user how often to extract frames
    print("\n📸 Frame extraction frequency:")
    print("  Enter how often to extract frames (1 = every frame, 2 = every 2nd, 3 = every 3rd, etc.)")
    nth_str = input("Extract every n-th frame [default=1]: ").strip()
    every_nth = int(nth_str) if nth_str.isdigit() and int(nth_str) > 0 else 1

    # Ask if user wants to use GroundingDINO
    use_dino = input("\nDo you want to use GroundingDINO for object localization and cropping? (y/n): ").strip().lower()

    frames_dir = os.path.join(out_dir, "frames")
    crops_dir = os.path.join(out_dir, "cropped")  # <-- define before use

    # Extract frames (skips videos that already have frames unless overwrite=True)
    # (Use your chosen extension consistently; here I use JPG for speed/size.)
    extract_frames(videos_dir, frames_dir, image_ext="png", every_nth=every_nth, overwrite=False)

    if use_dino == "y":
        # Ask up front whether to keep extracted frames
        keep_frames = input("\nKeep the extracted frame images after cropping? (y/N): ").strip().lower() or "n"

        # GroundingDINO parameters
        caption = input("Enter your text prompt (e.g., 'orange'): ").strip() or "orange"

        box_threshold_str = input("Enter box threshold [default 0.35]: ").strip()
        box_threshold = float(box_threshold_str) if box_threshold_str else 0.35

        text_threshold_str = input("Enter text threshold [default 0.25]: ").strip()
        text_threshold = float(text_threshold_str) if text_threshold_str else 0.25

        device = input("Run on CPU or CUDA? [cpu/cuda, default=cpu]: ").strip().lower() or "cpu"

        run_dino_crop(
            frames_dir, crops_dir,
            caption=caption,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
            device=device
        )

        # Delete frames only if crops exist and the user asked to
        if keep_frames != "y":
            if has_any_files(crops_dir):
                shutil.rmtree(frames_dir, ignore_errors=True)
                print("🧹 Raw frames deleted (kept only cropped images).")
            else:
                print("⚠️ No cropped images were found — keeping frames for safety.")
        else:
            print("ℹ️ Keeping both frames and cropped images.")
    else:
        print("\nSkipping DINO detection — only frames extracted.")



if __name__ == "__main__":
    main()
