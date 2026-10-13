# ✦ WINGARDIUM LEVIOSA ✦
## Real-Time Computer Vision Magic System (Image & Video Processing Project)

**Wingardium Leviosa** is a real-time computer vision application built for college-level **Image & Video Processing (IVP)** coursework. It allows users to point a hand or physical wand at an object in front of a live webcam, cast magic spells via voice ("Wingardium Leviosa", "Accio", "Expelliarmus", "Finite") or UI buttons, and visually detach, levitate, translate, rotate, and scale the object in real-time while seamlessly reconstructing the background behind it.

---

## 📸 System Architecture & Features

```text
wingardium_leviosa/
│
├── main.py                    # Main application launcher & render loop
├── requirements.txt           # Python dependency specifications
├── README.md                  # Project documentation & algorithm guide
│
├── config/
│   └── settings.py            # Global configuration, color themes, physics & FX constants
│
├── camera/
│   └── camera.py              # Video stream capture, FPS tracking & synthetic fallback generator
│
├── tracking/
│   ├── hand_tracker.py        # MediaPipe HandLandmarker API & OpenCV skin/contour fallback
│   └── wand_tracker.py        # Color thresholding wand/stick tip tracker
│
├── detection/
│   └── object_detector.py     # Pointing ray projection, Canny edge & contour region detection
│
├── segmentation/
│   └── object_segmenter.py    # OpenCV GrabCut algorithm, Otsu thresholding & alpha matting
│
├── processing/
│   ├── background.py          # Background frame capture, inpainting & temporal reference modeling
│   ├── compositing.py         # Multi-layer scene compositing & alpha blending
│   ├── transformations.py    # 2D Affine transformations (translation, rotation, scaling)
│   ├── effects.py             # Particle system, wand light trails, drop shadows & magical aura glows
│   └── smoothing.py           # Exponential Moving Average (EMA) coordinate filtering
│
├── magic/
│   ├── spell_controller.py    # High-level spell state machine & hand interaction binding
│   └── physics.py             # Spring-damper physics, velocity damping & sinusoidal floating
│
├── speech/
│   └── speech_controller.py   # Asynchronous voice incantation recognition background worker
│
└── ui/
    └── interface.py           # Tkinter dark magical GUI with live viewport & control panel
```

---

## 🎓 How this project demonstrates Image & Video Processing

This project implements fundamental and advanced Image & Video Processing (IVP) algorithms. Each module visibly demonstrates real mathematical transformations on digital image frames:

| IVP Concept | Implementation Details | Academic Rationale |
| :--- | :--- | :--- |
| **Image Acquisition & Frame Buffering** | OpenCV `cv2.VideoCapture` captures BGR frames at 1280x720@30FPS with color space conversion (BGR to RGB/HSV/RGBA). | Converts analog camera signals into discrete 2D spatial pixel matrices $I(x,y,c)$. |
| **Hand Landmark Detection** | MediaPipe HandLandmarker / Tasks API tracks 21 3D hand joints. | Extracts geometric topology to convert continuous visual hand poses into vector coordinates. |
| **Pointing Ray Projection** | Vector algebra between Index MCP (landmark 5) and Index Tip (landmark 8): $\vec{v} = \frac{\mathbf{P}_8 - \mathbf{P}_5}{\|\mathbf{P}_8 - \mathbf{P}_5\|}$. | Projects directional ray across the image space to determine target object intersection. |
| **Edge Detection & Contour Extraction** | Canny edge filter with Gaussian pre-smoothing ($\sigma=1.0$) followed by morphological dilation (`cv2.dilate`). | Detects spatial intensity gradients $\nabla I(x,y)$ to find candidate object boundaries. |
| **Foreground Image Segmentation** | **OpenCV GrabCut (`cv2.grabCut`)** iteratively solves Gaussian Mixture Models (GMM) and Graph Cuts ($G = (V,E)$) to split foreground/background. | Isolates arbitrary complex object regions without pre-trained model dependencies. |
| **Background Reconstruction & Inpainting** | Stored clean reference background matrix $B_0(x,y)$ combined with Navier-Stokes / Fast Marching Inpainting (`cv2.inpaint`). | Solves partial differential equations to estimate occluded scene pixels when object levitates. |
| **Image Masking & Soft Feathering** | Gaussian blurring of binary mask: $M_{feather} = M * G_\sigma$, producing continuous alpha maps $[0.0, 1.0]$. | Prevents high-frequency edge aliasing (staircasing) during object extraction. |
| **2D Affine Transformations** | 2D Transformation Matrix $M = \begin{bmatrix} s\cos\theta & -s\sin\theta & t_x \\ s\sin\theta & s\cos\theta & t_y \end{bmatrix}$ via `cv2.warpAffine`. | Rotates, scales, and translates object cutouts smoothly across frame space. |
| **Multi-Layer Alpha Compositing** | Alpha blending formula: $I_{out} = (1 - \alpha) \cdot I_{bg} + \alpha \cdot I_{fg} + I_{fx}$. | Combines background, drop shadow, aura glow, floating object, and particle FX into single output. |
| **Temporal Coordinate Smoothing** | Exponential Moving Average (EMA): $S_t = \alpha Y_t + (1 - \alpha) S_{t-1}$ to filter micro-jitter. | Eliminates high-frequency noise from real-time hand tracking measurements. |
| **Shadow Projection & Attenuation** | Dynamic Gaussian blur radius scaling ($r \propto \Delta y$) and alpha attenuation ($\alpha \propto \frac{1}{\Delta y}$). | Simulates optical physics of light occlusion on the surface below floating objects. |
| **Real-Time Performance Optimization** | Processing on reduced ROIs, background threading for voice recognition, frame skipping. | Maintains real-time latency (< 25ms/frame) on standard laptop hardware. |

---

## 🪄 Magic Spell Commands

1. **"Wingardium Leviosa" (Levitation)**
   - *Effect*: Object detaches from table, background is inpainted/reconstructed, object ascends and hovers smoothly. Follows index finger or wand position, wrist rotation, and movement.
2. **"Accio" (Summoning Spell)**
   - *Effect*: Object accelerates towards camera/hand with scale enlargement ($s \to 1.4$), simulating fast approach towards user.
3. **"Expelliarmus" (Disarming Spell)**
   - *Effect*: Blasts the object away from the hand (or screen center) with a visible throw and golden spark trail.
4. **"Finite" (Counter-Spell)**
   - *Effect*: Cancels all magic, smoothly returns object back to its exact original table location, and re-integrates it.

---

## 🚀 Setup & Run Instructions

### Prerequisites
- Python 3.11 (required for the tested MediaPipe hand-landmark runtime)
- Webcam (or synthetic camera fallback mode)
- Microphone (optional, buttons/keyboard available)
- Internet connection for Google Speech Recognition voice commands

### Installation
1. Clone or download project repository:
   ```bash
   cd "c:/Users/hp/OneDrive/Desktop/IVP Project"
   ```

2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

3. Run the Application:
   ```bash
   python main.py
   ```

---

## 🎬 College Demo Walkthrough (For Professor Presentation)

1. **Start Application**: Run `python main.py`. The dark magical GUI window opens displaying live camera feed.
2. **Capture Background**: Click **📷 CAPTURE BACKGROUND** (or press key `B`) while the table scene is clear.
3. **Select and Lift an Object**: Draw a closed circle around an object with your tracked index fingertip. The circled area is selected and lifted automatically. Alternatively, click an object in the camera viewport to select it manually.
4. **Guide the Object**: Move your hand left, right, up, or down to steer the floating object. Show an open palm or make a fist to pause it. The original area is reconstructed while the object floats with visual effects.
5. **Cast Accio**: Say **"Accio!"** or click **🧲 ACCIO** button. Object flies towards camera while scaling up.
6. **Cast Finite**: Click **✋ FINITE** to return the object to its original position while keeping it selected. Click **DESELECT OBJECT** or press **Esc** to clear the selection entirely.
7. **Toggle Debug Mode**: Press key `D` or click **🐞 TOGGLE DEBUG MODE**. Show professor the hand landmarks, pointing ray vector, GrabCut ROI box, background status, and real-time FPS metrics!

---

## 🛡️ Robust Fallbacks

- **No Camera?** Automatically activates synthetic magic room simulation feed.
- **No Microphone?** Provides visible UI spell buttons and keyboard shortcuts (`1`-`4`, `B`, `D`, and `Esc` to deselect).
- **No Physical Wand?** Tracks MediaPipe index finger landmarks for circle selection and object control.
- **MediaPipe Unavailable?** Hand gestures are disabled rather than treating faces or other skin-colored regions as hands; click object selection and spell buttons remain available.
