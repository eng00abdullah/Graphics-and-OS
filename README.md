# 🖥️ OS Scheduler 3D Visualizer
### CPU Scheduling Algorithms + Deadlock Detection with Interactive 3D Graphics

---

> **Innovation University**
> **Course Supervisor:** Dr. Ahmed Salama
> **Teaching Assistant:** Eng. Aya Hassan

---

## 📌 Overview

**OS Scheduler 3D** is an interactive desktop application that simulates and visualizes classic CPU scheduling algorithms and deadlock detection using real-time 3D OpenGL graphics. Users input process data through a modern dark-themed GUI, and the application renders animated 3D Gantt charts, performance bar charts, and Resource Allocation Graphs (RAG).

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎨 **GUI Input** | All data entered through a Tkinter dark-themed GUI — no console typing required |
| 📊 **3D Gantt Chart** | Process bursts rendered as 3D extruded blocks with realistic lighting & shading |
| 📈 **3D Averages Chart** | Turnaround Time (TAT) and Waiting Time (WT) visualized as animated 3D bar charts |
| 🔵 **3D Resource Allocation Graph** | RAG uses 3D spheres for processes and cylinders for resources |
| 🎨 **Color Picker** | Customize Gantt bar color per process from the "Gantt Colors" tab |
| 🔁 **Multi-Run** | Press **N** in the visualizer to load a new dataset without closing the window |
| 🖱️ **Interactive 3D Rotation** | Drag to rotate the Gantt chart freely in 3D space |
| ⚡ **Speed Control** | Adjust animation speed (0.25× – 4×) |
| ⏸️ **Pause & Step** | Pause and manually step through the animation timeline |
| 🔢 **7 Algorithms** | FCFS · Round Robin · SJF · SRTF · Priority (Non-Pre) · Priority (Pre) · Deadlock (Banker's) |

---

## 🗂️ Project Structure

```
scheduler_v4/
├── main.py              ← Entry point — run this to start the app
├── gui_input.py         ← Tkinter GUI for all user input & algorithm selection
├── visualizer.py        ← OpenGL 3D rendering engine (Gantt, charts, RAG, popups)
├── draw3d.py            ← 3D primitives library (bars, spheres, cylinders, cones, grid)
├── innovation-university-Logo.png  ← University logo displayed in the GUI
└── README.md            ← This file
```

---

## ⚙️ Requirements

**Python 3.8+** is required. Install dependencies via pip:

```bash
pip install PyOpenGL PyOpenGL_accelerate Pillow
```

> **Tkinter** is bundled with Python on most systems.
> If missing on Linux, install it with:
> ```bash
> sudo apt install python3-tk   # Ubuntu / Debian
> ```

---

## 🚀 How to Run

```bash
cd scheduler_v4
python main.py
```

The GUI window will open. Select an algorithm, enter your process data, and click **Run** to launch the 3D visualizer.

---

## 🎮 Controls

| Key / Action | Description |
|---|---|
| **N** | New Run — opens a fresh input GUI without closing the visualizer |
| **Q** / **Esc** | Quit the application |
| **Mouse Drag** | Rotate the 3D Gantt chart horizontally and vertically |
| **1 – 7** | Switch between algorithms directly from the visualizer |
| **Space** | Pause / Resume animation |
| **← / →** | Step backward / forward through the animation (when paused) |
| **↑ / ↓** | Increase / Decrease animation speed |

---

## 🧮 Algorithms

| # | Algorithm | Type | Notes |
|---|-----------|------|-------|
| 1 | **FCFS** | Non-preemptive | Processes scheduled in arrival order |
| 2 | **Round Robin** | Preemptive | Configurable time quantum |
| 3 | **SJF** | Non-preemptive | Shortest CPU burst scheduled first |
| 4 | **SRTF** | Preemptive | Shortest Remaining Time First |
| 5 | **Priority (Non-Pre)** | Non-preemptive | Lower number = higher priority |
| 6 | **Priority (Pre)** | Preemptive | Lower number = higher priority |
| 7 | **Deadlock (Banker's)** | Detection | Detects safe/unsafe states, shows safety sequence and 3D RAG |

---

## 📷 Visualizer Views

- **Gantt Chart** — Animated 3D bars with per-process colors, time axis, and process labels
- **Average Stats** — Side-by-side 3D bar chart for TAT and WT per process
- **RAG (Deadlock mode)** — 3D graph with spheres (processes), cylinders (resources), and directional arrows showing allocation and request edges

---

## 🏫 Academic Information

| | |
|---|---|
| **University** | Innovation University |
| **Course** | Operating Systems |
| **Supervisor** | Dr. Ahmed Salama |
| **Teaching Assistant** | Eng. Aya Hassan |
