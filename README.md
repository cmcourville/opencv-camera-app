# Camera App

A webcam-based camera application built with OpenCV and Python.

## Requirements

- Python 3.13+
- OpenCV contrib 4.12+ (includes SIFT)

```bash
pip3 install opencv-contrib-python
```

## Setup

Place `opencv_logo.png` in the same directory as `camera_app.py`. Captured photos and videos are saved to a `captures/` folder (created automatically).

## Usage

```bash
python3 camera_app.py
```

## Controls

| Key | Action |
|-----|--------|
| `c` | Capture photo (white flash) |
| `v` | Start / stop video recording |
| `e` | Toggle color extraction (pink/magenta) |
| `r` | Rotate +10° |
| `t` | Toggle binary threshold |
| `b` | Toggle Gaussian blur |
| `s` | Toggle sharpen |
| `g` + `x` | Toggle Sobel X gradient mode |
| `g` + `y` | Toggle Sobel Y gradient mode |
| `d` | Toggle Canny edge detection |
| `4` | Toggle four-view window (Original / Laplacian / Sobel X / Sobel Y) |
| `esc` | Quit |

All toggleable modes are also clickable via the button bar at the bottom of the window.

## Trackbars

| Trackbar | Range | Effect |
|----------|-------|--------|
| Zoom | 1.0x – 3.0x | Center-crop zoom (draggable slider) |
| Blur Sigma | 5 – 30 | Gaussian blur intensity (draggable slider) |
| Sobel ksize | 0–3 → 1,3,5,7 | Kernel size for Sobel X and Sobel Y modes |
| Canny T1 | 1 – 5000 | Canny lower threshold |
| Canny T2 | 1 – 5000 | Canny upper threshold |

## Features

### Display
- Date/time stamp in bottom-right corner (mirrored to top-right)
- OpenCV logo blended at top-left with feathered edge
- Red constant border around the frame
- Button bar with active-mode highlighting

### Capture
- White screen flash on photo capture; saves to `captures/photo_NNN.jpg`
- Video recording with REC indicator; saves to `captures/video_NNN.avi`

### Image Processing Modes
- **Color extraction** — isolates pink/magenta pixels via HSV mask
- **Rotation** — cumulative +10° per keypress via affine warp
- **Threshold** — binary threshold at intensity 127
- **Gaussian blur** — controlled by Blur Sigma trackbar
- **Sharpen** — 3×3 unsharp kernel via `filter2D`
- **Sobel X** — horizontal gradient; kernel size adjustable via trackbar
- **Sobel Y** — vertical gradient; kernel size adjustable via trackbar
- **Canny** — edge detection with two adjustable thresholds (1–5000)
- **Four-view** — secondary window showing Original, Laplacian, Sobel X, Sobel Y computed from the live frame using custom `filter2D`-based implementations

### Custom Filter Functions
`sobel_x_custom`, `sobel_y_custom`, and `laplacian_custom` implement the standard 3×3 kernels using `cv2.filter2D()` directly (no `cv2.Sobel()` or `cv2.Laplacian()`). These power the four-view window.
