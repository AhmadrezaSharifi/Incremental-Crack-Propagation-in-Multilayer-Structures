import cv2
import numpy as np
import os

model_name = 'fl_1'  
new_dir = r'../' + model_name
os.chdir(new_dir)

if __name__ == "__main__":
    input_path = "crack.mov"      # your raw video
    output_path = "circle.mp4"   # output circular masked video


def crop_to_circle_white(input_video, output_video):
    cap = cv2.VideoCapture(input_video)

    if not cap.isOpened():
        print("❌ Cannot open the video file.")
        return

    # Video properties
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)

    # Square size
    square_size = min(width, height)

    # Center crop start coordinates
    x_start = (width  - square_size) // 2
    y_start = (height - square_size) // 2

    # Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video, fourcc, fps, (square_size, square_size))

    print(f"Cropping to CIRCLE with white background… {square_size}x{square_size}")

    # Circular mask
    center = (square_size // 2, square_size // 2)
    radius = square_size // 2

    Y, X = np.ogrid[:square_size, :square_size]
    dist = (X - center[0]) ** 2 + (Y - center[1]) ** 2
    circle_mask = (dist <= radius * radius).astype(np.uint8) * 255

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Crop center region
        crop = frame[y_start:y_start+square_size, x_start:x_start+square_size]

        # Apply circular area
        circular_region = cv2.bitwise_and(crop, crop, mask=circle_mask)

        # Create white background
        white_bg = np.full_like(crop, 255)  # white background (255,255,255)

        # Invert mask for background
        inv_mask = cv2.bitwise_not(circle_mask)

        # Place background outside the circle
        bg_region = cv2.bitwise_and(white_bg, white_bg, mask=inv_mask)

        # Combine circular region + white background
        final_frame = cv2.add(circular_region, bg_region)

        out.write(final_frame)

    cap.release()
    out.release()
    print("✅ Done! Saved:", output_video)


crop_to_circle_white(input_path, output_path)
