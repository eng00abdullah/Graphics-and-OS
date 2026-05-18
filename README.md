# OS Scheduler 3D Visualizer
## CPU Scheduling + Deadlock Detection with 3D Graphics

---

### Requirements

```bash
pip install PyOpenGL PyOpenGL_accelerate
# tkinter is bundled with Python on most systems
# If not: sudo apt install python3-tk  (Ubuntu/Debian)
```

---

### How to Run

```bash
cd scheduler_3d
python main.py
```

---

### Features

| Feature | Description |
|---------|-------------|
| **GUI Input** | All data entered through a Tkinter GUI window — no console typing |
| **3D Gantt Chart** | Bars rendered as 3D extruded blocks with lighting & shading |
| **3D Averages** | TAT and WT shown as 3D bar charts |
| **3D RAG** | Resource Allocation Graph uses 3D spheres (processes) and cylinders (resources) |
| **Color Picker** | Change Gantt bar color per process from the "Gantt Colors" tab or per-row button |
| **Multi-Run** | Press **N** in the visualizer to open a new input GUI without closing the window |
| **Algorithms** | FCFS · Round Robin · SJF · Priority · Deadlock (Banker's) |

---

### Controls

| Key | Action |
|-----|--------|
| **N** | New Run — opens GUI for another algorithm/dataset |
| **Q** or **Esc** | Quit |

---

### Project Structure

```
scheduler_3d/
├── main.py          ← Entry point (run this)
├── gui_input.py     ← Tkinter GUI for all user input
├── visualizer.py    ← OpenGL 3D rendering engine
├── draw3d.py        ← 3D primitives (bars, spheres, cylinders, arrows)
└── README.md        ← This file
```

---

### Algorithm Notes

- **FCFS** — Non-preemptive, arrival order
- **Round Robin** — Preemptive, configurable time quantum
- **SJF** — Non-preemptive, shortest burst first
- **Priority** — Non-preemptive, lowest number = highest priority
- **Deadlock (Banker's)** — Detects safe/unsafe states, shows safety sequence and Resource Allocation Graph
