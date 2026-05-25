# CS549 Vision Lab 1 — Camera App

A webcam-based camera application built with OpenCV and Python for WPI CS549 (Computer Vision).

## Requirements

- Python 3.13+
- OpenCV 4.12+

```bash
pip3 install opencv-python
```

## Setup

Place `opencv_logo.png` in the same directory as `camera_app.py`. Captured photos and videos are saved to a `captures/` folder (created automatically).

## Usage

```bash
python3 camera_app.py
```

| Key | Action |
|-----|--------|
| `c` | Capture photo (white flash) |
| `v` | Start / stop video recording |
| `e` | Toggle color extraction (pink/magenta) |
| `r` | Rotate +10° |
| `t` | Toggle binary threshold |
| `b` | Toggle Gaussian blur |
| `s` | Toggle sharpen |
| `esc` | Quit |

Use the **Zoom x10** trackbar to zoom in/out and the **Blur Sigma** trackbar (5–30) to adjust blur intensity.

## Features

- Date/time stamp in bottom-right corner (copied to top-right)
- OpenCV logo blended at top-left
- Red constant border around the frame
- White screen flash on photo capture
- REC indicator during video recording

