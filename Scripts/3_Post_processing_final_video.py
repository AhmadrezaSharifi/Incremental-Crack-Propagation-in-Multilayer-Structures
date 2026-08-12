import os
import cv2
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import imageio

# ---------------- USER SETTINGS ----------------
model_name = 'fl_1'
base_dir = os.path.abspath(os.path.join("..", model_name))

VIDEO_IN   = os.path.join(base_dir, "circle.mp4")
DATA_CSV   = os.path.join(base_dir, "force_displacement.csv")
GIF_OUT    = os.path.join(base_dir, "sync_animation.gif")

interface_y = 5.0
GIF_FPS = 10
# ------------------------------------------------

# ---------------- TEXT STYLE ----------------
TEXT_COLOR = (0, 140, 255)   # orange (BGR)

def draw_text(img, text, pos, scale=0.9):
    cv2.putText(img, text, pos,
                cv2.FONT_HERSHEY_SIMPLEX, scale,
                (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(img, text, pos,
                cv2.FONT_HERSHEY_SIMPLEX, scale,
                TEXT_COLOR, 2, cv2.LINE_AA)

# ---------------- Matplotlib Academic Style ----------------
mpl.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 18,
    'axes.labelsize': 24,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 16,
    'lines.linewidth': 2.5,
})

force_color = (0/255, 0/255, 128/255)
crack_color = (196/255, 18/255, 52/255)

# ---------------- Load CSV ----------------
df = pd.read_csv(DATA_CSV)
df.columns = [c.strip().lower() for c in df.columns]

required = ["displacement", "force", "crack length"]
for c in required:
    if c not in df.columns:
        raise ValueError(f"CSV missing required column: '{c}'")

has_energy = "released energy" in df.columns
has_maxp   = "max_p" in df.columns

# ---------------- Video metadata ----------------
cap = cv2.VideoCapture(VIDEO_IN)
if not cap.isOpened():
    raise RuntimeError(f"Cannot open video: {VIDEO_IN}")

fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
duration = frame_count / fps

# ---------------- Time interpolation ----------------
df["time"] = np.linspace(0.0, duration, len(df))
time_data = df["time"].values

interp_disp  = interp1d(time_data, df["displacement"].values, fill_value="extrapolate")
interp_force = interp1d(time_data, df["force"].values, fill_value="extrapolate")
interp_crack = interp1d(time_data, df["crack length"].values, fill_value="extrapolate")

if has_energy:
    interp_energy = interp1d(time_data, df["released energy"].values,
                             fill_value="extrapolate")

if has_maxp:
    interp_maxp = interp1d(time_data, df["max_p"].values,
                           fill_value="extrapolate")

# ---------------- Output layout ----------------
plot_w = frame_w
plot_h = frame_h
out_w = frame_w + plot_w
out_h = max(frame_h, plot_h)

# ---------------- Matplotlib figure ----------------
dpi = 100
fig = Figure(figsize=(plot_w / dpi, plot_h / dpi), dpi=dpi)
canvas = FigureCanvas(fig)
ax1 = fig.add_subplot(111)
ax2 = ax1.twinx()

ax1.plot(df["displacement"], df["force"], color=force_color, label="Force")
ax2.plot(df["displacement"], df["crack length"],
         color=crack_color, linestyle='--', label="Crack length")

ax1.set_xlabel("Displacement (mm)")
ax1.set_ylabel("Force (N)", color=force_color)
ax2.set_ylabel("Crack length (mm)", color=crack_color)

ax2.axhline(interface_y, color='gray', linestyle=':', linewidth=3)

marker_force, = ax1.plot([], [], marker='o', color=force_color, markersize=10)
marker_crack, = ax2.plot([], [], marker='s', color=crack_color, markersize=8)

ax1.legend(frameon=False, loc="upper left")

# ---------------- GIF writer ----------------
gif_writer = imageio.get_writer(GIF_OUT, mode='I', fps=GIF_FPS, loop=0)

# ---------------- MAIN LOOP ----------------
frame_idx = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    t = frame_idx / fps

    d = float(interp_disp(t))
    f = float(interp_force(t))
    a = float(interp_crack(t))

    g = float(interp_energy(t)) if has_energy else None
    mp = float(interp_maxp(t)) if has_maxp else None

    marker_force.set_data([d], [f])
    marker_crack.set_data([d], [a])

    canvas.draw()
    plot_img = np.asarray(canvas.buffer_rgba())
    plot_img = cv2.cvtColor(plot_img, cv2.COLOR_RGBA2BGR)

    annotated = frame.copy()

    cv2.rectangle(annotated, (8, 6), (560, 180), (0, 0, 0), -1)

    draw_text(annotated, f"Force = {f:.4g} N", (16, 35))
    draw_text(annotated, f"Displacement = {d:.4g} mm", (16, 65))
    draw_text(annotated, f"Crack length = {a:.4g} mm", (16, 95))

    y = 125
    if has_energy:
        draw_text(annotated, f"Released energy = {g:.4g} N/mm", (16, y))
        y += 30

    if has_maxp:
        draw_text(annotated, f"Max principal stress = {mp:.3f} MPa", (16, y))

    combined = np.zeros((out_h, out_w, 3), dtype=np.uint8)
    combined[:frame_h, :frame_w] = annotated
    combined[:plot_h, frame_w:] = plot_img

    gif_writer.append_data(cv2.cvtColor(combined, cv2.COLOR_BGR2RGB))
    frame_idx += 1

cap.release()
gif_writer.close()

print(f"\n✔ DONE — GIF saved to:\n{GIF_OUT}\n")


import os
import cv2
import imageio

# ---------------- USER SETTINGS ----------------
model_name = 'fl_1'
base_dir = os.path.abspath(os.path.join("..", model_name))

video_name = "Wavy_result.mov"
video_path = os.path.join(base_dir, video_name)
gif_name = os.path.splitext(video_name)[0] + ".gif"
gif_path = os.path.join(base_dir, gif_name)

GIF_FPS = 10  # adjust to 5 for slower, 15 for faster

# ---------------- CHECK VIDEO EXISTS ----------------
if not os.path.isfile(video_path):
    raise FileNotFoundError(f"Video not found: {video_path}")

# ---------------- OPEN VIDEO ----------------
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    raise RuntimeError(f"Cannot open video: {video_path}")

# ---------------- GET VIDEO INFO ----------------
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Video loaded: {frame_count} frames, {frame_w}x{frame_h}, {fps:.2f} FPS")

# ---------------- GIF WRITER ----------------
writer = imageio.get_writer(gif_path, mode='I', fps=GIF_FPS)

# ---------------- READ FRAMES ----------------
frame_idx = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert BGR → RGB for GIF
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    writer.append_data(rgb_frame)
    frame_idx += 1

cap.release()
writer.close()

print(f"\n✔ GIF created successfully:\n{gif_path}")