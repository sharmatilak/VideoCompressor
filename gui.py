import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import subprocess
import threading
import os
import sys
import re
import time

def base_path():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

def ffpath(name):
    return os.path.join(base_path(), name)

FFMPEG_PATH = ffpath("ffmpeg.exe")
FFPROBE_PATH = ffpath("ffprobe.exe")


CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0



PRESETS = {
    "High Quality":  {"bitrate": "3000k", "scale": None,       "fps": None},
    "Balanced":      {"bitrate": "1500k", "scale": "1280:720", "fps": 30},
    "Low Size":      {"bitrate": "800k",  "scale": "854:480",  "fps": 24}
}

def get_video_duration(file_path):
    cmd = [
        FFPROBE_PATH,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, creationflags=CREATE_NO_WINDOW)
        return float(result.stdout.strip())
    except Exception:
        return None

def extreme_compress_with_progress(input_path, output_path, target_bitrate, scale, fps):
    total_duration = get_video_duration(input_path)
    if not total_duration:
        yield (-1, 0, None)
        return

 
    has_audio = False
    probe_cmd = [
        FFPROBE_PATH, "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=index",
        "-of", "csv=p=0",
        input_path
    ]
    try:
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        has_audio = bool(probe_result.stdout.strip())
    except:
        pass


    cmd = [
        FFMPEG_PATH, "-y", "-i", input_path,
        "-map", "0:v:0"  
    ]

    if has_audio:
        cmd.extend(["-map", "0:a:0"]) 
    else:
        cmd.append("-an")  


    cmd.extend([
        "-map_metadata", "-1", 
        "-map_chapters", "-1", 
        "-metadata", "title=",
        "-metadata", "artist=",
        "-metadata", "album=",
        "-metadata", "comment="
    ])

 
    cmd.extend([
        "-vcodec", "libx265",
        "-crf", "28",
        "-preset", "medium",
        "-b:v", target_bitrate,
    ])
    if has_audio:
        cmd.extend(["-acodec", "aac", "-b:a", "96k"])
    if scale:
        cmd.extend(["-vf", f"scale={scale}"])
    if fps:
        cmd.extend(["-r", str(fps)])
    cmd.extend(["-movflags", "+faststart", output_path])


    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, creationflags=CREATE_NO_WINDOW)
    time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
    start_time = time.time()

    for line in process.stderr:
        match = time_pattern.search(line)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            elapsed_video_time = hours * 3600 + minutes * 60 + seconds
            percent = min(100, (elapsed_video_time / total_duration) * 100)

            elapsed_real_time = time.time() - start_time
            eta_seconds = None
            if percent > 0:
                total_estimated_time = elapsed_real_time / (percent / 100)
                eta_seconds = max(0, total_estimated_time - elapsed_real_time)

            yield (percent, elapsed_real_time, eta_seconds)

    process.wait()
    yield (100, time.time() - start_time, 0)


def format_time(seconds):
    if seconds is None:
        return "--:--"
    minutes = int(seconds // 60)
    sec = int(seconds % 60)
    return f"{minutes:02}:{sec:02}"

def start_compression():
    preset_choice = preset_var.get()
    settings = PRESETS[preset_choice]

    if not input_files:
        messagebox.showerror("Error", "Please select at least one input video.")
        return
    if not output_folder:
        messagebox.showerror("Error", "Please select an output folder.")
        return

    compress_button.config(state="disabled")
    progress_bar["value"] = 0
    progress_label.config(text="Progress: 0%")
    eta_label.config(text="Time Remaining: --:--")

    def run_batch():
        for idx, file in enumerate(input_files, start=1):
            output_path = os.path.join(output_folder, f"compressed_{os.path.basename(file)}")
            status_label.config(text=f"Compressing {idx}/{len(input_files)}: {os.path.basename(file)}")
            try:
                for percent, elapsed, eta in extreme_compress_with_progress(
                    file, output_path, settings["bitrate"], settings["scale"], settings["fps"]
                ):
                    if percent >= 0:
                        progress_bar["value"] = percent
                        progress_label.config(text=f"Progress: {percent:.1f}%")
                        eta_label.config(text=f"Time Remaining: {format_time(eta)}")
                status_label.config(text=f"✅ Done: {os.path.basename(file)}")
            except subprocess.CalledProcessError as e:
                status_label.config(text=f"❌ Failed: {os.path.basename(file)}")

        messagebox.showinfo("Batch Complete", "All videos processed.")
        compress_button.config(state="normal")

    threading.Thread(target=run_batch, daemon=True).start()

def browse_input_files():
    files = filedialog.askopenfilenames(
        title="Select Input Videos",
        filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")]
    )
    if files:
        input_files.clear()
        input_files.extend(files)
        input_label.config(text=f"{len(input_files)} files selected")

def browse_output_folder():
    global output_folder
    folder = filedialog.askdirectory(title="Select Output Folder")
    if folder:
        output_folder = folder
        output_label.config(text=folder)


root = tk.Tk()
root.title("Extreme Video Compressor (Batch Mode)")
root.geometry("550x350")

input_files = []
output_folder = ""

tk.Label(root, text="Input Videos:").pack(anchor="w", padx=10, pady=5)
input_frame = tk.Frame(root)
input_frame.pack(fill="x", padx=10)
input_label = tk.Label(input_frame, text="No files selected")
input_label.pack(side="left")
tk.Button(input_frame, text="Browse", command=browse_input_files).pack(side="right")

tk.Label(root, text="Output Folder:").pack(anchor="w", padx=10, pady=5)
output_frame = tk.Frame(root)
output_frame.pack(fill="x", padx=10)
output_label = tk.Label(output_frame, text="No folder selected")
output_label.pack(side="left")
tk.Button(output_frame, text="Browse", command=browse_output_folder).pack(side="right")

tk.Label(root, text="Quality Preset:").pack(anchor="w", padx=10, pady=5)
preset_var = tk.StringVar(value="Balanced")
preset_menu = ttk.Combobox(root, textvariable=preset_var, values=list(PRESETS.keys()), state="readonly")
preset_menu.pack(padx=10, pady=5)

progress_bar = ttk.Progressbar(root, mode="determinate", length=500)
progress_bar.pack(padx=10, pady=10)
progress_bar["maximum"] = 100

progress_label = tk.Label(root, text="Progress: 0%")
progress_label.pack()

eta_label = tk.Label(root, text="Time Remaining: --:--")
eta_label.pack()

status_label = tk.Label(root, text="")
status_label.pack()

compress_button = tk.Button(root, text="Start Compression", command=start_compression)
compress_button.pack(pady=10)

root.mainloop()
