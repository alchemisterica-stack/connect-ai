#!/usr/bin/env python3
"""
publish_instagram_slideshow.py
Bridge tool for office scheduler to trigger a 5-slide slideshow Reels publish.
"""
import subprocess
import sys

def main():
    script_path = r"C:\Users\User\my-ai-office\scripts\publish_instagram_schedule.py"
    subprocess.run([sys.executable, script_path, "--type", "slideshow"])

if __name__ == "__main__":
    main()
