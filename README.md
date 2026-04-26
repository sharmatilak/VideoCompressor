# Video Compressor

Python tool to compress videos using FFmpeg. Works in two ways:

## CLI Mode
```bash
python cli.py input.mp4 output.mp4
```

## GUI Mode
```bash
python gui.py
```
- Select multiple videos
- Choose output folder
- Pick preset (High Quality / Balanced / Low Size)
- Click Start

## Tech Used
- Python, Tkinter, Threading, Subprocess, FFmpeg

## Requirements
- FFmpeg installed (or ffmpeg.exe in same folder)
- Python 3.x

## Notes
- Compressed files saved as `compressed_originalname.mp4`
- Original files are not modified
  
