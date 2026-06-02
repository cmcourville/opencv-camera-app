import cv2
import numpy as np
from datetime import datetime
import os
import re

# iff doesn't exist, create dir for captured photos and videos
SAVE_DIR = "captures"
os.makedirs(SAVE_DIR, exist_ok=True)

# opencv_logo.png in the same directory as this script
LOGO_PATH = "opencv_logo.png"

# width of the red border added around every frame
BORDER = 10


SLIDER_H = 45   # pixel height of the bottom slider panel
BUTTON_H = 32   # pixel height of the button bar below the sliders

# (key label shown in button, action label, key code sent to main loop)
BUTTON_DEFS = [
    ("C",   "Capture", ord('c')),
    ("V",   "Record",  ord('v')),
    ("E",   "Color",   ord('e')),
    ("R",   "Rotate",  ord('r')),
    ("T",   "Thresh",  ord('t')),
    ("B",   "Blur",    ord('b')),
    ("S",   "Sharpen", ord('s')),
    ("GX",  "Sobel X", 0x01),     # virtual keycode; mouse click toggles sobel_x_mode
    ("GY",  "Sobel Y", 0x02),     # virtual keycode; mouse click toggles sobel_y_mode
    ("D",   "Canny",   ord('d')),
    ("ESC", "Quit",    27),
]

slider_state = {"zoom": 0, "blur": 5}
pending_key = {"val": -1}   # set by mouse button clicks, consumed by main loop
_drag = {"active": None}
_frame_wh = [640, 480]  # updated each frame so the mouse callback knows slider positions


def draw_sliders(frame, zoom_val, blur_val):
    h, w = frame.shape[:2]
    panel_y = h - SLIDER_H - BUTTON_H
    cv2.rectangle(frame, (0, panel_y), (w, h - BUTTON_H), (30, 30, 30), -1)

    z_x1, z_x2 = 90, w // 2 - 20
    z_y = panel_y + SLIDER_H // 2
    z_thumb = int(z_x1 + (zoom_val / 20) * (z_x2 - z_x1))
    cv2.putText(frame, f"Zoom {1.0 + zoom_val * 0.1:.1f}x", (8, z_y + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.line(frame, (z_x1, z_y), (z_x2, z_y), (120, 120, 120), 2)
    cv2.circle(frame, (z_thumb, z_y), 8, (0, 200, 255), -1)

    b_x1, b_x2 = w // 2 + 70, w - 20
    b_y = panel_y + SLIDER_H // 2
    b_thumb = int(b_x1 + ((blur_val - 5) / 25) * (b_x2 - b_x1))
    cv2.putText(frame, f"Blur  {blur_val}", (w // 2 + 8, b_y + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.line(frame, (b_x1, b_y), (b_x2, b_y), (120, 120, 120), 2)
    cv2.circle(frame, (b_thumb, b_y), 8, (0, 200, 255), -1)


def draw_button_bar(frame, active_indices):
    h, w = frame.shape[:2]
    bar_y = h - BUTTON_H
    cv2.rectangle(frame, (0, bar_y), (w, h), (45, 45, 45), -1)
    n = len(BUTTON_DEFS)
    btn_w = w // n
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.36
    for i, (key_label, label, _) in enumerate(BUTTON_DEFS):
        x1 = i * btn_w
        x2 = (i + 1) * btn_w if i < n - 1 else w
        is_active = i in active_indices
        bg = (0, 130, 170) if is_active else (80, 80, 80)
        cv2.rectangle(frame, (x1 + 2, bar_y + 3), (x2 - 2, h - 3), bg, -1)
        display_label = "Stop" if (key_label == "V" and is_active) else label
        text = f"[{key_label}] {display_label}"
        (tw, th), _ = cv2.getTextSize(text, font, scale, 1)
        tx = x1 + max((btn_w - tw) // 2, 2)
        ty = bar_y + (BUTTON_H + th) // 2
        cv2.putText(frame, text, (tx, ty), font, scale, (230, 230, 230), 1)


def on_mouse(event, x, y, flags, param):
    w, h = _frame_wh
    slider_y = h - SLIDER_H - BUTTON_H
    button_y = h - BUTTON_H

    # Ignore clicks in the main frame area
    if y < slider_y:
        if event == cv2.EVENT_LBUTTONUP:
            _drag["active"] = None
        return

    # Button bar region
    if y >= button_y:
        if event == cv2.EVENT_LBUTTONDOWN:
            n = len(BUTTON_DEFS)
            btn_w = w // n
            idx = min(x // btn_w, n - 1)
            pending_key["val"] = BUTTON_DEFS[idx][2]
        return

    # Slider region
    z_x1, z_x2 = 90, w // 2 - 20
    b_x1, b_x2 = w // 2 + 70, w - 20

    pressing = (event == cv2.EVENT_LBUTTONDOWN or
                (event == cv2.EVENT_MOUSEMOVE and flags & cv2.EVENT_FLAG_LBUTTON))
    if event == cv2.EVENT_LBUTTONDOWN:
        if z_x1 <= x <= z_x2:
            _drag["active"] = "zoom"
        elif b_x1 <= x <= b_x2:
            _drag["active"] = "blur"

    if pressing and _drag["active"] == "zoom":
        slider_state["zoom"] = int(np.clip((x - z_x1) / max(z_x2 - z_x1, 1) * 20, 0, 20))
    elif pressing and _drag["active"] == "blur":
        slider_state["blur"] = int(np.clip((x - b_x1) / max(b_x2 - b_x1, 1) * 25 + 5, 5, 30))

    if event == cv2.EVENT_LBUTTONUP:
        _drag["active"] = None


def add_timestamp(frame):
    # create timestamp on bottom right corner
    text = datetime.now().strftime("%Y/%m/%d  %H:%M:%S")
    font, scale, thick = cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
    (tw, th), _ = cv2.getTextSize(text, font, scale, thick)
    h, w = frame.shape[:2]
    pad = 8
    x, y = w - tw - pad, h - pad
    # Dark background rectangle for readability
    x1_box, y1_box = x - 4, y - th - 4
    cv2.rectangle(frame, (x1_box, y1_box), (w, h), (0, 0, 0), -1)
    cv2.putText(frame, text, (x, y), font, scale, (255, 255, 255), thick)
    return frame, (x1_box, y1_box, w, h)  # roi_bounds = (x1, y1, x2, y2)


def copy_timestamp_roi(frame, roi_bounds):
    # copies and pastes timestamp on ROI at the top right
    x1, y1, x2, y2 = roi_bounds
    w = frame.shape[1]
    roi = frame[y1:y2, x1:x2].copy()
    rh, rw = roi.shape[:2]
    frame[0:rh, w - rw:w] = roi
    return frame


def apply_zoom(frame, zoom_level):
    # sim zoom by cropping the center and resizing back to org dimensions
    # zoom_level=1.0, no zoom; 3.0, 3x zoom
    if zoom_level <= 1.0:
        return frame
    h, w = frame.shape[:2]
    nh, nw = int(h / zoom_level), int(w / zoom_level)
    y1, x1 = (h - nh) // 2, (w - nw) // 2
    cropped = frame[y1:y1 + nh, x1:x1 + nw]
    return cv2.resize(cropped, (w, h))


def blend_logo(frame, logo):
    # alpha-blend the OpenCV logo in top-left corner with a feathered edge
    if logo is None:
        return frame
    lh, lw = logo.shape[:2]
    if lh > frame.shape[0] or lw > frame.shape[1]:
        return frame
    roi = frame[0:lh, 0:lw]

    if logo.shape[2] == 4:
        alpha_mask = logo[:, :, 3] / 255.0
        logo_rgb = logo[:, :, :3]
    else:
        alpha_mask = np.ones((lh, lw), dtype=np.float32)
        logo_rgb = logo

    # Feather gradient: full opacity across most of the logo, fades only at the outer edges
    flat_x = int(lw * 0.7)
    flat_y = int(lh * 0.7)
    fade_x = np.concatenate([np.ones(flat_x), np.linspace(1.0, 0.0, lw - flat_x)])
    fade_y = np.concatenate([np.ones(flat_y), np.linspace(1.0, 0.0, lh - flat_y)]).reshape(-1, 1)
    feather = (fade_x * fade_y).astype(np.float32)

    combined_alpha = (alpha_mask * feather)[:, :, np.newaxis]
    blended = (combined_alpha * logo_rgb + (1 - combined_alpha) * roi).astype(np.uint8)
    frame[0:lh, 0:lw] = blended
    return frame

def rotate_frame(frame, angle):
    # rotate fram around center by  given angle in degrees
    h, w = frame.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(frame, M, (w, h))

def extract_color(frame):
    # extract pink/magenta pixels using an HSV rangs mask and bitwise and
    # change the hsv bounds to target a diff color
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array([140, 50, 50])
    upper = np.array([170, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    return cv2.bitwise_and(frame, frame, mask=mask)


def sharpen(frame):
    # apply sharpening kernel using 2d convolution
    kernel = np.array([[ 0, -1,  0],
                       [-1,  5, -1],
                       [ 0, -1,  0]])
    return cv2.filter2D(frame, -1, kernel)


# Part 2 - custom gradient/edge filters using filter2D only (no cv2.Sobel/Laplacian)
def sobel_x_custom(gray):
    # horizontal gradient; standard 3x3 Sobel X kernel
    kernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    return cv2.convertScaleAbs(cv2.filter2D(gray.astype(np.float32), -1, kernel))

def sobel_y_custom(gray):
    # vertical gradient; standard 3x3 Sobel Y kernel
    kernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
    return cv2.convertScaleAbs(cv2.filter2D(gray.astype(np.float32), -1, kernel))

def laplacian_custom(gray):
    # second-order isotropic edge detector; 3x3 Laplacian kernel
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    return cv2.convertScaleAbs(cv2.filter2D(gray.astype(np.float32), -1, kernel))


def max_capture_index(save_dir, prefix, ext):
    # scan save_dir for prefix_NNN.ext files and return the highest NNN found
    pat = re.compile(rf"^{prefix}_(\d+)\.{ext}$")
    indices = [int(m.group(1)) for f in os.listdir(save_dir) if (m := pat.match(f))]
    return max(indices, default=0)


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open webcam.")
        return

    # load OpenCV logo with alpha channel if exists
    logo = None
    if os.path.exists(LOGO_PATH):
        raw = cv2.imread(LOGO_PATH, cv2.IMREAD_UNCHANGED)
        if raw is not None:
            logo = cv2.resize(raw, (80, 80))

    # create window and attach trackbars
    win = "Camera App"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, on_mouse)
    # Part 1 trackbars: Sobel kernel size (0-3 → odd ksizes 1,3,5,7) and Canny thresholds
    cv2.createTrackbar("Sobel ksize", win, 1, 3, lambda x: None)
    cv2.createTrackbar("Canny T1",    win, 100, 5000, lambda x: None)
    cv2.createTrackbar("Canny T2",    win, 200, 5000, lambda x: None)

    # App state
    recording = False
    video_writer = None
    flash_frames = 0      # remaining frames to show the white capture flash
    rotation_angle = 0    # cumulative rotation; each 'r' press adds 10 degrees
    color_mode = False
    threshold_mode = False
    blur_mode = False
    sharpen_mode = False
    photo_count = max_capture_index(SAVE_DIR, "photo", "jpg")
    video_count = max_capture_index(SAVE_DIR, "video", "avi")
    sobel_x_mode = False
    sobel_y_mode = False
    canny_mode = False
    four_view_mode = False
    pending_g = False       # True after 'g' pressed; waits for 'x' or 'y'

    print("Controls:")
    print("  c = capture photo    v = start/stop recording    esc = quit")
    print("  e = color extract    r = rotate +10°             t = threshold")
    print("  b = blur (trackbar)  s = sharpen")
    print("  g+x = Sobel X        g+y = Sobel Y               d = Canny")
    print("  4 = Four View (Original, Laplacian, Sobel X, Sobel Y)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Part 2: Zoom via bottom slider
        zoom_val = slider_state["zoom"]
        zoom_level = 1.0 + zoom_val * 0.1  # 1.0x to 3.0x
        frame = apply_zoom(frame, zoom_level)

        display = frame.copy()

        # Part 2e - 4-view composite: Original, Laplacian, Sobel X, Sobel Y from raw frame
        if four_view_mode:
            gray_raw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            orig_bgr = cv2.cvtColor(gray_raw, cv2.COLOR_GRAY2BGR)
            lap_bgr  = cv2.cvtColor(laplacian_custom(gray_raw), cv2.COLOR_GRAY2BGR)
            sxv_bgr  = cv2.cvtColor(sobel_x_custom(gray_raw),   cv2.COLOR_GRAY2BGR)
            syv_bgr  = cv2.cvtColor(sobel_y_custom(gray_raw),   cv2.COLOR_GRAY2BGR)
            half = (frame.shape[1] // 2, frame.shape[0] // 2)
            for panel, lbl in [(orig_bgr, "Original"), (lap_bgr, "Laplacian"),
                               (sxv_bgr, "Sobel X"),   (syv_bgr, "Sobel Y")]:
                (tw, th), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(panel, (4, 4), (tw + 8, th + 10), (0, 0, 0), -1)
                cv2.putText(panel, lbl, (6, th + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            row1 = np.hstack([cv2.resize(orig_bgr, half), cv2.resize(lap_bgr, half)])
            row2 = np.hstack([cv2.resize(sxv_bgr, half),  cv2.resize(syv_bgr, half)])
            cv2.imshow("Four View", np.vstack([row1, row2]))

        # Part 4- Image processing modes (toggled by key presses)
        if color_mode:
            display = extract_color(display)

        if rotation_angle % 360 != 0:
            display = rotate_frame(display, rotation_angle)

        if threshold_mode:
            gray = cv2.cvtColor(display, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            display = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

        if blur_mode:
            sigma = slider_state["blur"]
            display = cv2.GaussianBlur(display, (0, 0), sigma, sigma)

        if sharpen_mode:
            display = sharpen(display)

        # Part 1a/b - Sobel X and Y gradient modes
        if sobel_x_mode:
            ksize = 2 * cv2.getTrackbarPos("Sobel ksize", win) + 1
            gray = cv2.cvtColor(display, cv2.COLOR_BGR2GRAY)
            sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=ksize)
            display = cv2.cvtColor(cv2.convertScaleAbs(sx), cv2.COLOR_GRAY2BGR)

        if sobel_y_mode:
            ksize = 2 * cv2.getTrackbarPos("Sobel ksize", win) + 1
            gray = cv2.cvtColor(display, cv2.COLOR_BGR2GRAY)
            sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=ksize)
            display = cv2.cvtColor(cv2.convertScaleAbs(sy), cv2.COLOR_GRAY2BGR)

        # Part 1c - Canny edge detector mode
        if canny_mode:
            t1 = max(1, cv2.getTrackbarPos("Canny T1", win))
            t2 = max(1, cv2.getTrackbarPos("Canny T2", win))
            gray = cv2.cvtColor(display, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, t1, t2)
            display = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        # Part 2 - timestamp in bottom-right
        display, roi_bounds = add_timestamp(display)

        # Part 3b - copy timestamp ROI to top-right
        display = copy_timestamp_roi(display, roi_bounds)

        # Part 3d - blend OpenCV logo at top-left
        display = blend_logo(display, logo)

        # Part 3c - red constant border
        display = cv2.copyMakeBorder(
            display, BORDER, BORDER, BORDER, BORDER,
            cv2.BORDER_CONSTANT, value=(0, 0, 255)
        )

        # Part 2 - video recording, write frame and show REC indicator
        if recording and video_writer is not None:
            video_writer.write(display)
            h_d, w_d = display.shape[:2]
            # Red dot + REC label in top-right (inside border)
            cv2.circle(display, (w_d - BORDER - 12, BORDER + 12), 7, (0, 0, 255), -1)
            cv2.putText(display, "REC", (w_d - BORDER - 50, BORDER + 17),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)

        _frame_wh[:] = [display.shape[1], display.shape[0]]
        draw_sliders(display, slider_state["zoom"], slider_state["blur"])

        # Button bar: highlight active toggles by their index in BUTTON_DEFS
        active_btns = set()
        if recording:       active_btns.add(1)
        if color_mode:      active_btns.add(2)
        if threshold_mode:  active_btns.add(4)
        if blur_mode:       active_btns.add(5)
        if sharpen_mode:    active_btns.add(6)
        if sobel_x_mode:    active_btns.add(7)
        if sobel_y_mode:    active_btns.add(8)
        if canny_mode:      active_btns.add(9)
        draw_button_bar(display, active_btns)

        # Part 3a - White flash on capture
        if flash_frames > 0:
            cv2.imshow(win, np.full_like(display, 255))
            flash_frames -= 1
        else:
            cv2.imshow(win, display)

        # key handling — merge keyboard press with any pending mouse button click
        key = cv2.waitKey(1) & 0xFF
        if key == 0xFF and pending_key["val"] != -1:
            key = pending_key["val"] & 0xFF
            pending_key["val"] = -1

        # Part 1a/b - chord key: 'g' then 'x'/'y' activates Sobel modes
        if key == ord('g'):
            pending_g = True

        elif pending_g and key != 0xFF:
            pending_g = False
            if key == ord('x'):
                sobel_x_mode = not sobel_x_mode
                print(f"Sobel X: {'ON' if sobel_x_mode else 'OFF'}")
            elif key == ord('y'):
                sobel_y_mode = not sobel_y_mode
                print(f"Sobel Y: {'ON' if sobel_y_mode else 'OFF'}")

        elif key == 0x01:  # mouse-clicked Sobel X button
            sobel_x_mode = not sobel_x_mode
            print(f"Sobel X: {'ON' if sobel_x_mode else 'OFF'}")

        elif key == 0x02:  # mouse-clicked Sobel Y button
            sobel_y_mode = not sobel_y_mode
            print(f"Sobel Y: {'ON' if sobel_y_mode else 'OFF'}")

        # Part 1c - Canny toggle
        elif key == ord('d'):
            canny_mode = not canny_mode
            print(f"Canny: {'ON' if canny_mode else 'OFF'}")

        # Part 2e - four-view window toggle
        elif key == ord('4'):
            four_view_mode = not four_view_mode
            if not four_view_mode:
                cv2.destroyWindow("Four View")
            print(f"Four View: {'ON' if four_view_mode else 'OFF'}")

        elif key == 27:  # esc — exit
            break

        elif key == ord('c'):  # capture photo
            flash_frames = 5  # show white flash for 5 frames
            photo_count += 1
            fname = os.path.join(SAVE_DIR, f"photo_{photo_count:03d}.jpg")
            cv2.imwrite(fname, display)
            print(f"Photo saved: {fname}")

        elif key == ord('v'):  # toggle video recording
            if not recording:
                video_count += 1
                fname = os.path.join(SAVE_DIR, f"video_{video_count:03d}.avi")
                h_d, w_d = display.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                video_writer = cv2.VideoWriter(fname, fourcc, 20.0, (w_d, h_d))
                recording = True
                print(f"Recording started: {fname}")
            else:
                recording = False
                video_writer.release()
                video_writer = None
                print("Recording stopped.")

        elif key == ord('e'):  # toggle color extraction
            color_mode = not color_mode
            print(f"Color extraction: {'ON' if color_mode else 'OFF'}")

        elif key == ord('r'):  # rotate +10 degrees
            rotation_angle = (rotation_angle + 10) % 360
            print(f"Rotation: {rotation_angle}°")

        elif key == ord('t'):  # toggle threshold
            threshold_mode = not threshold_mode
            print(f"Threshold: {'ON' if threshold_mode else 'OFF'}")

        elif key == ord('b'):  # toggle Gaussian blur
            blur_mode = not blur_mode
            print(f"Blur: {'ON' if blur_mode else 'OFF'}")

        elif key == ord('s'):  # toggle sharpen
            sharpen_mode = not sharpen_mode
            print(f"Sharpen: {'ON' if sharpen_mode else 'OFF'}")

    # release everything on exit
    if recording and video_writer is not None:
        video_writer.release()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

