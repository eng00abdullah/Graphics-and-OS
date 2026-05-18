"""
visualizer.py  —  OS Scheduler 3D  Enhanced Interactive Visualizer
Features: 3D drag-rotate Gantt, sidebar algo switcher, process click popup,
          compare mode, step-through, speed control, keyboard shortcuts 1-7.
"""
from OpenGL.GL   import *
from OpenGL.GLUT import *
from OpenGL.GLU  import *
import math, time, os
import draw3d

try:
    from PIL import Image as _PILImage
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

_LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "innovation-university-Logo.png")
_logo_tex   = None   # OpenGL texture id
_logo_w     = 0
_logo_h     = 0

# ═══════════════════════════════════════════════════════════
#  GLOBALS
# ═══════════════════════════════════════════════════════════
WINDOW_W, WINDOW_H = 1440, 860
SIDEBAR_W = 0         # sidebar removed

_on_new_run_cb = None
current_algo   = 0
ALGO_DATA      = {}

ALGO_NAMES = ["FCFS","Round Robin","SJF","SRTF",
              "Priority (Non-Pre)","Priority (Pre)","Deadlock (Banker's)"]
ALGO_SHORT = ["FCFS","Round Robin","SJF","SRTF",
              "Priority (Non-Pre)","Priority (Pre)","Deadlock (Banker's)"]

PROC_COLORS = [
    (0.17,0.50,1.00),(0.13,0.87,0.40),(1.00,0.55,0.10),
    (0.67,0.27,1.00),(1.00,0.20,0.33),(0.00,0.83,0.83),
    (1.00,0.40,0.73),(0.40,1.00,0.40),
]

# Palette
BG    =(0.024,0.024,0.055); ACCENT=(0.17,0.50,1.00); ACCENT2=(0.00,0.80,0.90)
GREEN =(0.13,0.87,0.40);    RED   =(1.00,0.20,0.33); YELLOW =(1.00,0.87,0.13)
PURPLE=(0.67,0.27,1.00);    ORANGE=(1.00,0.55,0.10); GRAY   =(0.50,0.50,0.62)
WHITE =(1.00,1.00,1.00);    DARK  =(0.04,0.04,0.13); DARK2  =(0.06,0.06,0.16)

# ── Animation ────────────────────────────────────────────
_anim_start     = 0.0
_paused         = False
_manual_time    = 0.0
_speed_levels   = [0.25, 0.5, 1.0, 2.0, 4.0]
_speed_idx      = 2
_compare_mode   = False

GANTT_DUR  = 1.8
FADE_DUR   = 0.55
SLIDE_DUR  = 0.45
SEQ_DELAY  = 0.36

# ── Mouse ─────────────────────────────────────────────────
_mouse_x    = 0
_mouse_y    = 0
_drag_active= False
_drag_start_x=0

# ── 3D Gantt rotation (mouse drag) ───────────────────────
_gantt_rot_y   = -18.0   # horizontal rotation (yaw)
_gantt_rot_x   =  12.0   # vertical tilt (pitch)
_drag_gantt    = False
_drag_gx       = 0
_drag_gy       = 0
_drag_rot_start_y = 0.0
_drag_rot_start_x = 0.0

# ── Process selection popup ───────────────────────────────
_selected_pid    = -1
_popup_x         = 0
_popup_y         = 0

GH_GLOBAL = 200   # set by draw_sched, read by draw_gantt_3d

# ── Precomputed results ───────────────────────────────────
_cached_gantt   = None
_cached_results = None
_cached_total   = 1

# ─────────────────────────────────────────────────────────
def elapsed():
    if _paused:
        return _manual_time / max(_speed_levels[_speed_idx], 0.001)
    raw = time.time() - _anim_start
    return raw * _speed_levels[_speed_idx]

def gantt_revealed():
    """How many time-units of Gantt are currently visible."""
    if _paused:
        return _manual_time
    t = elapsed()
    return _cached_total * ease_in_out(min(1.0, t / max(GANTT_DUR, 0.001)))

def anim_t(d=1.0):
    return min(1.0, elapsed() / max(d, 0.001))

def ease_out(t):
    t=max(0.0,min(1.0,t)); return 1-(1-t)**2.5
def ease_in_out(t):
    t=max(0.0,min(1.0,t)); return t*t*(3-2*t)
def bounce_out(t):
    t=max(0.0,min(1.0,t))
    if t<1/2.75:     return 7.5625*t*t
    elif t<2/2.75:   t-=1.5/2.75;  return 7.5625*t*t+0.75
    elif t<2.5/2.75: t-=2.25/2.75; return 7.5625*t*t+0.9375
    else:            t-=2.625/2.75;return 7.5625*t*t+0.984375
def pulse(s=2.0): return (math.sin(time.time()*s*math.pi)+1)*0.5
def shimmer():    return (math.sin(time.time()*1.4*math.pi)+1)*0.5

# ═══════════════════════════════════════════════════════════
#  2D HELPERS
# ═══════════════════════════════════════════════════════════
def begin_2d():
    glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity()
    gluOrtho2D(0,WINDOW_W,0,WINDOW_H)
    glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity()
    glDisable(GL_DEPTH_TEST);glDisable(GL_LIGHTING)
def end_2d():
    glMatrixMode(GL_PROJECTION);glPopMatrix()
    glMatrixMode(GL_MODELVIEW);glPopMatrix()
    glEnable(GL_DEPTH_TEST);glEnable(GL_LIGHTING)

def dt(x,y,text,font=GLUT_BITMAP_9_BY_15):
    glRasterPos2f(x,y)
    for c in str(text): glutBitmapCharacter(font,ord(c))
def dtb(x,y,t): dt(x,y,t,GLUT_BITMAP_HELVETICA_18)
def dtl(x,y,t): dt(x,y,t,GLUT_BITMAP_TIMES_ROMAN_24)
def dts(x,y,t): dt(x,y,t,GLUT_BITMAP_8_BY_13)

def frect(x,y,w,h,col,a=1.0):
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(*col,a);glBegin(GL_QUADS)
    glVertex2f(x,y);glVertex2f(x+w,y);glVertex2f(x+w,y+h);glVertex2f(x,y+h)
    glEnd();glDisable(GL_BLEND)
def grect(x,y,w,h,cb,ct,a=1.0):
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    glColor4f(*cb,a);glVertex2f(x,y);glVertex2f(x+w,y)
    glColor4f(*ct,a);glVertex2f(x+w,y+h);glVertex2f(x,y+h)
    glEnd();glDisable(GL_BLEND)
def orect(x,y,w,h,col,lw=1.5,a=1.0):
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(lw);glColor4f(*col,a);glBegin(GL_LINE_LOOP)
    glVertex2f(x,y);glVertex2f(x+w,y);glVertex2f(x+w,y+h);glVertex2f(x,y+h)
    glEnd();glDisable(GL_BLEND)
def circ(cx,cy,r,col,filled=True,a=1.0):
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(*col,a)
    glBegin(GL_POLYGON if filled else GL_LINE_LOOP)
    for i in range(48):
        ang=2*math.pi*i/48; glVertex2f(cx+r*math.cos(ang),cy+r*math.sin(ang))
    glEnd();glDisable(GL_BLEND)
def arrow2d(x1,y1,x2,y2,col,lw=2.0,a=1.0):
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(lw);glColor4f(*col,a)
    glBegin(GL_LINES);glVertex2f(x1,y1);glVertex2f(x2,y2);glEnd()
    ang=math.atan2(y2-y1,x2-x1);s=10
    glBegin(GL_TRIANGLES)
    glVertex2f(x2,y2)
    glVertex2f(x2-s*math.cos(ang-0.42),y2-s*math.sin(ang-0.42))
    glVertex2f(x2-s*math.cos(ang+0.42),y2-s*math.sin(ang+0.42))
    glEnd();glDisable(GL_BLEND)

def panel(x,y,w,h,title="",a=1.0,glow=None):
    grect(x+1,y+1,w-2,h-2,(0.055,0.060,0.175),(0.072,0.078,0.220),0.94*a)
    s=shimmer()
    if glow:
        bc=tuple(min(c*(0.7+0.5*s),1.0) for c in glow); lw=2.0+s*2.0
        glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(lw+2);glColor4f(bc[0]*0.4,bc[1]*0.4,bc[2]*0.4,0.22*a*s)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x-1,y-1);glVertex2f(x+w+1,y-1)
        glVertex2f(x+w+1,y+h+1);glVertex2f(x-1,y+h+1)
        glEnd();glDisable(GL_BLEND)
    else:
        bc,lw=ACCENT,1.8
    orect(x,y,w,h,bc,lw,a)
    if title:
        tc=glow if glow else ACCENT
        grect(x+1,y+h-32,w-2,31,(tc[0]*0.10,tc[1]*0.10,tc[2]*0.22),
              (tc[0]*0.20,tc[1]*0.20,tc[2]*0.38),0.88*a)
        glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(*(glow if glow else ACCENT),a)
        dts(x+10,y+h-22,title)
        glLineWidth(1.0);glColor4f(*bc,0.40*a)
        glBegin(GL_LINES)
        glVertex2f(x+2,y+h-33);glVertex2f(x+w-2,y+h-33)
        glEnd();glDisable(GL_BLEND)

# ═══════════════════════════════════════════════════════════
#  BACKGROUND
# ═══════════════════════════════════════════════════════════
def draw_background():
    begin_2d()
    glBegin(GL_QUADS)
    glColor3f(0.020,0.020,0.050);glVertex2f(0,0);glVertex2f(WINDOW_W,0)
    glColor3f(0.040,0.040,0.110);glVertex2f(WINDOW_W,WINDOW_H);glVertex2f(0,WINDOW_H)
    glEnd()
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.08,0.08,0.22,0.12);glLineWidth(0.5)
    glBegin(GL_LINES)
    for gx in range(0,WINDOW_W,72):glVertex2f(gx,0);glVertex2f(gx,WINDOW_H)
    for gy in range(0,WINDOW_H,72):glVertex2f(0,gy);glVertex2f(WINDOW_W,gy)
    glEnd();glDisable(GL_BLEND)
    end_2d()

# ═══════════════════════════════════════════════════════════
#  NAVBAR  (top 54px)
# ═══════════════════════════════════════════════════════════
def draw_navbar():
    grect(0,WINDOW_H-54,WINDOW_W,54,(0.030,0.030,0.095),(0.060,0.060,0.175),1.0)
    s=shimmer()
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(1.8);glColor4f(ACCENT[0],ACCENT[1],ACCENT[2]+0.25*s,0.65+0.35*s)
    glBegin(GL_LINES);glVertex2f(0,WINDOW_H-54);glVertex2f(WINDOW_W,WINDOW_H-54);glEnd()

    # Logo icon bg
    frect(12,WINDOW_H-46,36,36,(0.17,0.50,1.00),1.0)
    glColor4f(1,1,1,1.0);dts(16,WINDOW_H-33,"OS")

    # Title
    p=pulse(0.6)
    glColor4f(1.0,1.0,1.0,1.0);dtb(56,WINDOW_H-34,"OS SCHEDULER ")
    glColor4f(ACCENT[0],ACCENT[1]+0.08*p,ACCENT[2],1.0)
    dtb(56+130,WINDOW_H-34,"3D")
    glColor4f(*GRAY,0.5);dts(56+162,WINDOW_H-32,"  CPU SCHEDULING · DEADLOCK VISUALIZER")

    # Algo badge (center)
    if current_algo>=0:
        ta=ease_out(anim_t(0.35)); name=ALGO_NAMES[current_algo]
        bw=max(190,len(name)*10+36); bx=WINDOW_W//2-bw//2
        bc=ACCENT2;p2=pulse(1.6)
        frect(bx,WINDOW_H-50,bw,50,(bc[0]*0.05,bc[1]*0.05,bc[2]*0.10),0.95*ta)
        glLineWidth(2.0+p2);glColor4f(*bc,(0.6+0.4*p2)*ta)
        glBegin(GL_LINE_LOOP)
        glVertex2f(bx,WINDOW_H-50);glVertex2f(bx+bw,WINDOW_H-50)
        glVertex2f(bx+bw,WINDOW_H);glVertex2f(bx,WINDOW_H)
        glEnd()
        # Dot indicator
        circ(bx+12,WINDOW_H-26,5,ACCENT2,ta)
        glColor4f(*WHITE,ta);dtb(bx+22,WINDOW_H-33,name)

    # Speed display
    spd_str=f"{_speed_levels[_speed_idx]:.2g}x"
    spd_x=WINDOW_W-280
    glColor4f(*GRAY,0.55);dts(spd_x-36,WINDOW_H-32,"SPEED")
    frect(spd_x,WINDOW_H-44,62,28,(0.10,0.10,0.28),0.7)
    glColor4f(*YELLOW,1.0);dtb(spd_x+4,WINDOW_H-33,spd_str)
    # speed - + buttons drawn as text hints
    glColor4f(*GRAY,0.55);dts(spd_x-22,WINDOW_H-32,"−")
    glColor4f(*GRAY,0.55);dts(spd_x+68,WINDOW_H-32,"+")

    # Pause indicator
    if _paused:
        frect(WINDOW_W-200,WINDOW_H-46,90,32,(0.25,0.12,0.05),0.85)
        orect(WINDOW_W-200,WINDOW_H-46,90,32,ORANGE,1.8,0.9)
        glColor4f(*ORANGE,1.0);dts(WINDOW_W-196,WINDOW_H-33,"⏸ PAUSED")

    # Compare badge
    if _compare_mode:
        frect(WINDOW_W-100,WINDOW_H-46,88,32,(0.05,0.20,0.05),0.85)
        orect(WINDOW_W-100,WINDOW_H-46,88,32,GREEN,1.8,0.9)
        glColor4f(*GREEN,1.0);dts(WINDOW_W-96,WINDOW_H-33,"COMPARE")

    # Hints right
    glColor4f(*GRAY,0.50)
    dts(WINDOW_W-600,WINDOW_H-29,"N=New  Q=Close  TAB=Switch  C=Compare  SPC=Pause  ±=Speed")

    # Innovation University logo — top-right, always on top
    _draw_logo_texture()

    glDisable(GL_BLEND)

# ═══════════════════════════════════════════════════════════
#  SIDEBAR  (left 170px algo switcher)
# ═══════════════════════════════════════════════════════════
_sidebar_hover = -1

def draw_sidebar():
    pass   # sidebar removed — full width layout

def sidebar_click(mx,my):
    return -1   # sidebar removed

# ═══════════════════════════════════════════════════════════
#  3D GANTT CHART — Mouse rotatable
# ═══════════════════════════════════════════════════════════
# Gantt viewport bounds (set during draw, used for hit-testing)
_gantt_vp = (0,0,0,0)   # x,y,w,h in screen coords

def draw_gantt_3d(gantt, y_base, total_time, content_x, content_w):
    global _gantt_vp

    if not gantt: return

    revealed = gantt_revealed()
    la = ease_out(max(0.0, elapsed() - GANTT_DUR) / 0.5)
    fa = ease_out(anim_t(FADE_DUR))

    # Panel fills the given height (GH passed from draw_sched)
    PH = GH_GLOBAL   # set by draw_sched before calling us
    PX = content_x + 4
    PW = content_w - 8

    TICK_H = 22   # space at bottom for time-tick numbers (INSIDE panel)
    ML = 8        # left margin (no PID axis labels needed — labels on bars)
    MR = 8        # right margin
    MB = TICK_H + 2   # bottom margin = tick area
    MT = 36           # top margin (title bar)

    begin_2d()
    panel(PX, y_base, PW, PH, "GANTT CHART 3D", fa, ACCENT)
    glColor4f(*GRAY, fa * 0.65)
    dts(PX + PW - 230, y_base + PH - 22,
        f"Total: {total_time} units · {len(gantt)} segments")
    glColor4f(*GRAY, 0.28)
    dts(PX + 10, y_base + TICK_H + 2, "drag to rotate  ·  ← → step when paused")
    end_2d()

    # ── 3D viewport (fills panel minus margins) ──────────────
    vp_x = int(PX + ML)
    vp_y = int(y_base + MB)
    vp_w = int(PW - ML - MR)
    vp_h = int(PH - MB - MT)
    _gantt_vp = (vp_x, vp_y, vp_w, vp_h)

    glViewport(vp_x, vp_y, vp_w, vp_h)
    glScissor(vp_x, vp_y, vp_w, vp_h); glEnable(GL_SCISSOR_TEST)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluPerspective(42, vp_w / max(vp_h, 1), 1, 4000)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    scale3d = (vp_w - 8) / max(total_time, 1)
    # Scale bar height/depth to fill the 3D viewport nicely
    BH = max(int(vp_h * 0.60), 50)   # 60% of viewport height
    BD = max(int(BH * 0.65), 36)     # depth proportional to height

    # Camera distance scales with viewport so bars always fill the view
    cam_dist = max(vp_h * 2.2, 300)
    bar_mid_y = BH * 0.5
    rad_y = math.radians(_gantt_rot_y)
    rad_x = math.radians(_gantt_rot_x)
    cx_ = cam_dist * math.sin(rad_y) * math.cos(rad_x)
    cy_ = cam_dist * math.sin(rad_x) + bar_mid_y
    cz_ = cam_dist * math.cos(rad_y) * math.cos(rad_x)
    gluLookAt(vp_w / 2 + cx_, cy_, cz_,
              vp_w / 2,       bar_mid_y,  0,
              0, 1, 0)

    glEnable(GL_DEPTH_TEST); glClear(GL_DEPTH_BUFFER_BIT)
    draw3d.setup_lighting()

    draw3d.draw_grid_floor(0, -BD, vp_w, BD + 10, 0,
                           max(scale3d, 8), (0.08, 0.10, 0.30), 0.35)

    for (pid, start, end) in gantt:
        if start >= revealed: break
        ve  = min(end, revealed)
        bx3 = start * scale3d
        bw3 = (ve - start) * scale3d
        col = PROC_COLORS[pid % len(PROC_COLORS)]
        if bw3 > 0.5:
            if pid == _selected_pid:
                draw3d.draw_bar_3d(bx3 + 1, 0, 0, max(bw3 - 2, 0.5),
                                   BH + 6, BD + 4,
                                   tuple(min(c * 1.4, 1) for c in col), 1.0)
            draw3d.draw_bar_3d(bx3 + 1, 0, 0, max(bw3 - 2, 0.5),
                               BH, BD, col, 0.95)

    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW);  glPopMatrix()
    glDisable(GL_SCISSOR_TEST); glViewport(0, 0, WINDOW_W, WINDOW_H)
    glDisable(GL_DEPTH_TEST);   draw3d.lighting_off()

    # ── 2D overlay: labels + ruler ───────────────────────────
    begin_2d()
    scale2d   = vp_w / max(total_time, 1)
    bar_x2d   = vp_x
    bar_ctr_y = vp_y + vp_h // 2 + 6   # vertical mid of bars in 2D coords

    # ── RULER — colored segments + time numbers ───────────────
    # Ruler strip sits at very bottom of panel (inside TICK_H area)
    RH      = 16    # ruler bar height (colored segments)
    RNUM_Y  = y_base + 4          # number baseline
    RBAR_Y  = y_base + TICK_H - RH - 2   # colored bar top

    # ── PID labels — pinned just above the ruler strip ──────────────────
    LABEL_Y = RBAR_Y - 14   # just above colored ruler bar
    for (pid, start, end) in gantt:
        if start >= revealed: break
        ve  = min(end, revealed)
        bx2 = bar_x2d + start * scale2d
        bw2 = (ve - start) * scale2d
        col = PROC_COLORS[pid % len(PROC_COLORS)]
        lbl = f"P{pid}"
        char_w = 9.5

        if bw2 >= 16:
            tx = bx2 + bw2 / 2 - len(lbl) * char_w / 2
            # Colored shadow matching process color
            glColor4f(*col, 0.55 * la)
            dtb(tx + 1, LABEL_Y - 1, lbl)
            # Bright white label
            glColor4f(1.0, 1.0, 1.0, min(la, 1.0))
            dtb(tx, LABEL_Y, lbl)

        # Selection outline
        if pid == _selected_pid and bw2 > 4:
            orect(bx2, vp_y, bw2, vp_h, WHITE, 2.5, la * 0.9)

    # Draw colored ruler segments (one per gantt entry, proportional)
    for (pid, start, end) in gantt:
        if start >= revealed: break
        ve  = min(end, revealed)
        bx2 = bar_x2d + start * scale2d
        bw2 = (ve - start) * scale2d
        col = PROC_COLORS[pid % len(PROC_COLORS)]
        if bw2 > 0.5:
            frect(bx2, RBAR_Y, bw2, RH, col, 0.82 * la)

    # Ruler outline
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(0.8); glColor4f(*GRAY, 0.30 * la)
    glBegin(GL_LINES)
    glVertex2f(bar_x2d, RBAR_Y); glVertex2f(bar_x2d + vp_w, RBAR_Y)
    glEnd(); glDisable(GL_BLEND)

    # Tick interval
    raw_step = total_time / max(vp_w / 55, 1)
    tick_step = 1
    for step in [1,2,5,10,20,50,100]:
        if step >= raw_step:
            tick_step = step; break

    t_val = 0
    while t_val <= total_time + 0.01:
        tv    = min(t_val, total_time)
        tx    = bar_x2d + tv * scale2d
        label = str(int(tv))
        lw    = len(label) * 4
        # Determine if boundary of a segment (highlight)
        is_boundary = any(abs(s - tv) < 0.01 or abs(e - tv) < 0.01
                          for (_, s, e) in gantt)
        # Tick line from ruler bar up to bar area
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(1.2 if is_boundary else 0.7)
        glColor4f(*(ACCENT2 if is_boundary else GRAY),
                  (0.65 if is_boundary else 0.22) * la)
        glBegin(GL_LINES)
        glVertex2f(tx, RBAR_Y + RH); glVertex2f(tx, vp_y)
        glEnd(); glDisable(GL_BLEND)
        # Number label
        glColor4f(*(ACCENT2 if is_boundary else GRAY), 0.88 * la)
        dts(tx - lw, RNUM_Y, label)
        t_val += tick_step

    end_2d()

# ═══════════════════════════════════════════════════════════
#  PROCESS METRICS TABLE
# ═══════════════════════════════════════════════════════════
_row_rects = []   # (y_min, y_max, pid) for click detection

def draw_proc_table(procs, results, x, y, w, h):
    global _row_rects
    fa=ease_out(anim_t(FADE_DUR))
    begin_2d()
    panel(x,y,w,h,"PROCESS METRICS",fa,GREEN)

    # Sub-info
    glColor4f(*GRAY,fa*0.6)
    dts(x+w-90,y+h-22,f"{len(procs)} processes")

    COLS=[("PID",14,WHITE),("Arrive",56,GRAY),("Burst",110,(0.80,0.80,0.95)),
          ("Prio",164,GRAY),("Finish",210,GREEN),("TAT",266,YELLOW),("Wait",316,ORANGE)]
    HDR_Y=y+h-50
    frect(x+4,HDR_Y-4,w-8,22,(0.08,0.14,0.32),0.65*fa)
    for lbl,dx,col in COLS:
        glColor4f(*col,0.85*fa);dts(x+dx,HDR_Y+4,lbl)

    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(1.0);glColor4f(*ACCENT,0.3*fa)
    glBegin(GL_LINES)
    glVertex2f(x+4,HDR_Y-5);glVertex2f(x+w-4,HDR_Y-5)
    glEnd();glDisable(GL_BLEND)

    ROW_H=28; max_rows=(h-60)//ROW_H
    _row_rects=[]
    for ri,proc in enumerate(procs[:max_rows]):
        pid=proc["pid"]
        res=next((r for r in results if r["pid"]==pid),None)
        ry=HDR_Y-8-(ri+1)*ROW_H
        if ry<y+44:break
        # Hover/selected highlight
        if pid==_selected_pid:
            frect(x+4,ry-2,w-8,ROW_H-1,(0.15,0.25,0.50),0.7*fa)
            orect(x+4,ry-2,w-8,ROW_H-1,ACCENT,1.5,fa)
        elif ri%2==0:
            frect(x+4,ry-2,w-8,ROW_H-1,(0.05,0.05,0.14),0.45*fa)

        col=PROC_COLORS[pid%len(PROC_COLORS)]
        circ(x+COLS[0][1]+5,ry+ROW_H//2-3,6,col,fa)
        glColor4f(*WHITE,fa);dts(x+COLS[0][1]+14,ry+5,f"P{pid}")
        glColor4f(*GRAY,fa)
        dts(x+COLS[1][1],ry+5,str(proc["arrival"]))
        dts(x+COLS[2][1],ry+5,str(proc["burst"]))
        pv=proc.get("priority",0)
        dts(x+COLS[3][1],ry+5,str(pv) if pv>0 else "—")
        if res:
            glColor4f(*GREEN,fa);dts(x+COLS[4][1],ry+5,str(res["completion"]))
            glColor4f(*YELLOW,fa);dts(x+COLS[5][1],ry+5,str(res["turnaround"]))
            glColor4f(*ORANGE,fa);dts(x+COLS[6][1],ry+5,str(res["waiting"]))

        _row_rects.append((ry-2,ry+ROW_H-2,pid))
    end_2d()

# ═══════════════════════════════════════════════════════════
#  AVERAGES 3D
# ═══════════════════════════════════════════════════════════
def draw_averages(results, x, y, w, h):
    fa  = ease_out(anim_t(FADE_DUR + 0.1))
    begin_2d()
    panel(x, y, w, h, "AVERAGES 3D", fa, YELLOW)
    if not results:
        end_2d(); return
    avg_tat = sum(r["turnaround"] for r in results) / len(results)
    avg_wt  = sum(r["waiting"]    for r in results) / len(results)
    end_2d()

    # ── 3D bars viewport ─────────────────────────────────────
    STATS_H = 52   # bottom strip for text stats
    BAR_H   = h - 36 - STATS_H   # remaining for bars (36=title bar)
    vp_x = int(x + 4);      vp_y = int(y + STATS_H)
    vp_w = int(w - 8);      vp_h = int(BAR_H)
    if vp_w < 10 or vp_h < 10:
        begin_2d(); end_2d(); return

    glViewport(vp_x, vp_y, vp_w, vp_h)
    glScissor(vp_x, vp_y, vp_w, vp_h); glEnable(GL_SCISSOR_TEST)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluPerspective(36, vp_w / max(vp_h, 1), 1, 1200)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    bf   = ease_in_out(anim_t(FADE_DUR + 0.5))
    mv   = max(avg_tat, avg_wt, 0.001)
    BW   = max(int(vp_w * 0.30), 18)
    GAP  = max(int(vp_w * 0.12), 10)
    BD   = max(int(BW * 0.60), 10)
    BMH  = max(int(vp_h * 0.68), 10)
    TW   = BW * 2 + GAP
    TX   = (vp_w - TW) // 2
    cx_  = TX + TW // 2

    gluLookAt(cx_, BMH * 0.85, vp_h * 2.0,
              cx_, BMH * 0.15, 0, 0, 1, 0)
    glEnable(GL_DEPTH_TEST); glClear(GL_DEPTH_BUFFER_BIT)
    draw3d.setup_lighting()

    bht = BMH * (avg_tat / mv) * bf
    bhw = BMH * (avg_wt  / mv) * bf
    draw3d.draw_grid_floor(0, -BD, vp_w, BD + 4, 0,
                           max(BW, 16), (0.07, 0.10, 0.32), 0.28)
    draw3d.draw_bar_3d(TX,          0, 0, BW, max(bht, 1.0), BD, YELLOW, fa)
    draw3d.draw_bar_3d(TX + BW + GAP, 0, 0, BW, max(bhw, 1.0), BD, GREEN,  fa)

    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW);  glPopMatrix()
    glDisable(GL_SCISSOR_TEST); glViewport(0, 0, WINDOW_W, WINDOW_H)
    glDisable(GL_DEPTH_TEST);   draw3d.lighting_off()

    # ── Bar labels (TAT / WT) inside the viewport ─────────────
    begin_2d()
    glColor4f(*YELLOW, fa * 0.8)
    dts(vp_x + TX + BW // 2 - 10, vp_y + 6, "TAT")
    glColor4f(*GREEN, fa * 0.8)
    dts(vp_x + TX + BW + GAP + BW // 2 - 6, vp_y + 6, "WT")

    # ── Stat numbers — bottom strip, clean & correct ──────────
    SY = y + STATS_H - 10          # top of stats strip
    # TAT block (left half)
    glColor4f(*GRAY, fa * 0.65); dts(x + 10, SY + 18, "Avg TAT")
    glColor4f(*YELLOW, fa);      dtb(x + 10, SY,  f"{avg_tat:.2f}")
    # WT block (right half)
    half = w // 2
    glColor4f(*GRAY, fa * 0.65); dts(x + half + 6, SY + 18, "Avg WT")
    glColor4f(*GREEN, fa);       dtb(x + half + 6, SY,  f"{avg_wt:.2f}")
    end_2d()

# ═══════════════════════════════════════════════════════════
#  ALGORITHM INFO
# ═══════════════════════════════════════════════════════════
def draw_info_box(x, y, w, h, lines):
    fa=ease_out(anim_t(FADE_DUR+0.2))
    begin_2d()
    panel(x,y,w,h,"ALGORITHM INFO",fa,PURPLE)
    rh=24
    for i,line in enumerate(lines):
        la=ease_out(max(0.0,elapsed()-0.2-i*0.08)/0.28)*fa
        ry=y+h-52-i*rh
        if ry<y+10:break
        if ":" in line:
            k,v=line.split(":",1)
            glColor4f(*ACCENT2,la);dts(x+10,ry,k.strip())
            glColor4f(0.45,0.45,0.60,la*0.7);dts(x+120,ry,":")
            glColor4f(*WHITE,la);dts(x+130,ry,v.strip())
        else:
            glColor4f(*GRAY,la);dts(x+10,ry,line)
    end_2d()

# ═══════════════════════════════════════════════════════════
#  ALGO HEADER
# ═══════════════════════════════════════════════════════════
def draw_algo_header(title, desc, badge_text, content_x):
    fa=ease_out(anim_t(FADE_DUR))
    begin_2d()
    glColor4f(*WHITE,fa);dtb(content_x+10,WINDOW_H-80,title)
    # Badge
    bw=len(badge_text)*8+20; bx=content_x+10+len(title)*10.5+8
    frect(bx,WINDOW_H-92,bw,20,(PURPLE[0]*0.3,PURPLE[1]*0.3,PURPLE[2]*0.4),0.85*fa)
    orect(bx,WINDOW_H-92,bw,20,PURPLE,1.4,fa)
    glColor4f(*PURPLE,fa);dts(bx+8,WINDOW_H-85,badge_text)
    # Underline
    tw=len(title)*10.5
    p=pulse(0.8)
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(2.0);glColor4f(ACCENT[0],ACCENT[1],ACCENT[2]+0.2*p,0.65*fa)
    glBegin(GL_LINES)
    glVertex2f(content_x+10,WINDOW_H-96);glVertex2f(content_x+10+tw,WINDOW_H-96)
    glEnd();glDisable(GL_BLEND)
    glColor4f(*GRAY,fa*0.8);dts(content_x+10,WINDOW_H-110,desc)
    end_2d()

# ═══════════════════════════════════════════════════════════
#  PROCESS DETAIL POPUP
# ═══════════════════════════════════════════════════════════
def draw_popup(procs, results, total_time):
    if _selected_pid<0: return
    proc=next((p for p in procs if p["pid"]==_selected_pid),None)
    res =next((r for r in results if r["pid"]==_selected_pid),None)
    if not proc: return

    fa=ease_out(min(1.0,(elapsed()-_popup_open_time)/0.25)) if hasattr(draw_popup,'_popup_open_time') else 1.0
    PW=242; PH=215
    px=min(_popup_x+20,WINDOW_W-PW-10)
    py=max(_popup_y-PH//2,10)
    py=min(py,WINDOW_H-54-PH-10)

    begin_2d()
    # Shadow
    frect(px+4,py-4,PW,PH,(0,0,0),0.55*fa)
    # Body
    grect(px,py,PW,PH,(0.038,0.038,0.118),(0.058,0.058,0.165),0.96*fa)
    # Glow border
    col=PROC_COLORS[_selected_pid%len(PROC_COLORS)]
    p2=pulse(2.0);orect(px,py,PW,PH,col,2.5+p2*1.5,fa)

    # Title bar
    grect(px+1,py+PH-36,PW-2,35,
          (col[0]*0.18,col[1]*0.18,col[2]*0.30),
          (col[0]*0.28,col[1]*0.28,col[2]*0.45),0.92*fa)
    circ(px+18,py+PH-19,9,col,fa)
    glColor4f(*WHITE,fa);dtb(px+32,py+PH-26,f"Process  P{_selected_pid}")
    # Close hint
    glColor4f(*GRAY,fa*0.55);dts(px+PW-28,py+PH-26,"✕")

    # Separator
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(1.0);glColor4f(*col,0.3*fa)
    glBegin(GL_LINES)
    glVertex2f(px+2,py+PH-37);glVertex2f(px+PW-2,py+PH-37)
    glEnd();glDisable(GL_BLEND)

    # Data rows
    rows=[
        ("Arrival", str(proc.get("arrival","—")), GRAY),
        ("Burst",   str(proc.get("burst","—")),   GRAY),
        ("Priority",str(proc.get("priority","—")) if proc.get("priority",0)>0 else "—",GRAY),
    ]
    if res:
        rows+=[
            ("Finish",  str(res["completion"]), GREEN),
            ("TAT",     str(res["turnaround"]), YELLOW),
            ("Wait",    str(res["waiting"]),    ORANGE),
        ]
    for ri,(k,v,vc) in enumerate(rows):
        ry=py+PH-58-ri*24
        if ri%2==0:frect(px+4,ry-3,PW-8,22,(0.06,0.06,0.18),0.5*fa)
        glColor4f(*ACCENT2,fa*0.75);dts(px+14,ry+4,k)
        glColor4f(*vc,fa);dts(px+100,ry+4,v)

    # CPU share bar
    if total_time>0 and proc.get("burst",0)>0:
        pct=proc["burst"]/total_time
        bar_y=py+14; bar_x=px+10; bar_w=PW-20; bar_h=14
        frect(bar_x,bar_y,bar_w,bar_h,(0.06,0.06,0.18),0.8*fa)
        filled_w=bar_w*pct
        grect(bar_x,bar_y,filled_w,bar_h,col,(min(col[0]*1.4,1),min(col[1]*1.4,1),min(col[2]*1.4,1)),fa)
        orect(bar_x,bar_y,bar_w,bar_h,(0.30,0.30,0.50),1.0,0.5*fa)
        glColor4f(*GRAY,fa*0.65);dts(bar_x,bar_y-12,f"CPU share: {pct*100:.1f}%")

    end_2d()

_popup_open_time=0.0

# ═══════════════════════════════════════════════════════════
#  SCHEDULING ALGORITHMS
# ═══════════════════════════════════════════════════════════
def run_fcfs(procs):
    ps=sorted(procs,key=lambda p:p["arrival"])
    gantt,results,t=[],[],0
    for p in ps:
        s=max(t,p["arrival"]);e=s+p["burst"]
        gantt.append((p["pid"],s,e))
        results.append({"pid":p["pid"],"completion":e,"turnaround":e-p["arrival"],"waiting":s-p["arrival"]})
        t=e
    return gantt,results

def run_rr(procs,quantum):
    remaining={p["pid"]:p["burst"] for p in procs}
    queue,gantt,completion=[],[],{}
    ps=sorted(procs,key=lambda x:x["arrival"])
    t=ps[0]["arrival"];idx=0;arrived=set()
    while True:
        while idx<len(ps) and ps[idx]["arrival"]<=t:
            pid=ps[idx]["pid"]
            if pid not in arrived:queue.append(pid);arrived.add(pid)
            idx+=1
        if not queue:
            if idx<len(ps):t=ps[idx]["arrival"];continue
            break
        pid=queue.pop(0);run=min(quantum,remaining[pid]);s=t;t+=run
        remaining[pid]-=run;gantt.append((pid,s,t))
        while idx<len(ps) and ps[idx]["arrival"]<=t:
            p2=ps[idx]["pid"]
            if p2 not in arrived:queue.append(p2);arrived.add(p2)
            idx+=1
        if remaining[pid]>0:queue.append(pid)
        else:completion[pid]=t
    results=[]
    for p in procs:
        c=completion.get(p["pid"],0)
        results.append({"pid":p["pid"],"completion":c,"turnaround":c-p["arrival"],"waiting":c-p["arrival"]-p["burst"]})
    return gantt,results

def run_sjf(procs):
    rem=sorted(procs,key=lambda x:x["arrival"])
    done,gantt,t=[],[],0
    while rem:
        avail=[p for p in rem if p["arrival"]<=t]
        if not avail:t=rem[0]["arrival"];continue
        p=min(avail,key=lambda x:(x["burst"],x["arrival"]));rem.remove(p)
        s=t;e=t+p["burst"];gantt.append((p["pid"],s,e))
        done.append({"pid":p["pid"],"completion":e,"turnaround":e-p["arrival"],"waiting":s-p["arrival"]})
        t=e
    return gantt,done

def run_srtf(procs):
    import heapq
    n=len(procs);remaining={p["pid"]:p["burst"] for p in procs}
    completion={};ps=sorted(procs,key=lambda x:x["arrival"])
    gantt=[];t=ps[0]["arrival"];ready=[];idx=0
    while len(completion)<n:
        while idx<len(ps) and ps[idx]["arrival"]<=t:
            p=ps[idx];heapq.heappush(ready,(remaining[p["pid"]],p["arrival"],p["pid"]));idx+=1
        if not ready:
            if idx<n:t=ps[idx]["arrival"]
            continue
        rem2,arr,pid=heapq.heappop(ready)
        if rem2!=remaining[pid]:heapq.heappush(ready,(remaining[pid],arr,pid));continue
        if gantt and gantt[-1][0]==pid:gantt[-1]=(pid,gantt[-1][1],t+1)
        else:gantt.append((pid,t,t+1))
        remaining[pid]-=1;t+=1
        if remaining[pid]==0:completion[pid]=t
        else:heapq.heappush(ready,(remaining[pid],arr,pid))
        while idx<len(ps) and ps[idx]["arrival"]<=t:
            p=ps[idx];heapq.heappush(ready,(remaining[p["pid"]],p["arrival"],p["pid"]));idx+=1
    merged=[]
    for seg in gantt:
        if merged and merged[-1][0]==seg[0] and merged[-1][2]==seg[1]:merged[-1]=(seg[0],merged[-1][1],seg[2])
        else:merged.append(list(seg))
    gantt=[tuple(s) for s in merged]
    results=[{"pid":p["pid"],"completion":completion.get(p["pid"],0),
               "turnaround":completion.get(p["pid"],0)-p["arrival"],
               "waiting":completion.get(p["pid"],0)-p["arrival"]-p["burst"]}
              for p in procs]
    return gantt,results

def run_priority(procs):
    rem=sorted(procs,key=lambda x:x["arrival"])
    done,gantt,t=[],[],0
    while rem:
        avail=[p for p in rem if p["arrival"]<=t]
        if not avail:t=rem[0]["arrival"];continue
        p=min(avail,key=lambda x:(x["priority"],x["arrival"]));rem.remove(p)
        s=t;e=t+p["burst"];gantt.append((p["pid"],s,e))
        done.append({"pid":p["pid"],"completion":e,"turnaround":e-p["arrival"],"waiting":s-p["arrival"]})
        t=e
    return gantt,done

def run_priority_pre(procs):
    import heapq
    n=len(procs);remaining={p["pid"]:p["burst"] for p in procs}
    pm={p["pid"]:p["priority"] for p in procs}
    completion={};ps=sorted(procs,key=lambda x:x["arrival"])
    gantt=[];t=ps[0]["arrival"];ready=[];idx=0
    while len(completion)<n:
        while idx<len(ps) and ps[idx]["arrival"]<=t:
            p=ps[idx];heapq.heappush(ready,(p["priority"],p["arrival"],p["pid"]));idx+=1
        if not ready:
            if idx<n:t=ps[idx]["arrival"]
            continue
        pri,arr,pid=heapq.heappop(ready)
        if pri!=pm[pid] or remaining[pid]==0:continue
        if gantt and gantt[-1][0]==pid:gantt[-1]=(pid,gantt[-1][1],t+1)
        else:gantt.append((pid,t,t+1))
        remaining[pid]-=1;t+=1
        if remaining[pid]==0:completion[pid]=t
        else:heapq.heappush(ready,(pm[pid],arr,pid))
        while idx<len(ps) and ps[idx]["arrival"]<=t:
            p=ps[idx];heapq.heappush(ready,(p["priority"],p["arrival"],p["pid"]));idx+=1
    merged=[]
    for seg in gantt:
        if merged and merged[-1][0]==seg[0] and merged[-1][2]==seg[1]:merged[-1]=(seg[0],merged[-1][1],seg[2])
        else:merged.append(list(seg))
    gantt=[tuple(s) for s in merged]
    results=[{"pid":p["pid"],"completion":completion.get(p["pid"],0),
               "turnaround":completion.get(p["pid"],0)-p["arrival"],
               "waiting":completion.get(p["pid"],0)-p["arrival"]-p["burst"]}
              for p in procs]
    return gantt,results

def get_sched_data(algo_idx):
    """Return (gantt, results, procs) for a scheduling algorithm."""
    km={0:"fcfs",1:"rr",2:"sjf",3:"srtf",4:"priority",5:"priority_pre"}
    key=km.get(algo_idx)
    if not key or key not in ALGO_DATA:
        return [],[],[]
    procs=ALGO_DATA[key].get("procs",[])
    if not procs: return [],[],[]
    fn={0:lambda:run_fcfs(procs),
        1:lambda:run_rr(procs,ALGO_DATA["rr"].get("quantum",3)),
        2:lambda:run_sjf(procs),3:lambda:run_srtf(procs),
        4:lambda:run_priority(procs),5:lambda:run_priority_pre(procs)}
    gantt,results=fn[algo_idx]()
    return gantt,results,procs

# ── Unified scheduling renderer ────────────────────────────
SCHED_INFO={
    0:("FCFS","Non-Preemptive","Processes execute in arrival order — no preemption.",
       ["Type       : Non-Preemptive","Order      : Arrival Time (Ascending)",
        "Starvation : No","Convoy Eff.: Yes — long jobs block shorter ones",
        "Complexity : O(n log n)","Best For   : Batch processing systems"]),
    1:("Round Robin","Preemptive","Each process runs for one time quantum, then rotates.",
       ["Type       : Preemptive","Starvation : No",
        "Response   : Very low latency","Overhead   : Context switch per quantum",
        "Complexity : O(n)"]),
    2:("SJF — Non-Preemptive","Non-Preemptive","Picks shortest burst available, runs to completion.",
       ["Type       : Non-Preemptive","Order      : Shortest Burst Time first",
        "Starvation : Yes — long jobs may wait forever",
        "Optimal    : Minimizes average waiting time",
        "Complexity : O(n²)"]),
    3:("SRTF — Preemptive SJF","Preemptive","Preempts when a shorter remaining-burst job arrives.",
       ["Type       : Preemptive","Basis      : Remaining Burst Time",
        "Starvation : Yes — long jobs may starve",
        "Optimal    : Minimizes average waiting time",
        "Complexity : O(n²)"]),
    4:("Priority Scheduling","Non-Preemptive","Highest-priority process runs to full completion.",
       ["Type       : Non-Preemptive","Order      : Priority number (1 = Highest)",
        "Starvation : Yes — low-priority may starve",
        "Fix        : Aging — raise priority over time",
        "Use Case   : Real-time and embedded systems",
        "Complexity : O(n²)"]),
    5:("Priority Scheduling","Preemptive","Preempts on every higher-priority arrival.",
       ["Type       : Preemptive","Order      : Priority number (1 = Highest)",
        "Starvation : Yes — low-priority may starve",
        "Fix        : Aging — raise priority over time",
        "Preemption : On every higher-priority arrival",
        "Complexity : O(n²)"]),
}

def draw_sched(algo_idx, cx, cy, cw, ch, scale=1.0):
    """Render a scheduling visualization into content area (cx,cy,cw,ch)."""
    global _cached_gantt, _cached_results, _cached_total

    info=SCHED_INFO.get(algo_idx)
    if not info: return
    title,badge,desc,lines=info

    gantt,results,procs=get_sched_data(algo_idx)
    if not gantt: return

    total=gantt[-1][2]
    if algo_idx==current_algo:
        _cached_gantt=gantt; _cached_results=results; _cached_total=total

    # Add quantum to RR info line
    if algo_idx==1:
        q=ALGO_DATA.get("rr",{}).get("quantum",3)
        lines=[f"Time Quantum: {q} unit(s)"]+lines[1:]

    # ── LAYOUT ──────────────────────────────────────────────
    # Panels are content-tight (just enough for rows + headers)
    n_procs   = len(procs)
    ROW_H     = 26
    # PANEL_H fixed so panels never grow/shrink
    PANEL_H   = 220
    HEADER_H  = 30          # slim strip above Gantt

    # Layout: panels fixed on top, Gantt fills everything below
    # navbar(54) -> panels(PANEL_H) -> header strip -> GANTT (fills rest)
    GH        = ch - PANEL_H - HEADER_H - 20   # fill all remaining height
    GH        = max(GH, 160)                    # safety floor only
    GY_ACTUAL = cy + PANEL_H + HEADER_H + 6    # Gantt starts right below panels

    GAP     = 6
    TABLE_W = int(cw * 0.46) - GAP
    AVG_W   = int(cw * 0.20) - GAP
    INFO_W  = cw - TABLE_W - AVG_W - GAP * 3 - 8
    TABLE_X = cx + 4
    AVG_X   = TABLE_X + TABLE_W + GAP
    INFO_X  = AVG_X + AVG_W + GAP

    # Header strip sits right below panels, above Gantt
    HDR_Y   = cy + PANEL_H + 4

    global GH_GLOBAL
    GH_GLOBAL = GH
    draw_algo_header(title, desc, badge, cx)
    draw_gantt_3d(gantt, GY_ACTUAL, total, cx, cw)
    draw_proc_table(procs, results, TABLE_X, cy + 4, TABLE_W, PANEL_H)
    draw_averages(results,  AVG_X,  cy + 4, AVG_W,   PANEL_H)
    draw_info_box(INFO_X,   cy + 4, INFO_W, PANEL_H, lines)

    if algo_idx==current_algo:
        draw_popup(procs,results,total)

# ═══════════════════════════════════════════════════════════
#  DEADLOCK
# ═══════════════════════════════════════════════════════════
def bankers_safety(alloc,max_d,total_res,n_res):
    n=len(alloc)
    need=[[max_d[i][j]-alloc[i][j] for j in range(n_res)] for i in range(n)]
    avail=list(total_res)
    for row in alloc:
        for j in range(n_res):avail[j]-=row[j]
    finish=[False]*n;safe=[];work=list(avail);steps=[]
    changed=True
    while changed and len(safe)<n:
        changed=False
        for i in range(n):
            if not finish[i] and all(need[i][j]<=work[j] for j in range(n_res)):
                steps.append({"pid":i,"need":list(need[i]),"avail":list(work),"action":"GRANT"})
                for j in range(n_res):work[j]+=alloc[i][j]
                finish[i]=True;safe.append(i);changed=True
    if len(safe)<n:
        steps.append({"action":"DEADLOCK","unfinished":[i for i in range(n) if not finish[i]]})
        return False,safe,steps,need,avail
    return True,safe,steps,need,avail

def draw_matrix(mat,rnames,pnames,x,y,cw,rh,header,hcol,a=1.0):
    nr=len(mat);nc=len(rnames);pw=nc*cw+62;ph=nr*rh+68
    panel(x,y,pw,ph,header,a,hcol)
    for j,rn in enumerate(rnames):
        glColor4f(*ACCENT2,a);dts(x+44+j*cw,y+ph-38,rn)
    for i,row in enumerate(mat):
        ry=y+ph-68-i*rh
        glColor4f(*YELLOW,a);dts(x+6,ry+7,pnames[i])
        for j,val in enumerate(row):
            cx_=x+44+j*cw
            cc=hcol if val>0 else(0.08,0.08,0.22)
            frect(cx_,ry,cw-4,rh-4,cc,0.88*a)
            orect(cx_,ry,cw-4,rh-4,hcol,0.7,a*0.3)
            glColor4f(*WHITE,a);dts(cx_+9,ry+7,str(val))

def draw_deadlock_screen(cx,cy,cw,ch):
    d=ALGO_DATA.get("deadlock",{})
    alloc=d.get("alloc",[]); max_d=d.get("max_d",[])
    total_res=d.get("total_res",[]); rnames=d.get("res_names",[])
    n_res=d.get("n_res",3); n_proc=len(alloc)
    if not alloc: return
    is_safe,safe_seq,steps,need,avail=bankers_safety(alloc,max_d,total_res,n_res)
    fa=ease_out(anim_t(FADE_DUR)); pnames=[f"P{i}" for i in range(n_proc)]

    GAP  = 8
    cw2  = 38; rh2 = 26
    mw   = lambda nc: nc*cw2 + 58
    mat_h = n_proc*rh2 + 64

    HEADER_H = 52
    MAT_Y    = cy + ch - mat_h - 4
    SR_H     = 108
    SR_Y     = MAT_Y - SR_H - GAP
    RAG_Y    = cy + HEADER_H + 2
    RAG_H    = max(SR_Y - RAG_Y - GAP, 80)

    begin_2d()

    # Header
    glColor4f(*WHITE, fa)
    dtb(cx+10, cy+ch-26, "Deadlock Detection  -  Banker's Algorithm  (3D)")
    p2=pulse(0.7); glColor4f(ACCENT[0]+0.15*p2, ACCENT[1], ACCENT[2], fa*0.75)
    ts  = "  Total: " + "  ".join(f"{rnames[j]}={total_res[j]}" for j in range(n_res))
    av2 = "     Available: " + "  ".join(f"{rnames[j]}={avail[j]}" for j in range(n_res))
    dts(cx+10, cy+ch-44, ts+av2)

    # Matrices row at bottom
    mfa = ease_out(anim_t(FADE_DUR+0.1))
    xc  = cx + 8
    draw_matrix(max_d, rnames, pnames, xc, MAT_Y, cw2, rh2,
                "Max Demand", (0.22,0.22,0.60), mfa)
    xc += mw(n_res) + GAP
    draw_matrix(alloc, rnames, pnames, xc, MAT_Y, cw2, rh2,
                "Allocated",  (0.10,0.44,0.20), mfa)
    xc += mw(n_res) + GAP
    draw_matrix(need,  rnames, pnames, xc, MAT_Y, cw2, rh2,
                "Need",       (0.48,0.20,0.10), mfa)
    xc += mw(n_res) + GAP
    av_pw = 120
    panel(xc, MAT_Y, av_pw, mat_h, "Available", mfa, ACCENT2)
    for j in range(n_res):
        glColor4f(*ACCENT, mfa)
        dts(xc+10, MAT_Y+mat_h-56-j*26, f"{rnames[j]}  :  {avail[j]}")

    # Safety steps (left)
    sg  = [s for s in steps if s["action"]=="GRANT"]
    sr  = int(elapsed()/SEQ_DELAY)+1
    vs  = sg[:sr]
    SW  = cw//2 - GAP
    panel(cx+8, SR_Y, SW, SR_H, "Safety Check - Step Execution", fa, GREEN)
    sx2 = cx+30; sy2 = SR_Y+SR_H-36; row2 = 22
    msr = max(1, (SR_H-46)//row2)
    for si, step in enumerate(vs[:msr]):
        sta = ease_out(min(1.0,(elapsed()-si*SEQ_DELAY)/0.28))
        ssl = (1.0-sta)*(-22)
        pid = step["pid"]; col = PROC_COLORS[pid%len(PROC_COLORS)]
        circ(sx2+7+ssl, sy2-si*row2+7, 6, col, True, sta*fa)
        glColor4f(*WHITE, sta*fa)
        ns  = "["+" ".join(str(v) for v in step["need" ])+"]"
        av3 = "["+" ".join(str(v) for v in step["avail"])+"]"
        dts(sx2+20+ssl, sy2-si*row2+3,
            f"P{pid}  need={ns}  avail={av3}  -> GRANTED")
    ds = next((s for s in steps if s["action"]=="DEADLOCK"), None)
    if ds and sr > len(sg):
        stuck = ["P"+str(p2) for p2 in ds["unfinished"]]
        glColor4f(*RED, fa)
        dtb(sx2, sy2-len(vs[:msr])*row2-4, f"DEADLOCK!  Stuck: {stuck}")

    # Result badge (right)
    rd = len(sg)*SEQ_DELAY
    ra = ease_out(max(0.0, elapsed()-rd)/0.55)*fa
    RX2 = cx + 8 + SW + GAP; RW2 = cw - SW - GAP*3 - 8
    if ra > 0.01:
        bc2  = (0.04,0.24,0.10) if is_safe else (0.24,0.04,0.04)
        bord = GREEN if is_safe else RED
        frect(RX2, SR_Y, RW2, SR_H, bc2, 0.88*ra)
        p3=pulse(2.2); orect(RX2, SR_Y, RW2, SR_H, bord, 2.5+p3*2, ra)
        if is_safe:
            glColor4f(*GREEN, ra);   dtb(RX2+14, SR_Y+SR_H-30, "SAFE STATE  OK")
            seq = "  ->  ".join(f"P{p2}" for p2 in safe_seq)
            glColor4f(*WHITE, ra);   dts(RX2+14, SR_Y+SR_H-52, f"Safe Seq:  {seq}")
            glColor4f(*GRAY, ra*0.8);dts(RX2+14, SR_Y+SR_H-68, "All processes can complete.")
        else:
            glColor4f(*RED, ra);     dtb(RX2+14, SR_Y+SR_H-30, "UNSAFE STATE  X")
            glColor4f(*YELLOW, ra);  dts(RX2+14, SR_Y+SR_H-52, "Deadlock may occur!")
            if ds:
                stuck = ["P"+str(p2) for p2 in ds["unfinished"]]
                glColor4f(*GRAY, ra*0.8)
                dts(RX2+14, SR_Y+SR_H-68, f"Stuck: {stuck}")

    end_2d()

    # RAG fills top
    draw_rag(alloc, need, n_proc, n_res, rnames,
             cx+8, RAG_Y, cw-16, RAG_H, fa)


def draw_rag(alloc,need,n_proc,n_res,rnames,rx,ry,rw,rh,fa):
    begin_2d()
    panel(rx,ry,rw,rh,"Resource Allocation Graph — 3D",fa,ACCENT2)
    end_2d()
    iw=rw-40;ih=rh-88
    ps2=max(55,ih//max(n_proc,1));rs2=max(55,ih//max(n_res,1))
    pth=(n_proc-1)*ps2;rth=(n_res-1)*rs2
    psy=ry+44+ih//2-pth//2;rsy=ry+44+ih//2-rth//2
    ppos=[(rx+55,psy+i*ps2) for i in range(n_proc)]
    rpos=[(rx+rw-55,rsy+j*rs2) for j in range(n_res)]
    vx=int(rx);vy=int(ry);vw=int(rw);vh=int(rh)
    glViewport(vx,vy,vw,vh);glScissor(vx,vy,vw,vh);glEnable(GL_SCISSOR_TEST)
    glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity()
    gluOrtho2D(rx,rx+rw,ry,ry+rh)
    glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity()
    glEnable(GL_DEPTH_TEST);glClear(GL_DEPTH_BUFFER_BIT);draw3d.setup_lighting()
    for i,(px2,py2) in enumerate(ppos):
        col=PROC_COLORS[i%len(PROC_COLORS)];r2=13+3*pulse(1.4+i*0.28)
        draw3d.draw_sphere_3d(px2,py2,0,r2,col,fa*0.92)
    for j,(rx2,ry2) in enumerate(rpos):
        draw3d.draw_cylinder_3d(rx2-10,ry2-18,0,10,36,(0.16,0.16,0.48),fa*0.92)
    glMatrixMode(GL_PROJECTION);glPopMatrix()
    glMatrixMode(GL_MODELVIEW);glPopMatrix()
    glDisable(GL_SCISSOR_TEST);glViewport(0,0,WINDOW_W,WINDOW_H)
    glDisable(GL_DEPTH_TEST);draw3d.lighting_off()
    begin_2d()
    for i in range(n_proc):
        for j in range(n_res):
            if alloc[i][j]>0:arrow2d(rpos[j][0]-14,rpos[j][1],ppos[i][0]+22,ppos[i][1],GREEN,1.8,fa)
    for i in range(n_proc):
        for j in range(n_res):
            if need[i][j]>0:arrow2d(ppos[i][0]+22,ppos[i][1],rpos[j][0]-14,rpos[j][1],YELLOW,1.4,fa)
    for i,(px2,py2) in enumerate(ppos):
        glColor4f(*WHITE,fa);dts(px2-7,py2-5,f"P{i}")
    for j,(rx2,ry2) in enumerate(rpos):
        s2=shimmer();orect(rx2-22,ry2-20,44,40,ACCENT,1.8+s2,fa)
        glColor4f(*WHITE,fa);dts(rx2-7,ry2-5,rnames[j])
    # Legend
    lx=rx+12;ly=ry+32
    arrow2d(lx,ly,lx+28,ly,GREEN,2.0,fa);glColor4f(*GREEN,fa);dts(lx+32,ly-4,"Allocated")
    arrow2d(lx,ly-20,lx+28,ly-20,YELLOW,2.0,fa);glColor4f(*YELLOW,fa);dts(lx+32,ly-24,"Request")
    end_2d()

# ═══════════════════════════════════════════════════════════
#  COMPARE MODE
# ═══════════════════════════════════════════════════════════
def draw_compare():
    """Split-screen: current algo left, next algo right."""
    algo_l=current_algo; algo_r=(current_algo+1)%6  # skip deadlock
    hw=WINDOW_W//2
    cx_l=0; cx_r=hw
    cy=0; ch=WINDOW_H-54-120  # leave room for headers

    # Divider
    begin_2d()
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(1.2);glColor4f(*ACCENT,0.4)
    glBegin(GL_LINES)
    glVertex2f(hw,0);glVertex2f(hw,WINDOW_H-54)
    glEnd();glDisable(GL_BLEND)

    # Labels
    glColor4f(*ACCENT2,0.7);dtb(cx_l+10,WINDOW_H-72,ALGO_NAMES[algo_l])
    glColor4f(*ACCENT2,0.7);dtb(cx_r+10,WINDOW_H-72,ALGO_NAMES[algo_r])
    end_2d()

    draw_sched(algo_l, cx_l, cy, hw-6, ch)
    draw_sched(algo_r, cx_r, cy, hw-6, ch)

# ═══════════════════════════════════════════════════════════
#  DISPLAY
# ═══════════════════════════════════════════════════════════
def display():
    glClearColor(*BG,1.0)
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glViewport(0,0,WINDOW_W,WINDOW_H)

    draw_background()
    draw_sidebar()

    begin_2d()
    draw_navbar()
    end_2d()

    cx=8; cy=0; cw=WINDOW_W-16; ch=WINDOW_H-54

    if _compare_mode and current_algo<6:
        draw_compare()
    elif current_algo==6:
        draw_deadlock_screen(cx,cy,cw,WINDOW_H-54-20)
    elif 0<=current_algo<=5:
        draw_sched(current_algo, cx, cy, cw, WINDOW_H-54-20)

    glutSwapBuffers()

def timer_callback(val):
    glutPostRedisplay()
    glutTimerFunc(16,timer_callback,0)

# ═══════════════════════════════════════════════════════════
#  INPUT HANDLERS
# ═══════════════════════════════════════════════════════════
def keyboard(key,x,y):
    global current_algo,_paused,_manual_time,_speed_idx,_compare_mode
    global _selected_pid,_anim_start
    k=key.decode("utf-8") if isinstance(key,bytes) else key
    if k in("q","Q","\x1b"):
        if _selected_pid>=0:_selected_pid=-1
        else:glutLeaveMainLoop()
    elif k in("n","N"):
        if _on_new_run_cb:_on_new_run_cb()
    elif k=="\t":
        current_algo=(current_algo+1)%7; _anim_start=time.time(); _selected_pid=-1
    elif k in("c","C"):
        _compare_mode=not _compare_mode; _selected_pid=-1
    elif k==" ":
        if not _paused:
            _manual_time=gantt_revealed()
        _paused=not _paused
    elif k=="+":
        _speed_idx=min(len(_speed_levels)-1,_speed_idx+1)
    elif k=="-":
        _speed_idx=max(0,_speed_idx-1)
    elif k in[str(i) for i in range(1,8)]:
        current_algo=int(k)-1; _anim_start=time.time(); _selected_pid=-1; _paused=False
    glutPostRedisplay()

def special_key(key,x,y):
    global _manual_time,_paused
    if _paused:
        if key==GLUT_KEY_RIGHT:_manual_time=min(_manual_time+1,_cached_total)
        elif key==GLUT_KEY_LEFT:_manual_time=max(0.0,_manual_time-1)
    glutPostRedisplay()

def mouse(button,state,mx,my):
    global _selected_pid,_popup_x,_popup_y,_popup_open_time
    global _drag_gantt,_drag_gx,_drag_gy,_drag_rot_start_y,_drag_rot_start_x
    global current_algo,_anim_start,_mouse_x,_mouse_y

    _mouse_x=mx; _mouse_y=my

    if button==GLUT_LEFT_BUTTON and state==GLUT_DOWN:
        # No sidebar (removed) — skip

        # Gantt drag start
        vx,vy,vw,vh=_gantt_vp
        ogl_y=WINDOW_H-my
        if vx<=mx<=vx+vw and vy<=ogl_y<=vy+vh:
            _drag_gantt=True; _drag_gx=mx; _drag_gy=my
            _drag_rot_start_y=_gantt_rot_y; _drag_rot_start_x=_gantt_rot_x
            return

        # Process table row click
        ogl_y2=WINDOW_H-my
        for(y_min,y_max,pid) in _row_rects:
            if y_min<=ogl_y2<=y_max:
                if _selected_pid==pid:_selected_pid=-1
                else:
                    _selected_pid=pid; _popup_x=mx; _popup_y=my
                    _popup_open_time=time.time()
                glutPostRedisplay(); return

        # Click outside popup — deselect
        _selected_pid=-1

    elif button==GLUT_LEFT_BUTTON and state==GLUT_UP:
        _drag_gantt=False

    glutPostRedisplay()

def motion(mx,my):
    """Mouse drag handler."""
    global _gantt_rot_y,_gantt_rot_x,_mouse_x,_mouse_y
    _mouse_x=mx; _mouse_y=my
    if _drag_gantt:
        dx=mx-_drag_gx; dy=my-_drag_gy
        _gantt_rot_y=_drag_rot_start_y+dx*1.1
        _gantt_rot_x=max(-8.0,min(45.0,_drag_rot_start_x+dy*0.70))
    glutPostRedisplay()

def passive_motion(mx,my):
    global _mouse_x,_mouse_y
    _mouse_x=mx; _mouse_y=my
    glutPostRedisplay()

def reshape(w,h):
    global WINDOW_W,WINDOW_H
    WINDOW_W,WINDOW_H=w,h; glViewport(0,0,w,h)

# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════
_gl_initialized=False

def load_run(data, on_new_run=None):
    global current_algo,ALGO_DATA,PROC_COLORS,_anim_start,_on_new_run_cb
    global _paused,_manual_time,_selected_pid,_compare_mode
    _on_new_run_cb=on_new_run; current_algo=data["algo_idx"]
    ALGO_DATA=data; _anim_start=time.time()
    _paused=False; _manual_time=0.0; _selected_pid=-1; _compare_mode=False
    if "gantt_colors" in data:PROC_COLORS=list(data["gantt_colors"])

def _load_logo_texture():
    """Load the Innovation University logo as an OpenGL texture (RGBA)."""
    global _logo_tex, _logo_w, _logo_h
    if not _PIL_OK or not os.path.exists(_LOGO_PATH):
        return
    try:
        img = _PILImage.open(_LOGO_PATH).convert("RGBA")
        # Scale to a sensible height for the navbar (42px tall)
        target_h = 42
        w, h = img.size
        target_w = int(w * target_h / h)
        img = img.resize((target_w, target_h), _PILImage.LANCZOS)
        _logo_w, _logo_h = img.size
        img_data = img.tobytes("raw", "RGBA", 0, -1)
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, _logo_w, _logo_h,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        _logo_tex = tex
    except Exception:
        pass  # silently skip on any error

def _draw_logo_texture():
    """Render the logo texture at the top-right corner of the navbar."""
    if _logo_tex is None:
        return
    margin = 10
    x = WINDOW_W - _logo_w - margin
    y = WINDOW_H - _logo_h - (54 - _logo_h) // 2   # vertically centred in 54px bar
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, _logo_tex)
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1, 1, 1, 1)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x,          y)
    glTexCoord2f(1, 0); glVertex2f(x + _logo_w, y)
    glTexCoord2f(1, 1); glVertex2f(x + _logo_w, y + _logo_h)
    glTexCoord2f(0, 1); glVertex2f(x,           y + _logo_h)
    glEnd()
    glDisable(GL_TEXTURE_2D)

def init_window():
    global _gl_initialized
    if _gl_initialized:return
    _gl_initialized=True
    glutInit(); glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGBA|GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W,WINDOW_H); glutInitWindowPosition(30,20)
    glutCreateWindow(b"OS Scheduler 3D + Deadlock Visualizer")
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_DEPTH_TEST)
    _load_logo_texture()
    glutDisplayFunc(display); glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard); glutSpecialFunc(special_key)
    glutMouseFunc(mouse); glutMotionFunc(motion)
    glutPassiveMotionFunc(passive_motion)
    glutTimerFunc(16,timer_callback,0)

def run(): glutMainLoop()
