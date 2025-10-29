import cv2  # OpenCV library for video processing
import os  # For creating folders and handling file paths
import sys  # For exiting the script if the folder is invalid


def extract_frames_from_videos(input_folder_path):
    """
    Scans a folder for video files, extracts all frames, and saves them
    to a new folder named 'Extracted_Images' at the same level.
    """

    # --- 1. Define Video Formats ---
    # A set of common video file extensions
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpeg', '.mpg'}

    # --- 2. Validate Input Folder ---
    # Check if the provided path is a valid directory
    if not os.path.isdir(input_folder_path):
        print(f"Error: Input path '{input_folder_path}' is not a valid directory.")
        sys.exit(1)  # Exit the script

    # Get the absolute path for consistency
    input_folder_path = os.path.abspath(input_folder_path)

    # --- 3. Create Output Folder ---
    # Get the parent directory of the input folder
    # e.g., if input is '/User/Projects/MyVideos', parent is '/User/Projects'
    parent_directory = os.path.dirname(input_folder_path)

    # Define the path for the new 'Extracted_Images' folder
    output_folder_path = os.path.join(parent_directory, "Extracted_Images")

    # Create the folder if it doesn't already exist
    try:
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)
            print(f"Successfully created output folder: {output_folder_path}")
        else:
            print(f"Output folder already exists: {output_folder_path}")
    except OSError as e:
        print(f"Error creating directory '{output_folder_path}': {e}")
        sys.exit(1)

    # --- 4. Process Videos ---
    print(f"\nScanning for videos in: {input_folder_path}...")

    processed_video_count = 0

    # Loop through every file in the input folder
    for filename in os.listdir(input_folder_path):
        # Get the file's name (without extension) and its extension
        file_basename, file_extension = os.path.splitext(filename)

        # Check if the file's extension is in our list of video formats
        if file_extension.lower() in VIDEO_EXTENSIONS:
            processed_video_count += 1
            print(f"\n--- Processing video: {filename} ---")

            # Construct the full path to the video file
            video_path = os.path.join(input_folder_path, filename)

            # Open the video file with OpenCV
            video_capture = cv2.VideoCapture(video_path)

            if not video_capture.isOpened():
                print(f"Error: Could not open video file {video_path}")
                continue  # Skip to the next file

            # --- 5. Extract and Save Frames ---
            frame_number = 0
            while True:
                # Read one frame from the video
                # 'success' is a boolean (True/False)
                # 'frame' is the image data (a NumPy array)
                success, frame = video_capture.read()

                # If 'success' is False, we have reached the end of the video
                if not success:
                    break

                # Construct the output filename
                # Format: [VideoFileName]_frame_000001.jpg
                image_filename = f"{file_basename}_frame_{frame_number:06d}.png"

                # Construct the full path to save the image
                output_image_path = os.path.join(output_folder_path, image_filename)

                # Save the 'frame' as a PNG image
                cv2.imwrite(output_image_path, frame)

                frame_number += 1

            # Release the video file handle
            video_capture.release()
            print(f"Successfully extracted {frame_number} frames from {filename}.")

    # --- 6. Final Report ---
    if processed_video_count == 0:
        print("\nNo video files found in the specified folder.")
    else:
        print(f"\n✅ All done. Processed {processed_video_count} video(s).")


# --- Run the script ---
if __name__ == "__main__":
    # Prompt the user to enter the path to their video folder
    folder_path = input("Enter the full path to your video folder: ")

    # Clean up the path (removes extra quotes or spaces)
    folder_path = folder_path.strip().strip('"').strip("'")

    extract_frames_from_videos(folder_path)
