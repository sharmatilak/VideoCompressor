import subprocess
import shutil
import os
import sys

def extreme_compress(input_path, output_path, target_bitrate="1500k", fps=None, scale=None):

    if not shutil.which("ffmpeg"):
        print("FFmpeg not installed!")
        return

    ext = os.path.splitext(output_path)[1].lower()

    cmd = [
        "ffmpeg", "-i", input_path,
        "-vcodec", "libx265",           
        "-crf", "28",                   
        "-preset", "medium",            
        "-b:v", target_bitrate,         
        "-acodec", "aac",                
        "-b:a", "96k",            
        "-vf", "scale=1280:720",      
        "-movflags", "+faststart"
    ]

   
    if fps:
        cmd.extend(["-r", str(fps)])


    if ext == ".mov":
        cmd.extend(["-pix_fmt", "yuv420p"])  

    cmd.append(output_path)
    
    subprocess.run(cmd, check=True)
    print(f"Compressed video saved as: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python compress.py input.mp4 output.mp4")
    else:
        extreme_compress(
            sys.argv[1],
            sys.argv[2],
            target_bitrate="1000k",  
            scale="1280:720",       
            fps=30                  
        )
