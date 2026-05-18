"""
gui_input.py  —  OS Scheduler 3D  ·  Dark Themed Setup Window
Matches the screenshot style: algorithm grid buttons, process rows, keyboard hint bar.
"""
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import os
try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

_LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "innovation-university-Logo.png")

DEFAULT_COLORS = [
    "#2B7FFF","#22DD66","#FF8C1A","#AA44FF",
    "#FF3355","#00D4D4","#FF66CC","#66FF66",
]

def hex_to_rgb(h):
    h=h.lstrip("#")
    return tuple(int(h[i:i+2],16)/255.0 for i in(0,2,4))

def luma(h):
    r,g,b=hex_to_rgb(h)
    return 0.299*r+0.587*g+0.114*b

class InputGUI:
    ALGO_NAMES=["1. FCFS","2. Round Robin","3. SJF","4. SRTF",
                "5. Priority (Non-Pre)","6. Priority (Pre)","7. Deadlock (Banker's)"]
    ALGO_KEYS =["fcfs","rr","sjf","srtf","priority","priority_pre","deadlock"]

    def __init__(self):
        self.result=None
        self.gantt_colors=list(DEFAULT_COLORS)
        self.selected_algo=0

        root=tk.Tk()
        self.root=root
        root.title("OS Scheduler 3D + Deadlock Visualizer")
        root.configure(bg="#060614")
        root.geometry("1060x760")
        root.resizable(True,True)
        root.minsize(820,680)

        # ── Fonts ─────────────────────────────────────────────
        F_TITLE =("Courier New",15,"bold")
        F_SUB   =("Courier New",9)
        F_BOLD  =("Courier New",10,"bold")
        F_NORM  =("Courier New",10)
        F_SMALL =("Courier New",9)

        # ── Root grid ─────────────────────────────────────────
        root.grid_columnconfigure(0,weight=1)
        root.grid_rowconfigure(3,weight=1)

        # ══ Title bar ══════════════════════════════════════════
        tb=tk.Frame(root,bg="#0B0B24",pady=14,padx=18)
        tb.grid(row=0,column=0,sticky="ew")
        # Logo icon
        icon=tk.Label(tb,text=" OS ",bg="#2B7FFF",fg="#FFFFFF",
                      font=("Courier New",12,"bold"),padx=6,pady=3,bd=0)
        icon.pack(side="left",padx=(0,12))
        # Title
        tk.Label(tb,text="OS SCHEDULER ",bg="#0B0B24",fg="#FFFFFF",
                 font=("Courier New",15,"bold")).pack(side="left")
        tk.Label(tb,text="3D",bg="#0B0B24",fg="#2B7FFF",
                 font=("Courier New",15,"bold")).pack(side="left")
        tk.Label(tb,text="   3D · Multi-Run · Interactive Visualization",
                 bg="#0B0B24",fg="#445577",font=F_SUB).pack(side="left",padx=(4,0))
        # ── Innovation University logo (top-right, always visible) ──
        self._iu_logo_img = None  # keep reference to avoid GC
        if _PIL_OK and os.path.exists(_LOGO_PATH):
            try:
                pil_img = Image.open(_LOGO_PATH)
                # Resize to fit neatly in the title bar (~54px tall)
                target_h = 54
                w, h = pil_img.size
                target_w = int(w * target_h / h)
                pil_img = pil_img.resize((target_w, target_h), Image.LANCZOS)
                self._iu_logo_img = ImageTk.PhotoImage(pil_img)
                logo_lbl = tk.Label(tb, image=self._iu_logo_img,
                                    bg="#0B0B24", bd=0, padx=0, pady=0)
                logo_lbl.pack(side="right", padx=(0, 4))
            except Exception:
                pass  # silently skip if image fails
        if self._iu_logo_img is None:
            # Fallback text badge if PIL not available or image missing
            tk.Label(tb, text="Innovation\nUniversity",
                     bg="#0B0B24", fg="#7744CC",
                     font=("Courier New", 9, "bold")).pack(side="right", padx=(0, 8))

        # ══ Algorithm grid ═════════════════════════════════════
        af=tk.Frame(root,bg="#060614",padx=16,pady=6)
        af.grid(row=1,column=0,sticky="ew")
        tk.Label(af,text="ALGORITHM",bg="#060614",fg="#2B7FFF",font=F_BOLD).pack(anchor="w",pady=(0,6))
        grid_f=tk.Frame(af,bg="#060614")
        grid_f.pack(fill="x")
        # 4 in first row, 3 in second
        self.algo_btns=[]
        for i,name in enumerate(self.ALGO_NAMES):
            row=i//4; col=i%4
            btn=tk.Button(grid_f,text=name,font=("Courier New",10,"bold"),
                          relief="flat",bd=0,padx=12,pady=7,cursor="hand2",
                          command=lambda idx=i:self._select_algo(idx))
            btn.grid(row=row,column=col,padx=4,pady=3,sticky="ew")
            grid_f.grid_columnconfigure(col,weight=1)
            self.algo_btns.append(btn)
        # NOTE: _select_algo(0) called at end of __init__ after all widgets exist

        # ══ Tabs ═══════════════════════════════════════════════
        style=ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TNotebook",background="#060614",borderwidth=0,tabmargins=[0,0,0,0])
        style.configure("Dark.TNotebook.Tab",background="#0E0E2A",foreground="#556688",
                        font=("Courier New",10,"bold"),padding=[14,6],borderwidth=0)
        style.map("Dark.TNotebook.Tab",
                  background=[("selected","#2B7FFF"),("active","#1A1A3E")],
                  foreground=[("selected","#FFFFFF"),("active","#AACCFF")])
        style.configure("TFrame",background="#060614")
        style.configure("TLabel",background="#060614",foreground="#DDEEFF",font=F_NORM)
        style.configure("TSpinbox",fieldbackground="#0E0E28",foreground="#DDEEFF",
                        insertcolor="#DDEEFF",font=F_NORM,arrowcolor="#2B7FFF")
        style.configure("TEntry",fieldbackground="#0E0E28",foreground="#DDEEFF",insertcolor="#2B7FFF")

        # ── Content area: notebook for sched algos OR deadlock frame ──
        # Container that holds both, only one visible at a time
        self.content_area=tk.Frame(root,bg="#060614")
        self.content_area.grid(row=3,column=0,sticky="nsew",padx=12,pady=0)
        self.content_area.grid_columnconfigure(0,weight=1)
        self.content_area.grid_rowconfigure(0,weight=1)

        # Notebook with 2 tabs (Process Input + Gantt Colors) — NO Deadlock
        nb=ttk.Notebook(self.content_area,style="Dark.TNotebook")
        nb.grid(row=0,column=0,sticky="nsew")
        self.nb=nb

        self.proc_tab=tk.Frame(nb,bg="#060614")
        self.col_tab =tk.Frame(nb,bg="#060614")

        nb.add(self.proc_tab,text="  ⚙ Process Input  ")
        nb.add(self.col_tab, text="  🎨 Gantt Colors  ")

        # Deadlock frame — separate, hidden by default
        self.dl_tab=tk.Frame(self.content_area,bg="#060614")
        self.dl_tab.grid(row=0,column=0,sticky="nsew")
        self.dl_tab.grid_remove()   # hidden until algo 6 selected

        self._build_proc_tab()
        self._build_dl_tab()
        self._build_col_tab()

        # ══ Launch bar ════════════════════════════════════════
        launch_f=tk.Frame(root,bg="#060614",pady=10,padx=16)
        launch_f.grid(row=4,column=0,sticky="ew")

        # Launch button — full width green
        launch_btn=tk.Button(launch_f,text="  🚀  Launch Visualizer  ",
                             bg="#1A6A20",fg="#AAFFBB",
                             font=("Courier New",13,"bold"),relief="flat",
                             bd=0,padx=20,pady=10,cursor="hand2",
                             activebackground="#22882A",activeforeground="#DFFFDF",
                             command=self._launch)
        launch_btn.pack(fill="x",pady=(0,8))

        # Keyboard hints bar
        hints_f=tk.Frame(launch_f,bg="#0A0A1E",pady=6,padx=10)
        hints_f.pack(fill="x")
        hints=[("N","New Run"),("Q","Quit/Close"),("TAB","Switch Algo"),
               ("C","Compare Mode"),("SPACE","Pause/Play"),("+ / -","Speed"),
               ("← →","Step (paused)"),("1-7","Jump to Algo"),("ESC","Dismiss popup")]
        for i,(key,desc) in enumerate(hints):
            col=i%3; row_=i//3
            cell=tk.Frame(hints_f,bg="#0A0A1E")
            cell.grid(row=row_,column=col,sticky="w",padx=12,pady=2)
            hints_f.grid_columnconfigure(col,weight=1)
            tk.Label(cell,text=key,bg="#1A1A40",fg="#2B7FFF",
                     font=("Courier New",9,"bold"),padx=5,pady=1,bd=0).pack(side="left")
            tk.Label(cell,text=" "+desc,bg="#0A0A1E",fg="#556677",
                     font=("Courier New",9)).pack(side="left")

        root.bind("<Return>",lambda e:self._launch())
        # All widgets built — now safe to set initial algo state
        self._select_algo(0)

    # ── Algorithm selector ────────────────────────────────
    def _select_algo(self,idx):
        self.selected_algo=idx
        for i,btn in enumerate(self.algo_btns):
            if i==idx:
                btn.configure(bg="#2B7FFF",fg="#FFFFFF",relief="solid",bd=1,
                              highlightbackground="#5599FF",highlightthickness=1)
            else:
                btn.configure(bg="#0E0E2A",fg="#778899",relief="flat",bd=0)
        # Show/hide quantum (guard: proc tab may not be built yet)
        if hasattr(self,"quantum_row") and hasattr(self,"nproc_row"):
            is_rr=(idx==1)
            if is_rr:
                self.quantum_row.pack(fill="x",pady=4,after=self.nproc_row)
            else:
                try: self.quantum_row.pack_forget()
                except: pass
        # Show/hide deadlock frame vs notebook (guard: may not exist yet)
        if hasattr(self,"nb") and hasattr(self,"dl_tab") and hasattr(self,"content_area"):
            if idx==6:
                self.nb.grid_remove()        # hide notebook
                self.dl_tab.grid()           # show deadlock frame
            else:
                self.dl_tab.grid_remove()    # hide deadlock frame
                self.nb.grid()               # show notebook

    # ── Process Input Tab ─────────────────────────────────
    def _build_proc_tab(self):
        f=self.proc_tab
        pad_f=tk.Frame(f,bg="#060614",padx=14,pady=10)
        pad_f.pack(fill="both",expand=True)

        # Number of processes row
        self.nproc_row=tk.Frame(pad_f,bg="#060614")
        self.nproc_row.pack(fill="x",pady=(0,4))
        tk.Label(self.nproc_row,text="Number of Processes",bg="#060614",
                 fg="#AABBCC",font=("Courier New",10)).pack(side="left")
        self.n_proc_var=tk.IntVar(value=4)
        btn_f=tk.Frame(self.nproc_row,bg="#060614")
        btn_f.pack(side="left",padx=14)
        tk.Button(btn_f,text=" - ",bg="#1A1A3A",fg="#AABBCC",font=("Courier New",11,"bold"),
                  relief="flat",cursor="hand2",
                  command=lambda:self._change_n(-1)).pack(side="left",padx=2)
        self.n_lbl=tk.Label(btn_f,text="4",bg="#0E0E28",fg="#FFFFFF",
                             font=("Courier New",12,"bold"),width=4,pady=2)
        self.n_lbl.pack(side="left",padx=2)
        tk.Button(btn_f,text=" + ",bg="#1A1A3A",fg="#AABBCC",font=("Courier New",11,"bold"),
                  relief="flat",cursor="hand2",
                  command=lambda:self._change_n(1)).pack(side="left",padx=2)

        # Quantum row (hidden unless RR)
        self.quantum_row=tk.Frame(pad_f,bg="#060614")
        tk.Label(self.quantum_row,text="Time Quantum",bg="#060614",
                 fg="#AABBCC",font=("Courier New",10)).pack(side="left")
        self.quantum_var=tk.IntVar(value=3)
        tk.Frame(self.quantum_row,bg="#060614",width=10).pack(side="left")
        qbf=tk.Frame(self.quantum_row,bg="#060614")
        qbf.pack(side="left",padx=14)
        tk.Button(qbf,text=" - ",bg="#1A1A3A",fg="#AABBCC",font=("Courier New",11,"bold"),
                  relief="flat",cursor="hand2",
                  command=lambda:self.quantum_var.set(max(1,self.quantum_var.get()-1))).pack(side="left",padx=2)
        self.q_lbl=tk.Label(qbf,text="3",bg="#0E0E28",fg="#FFFFFF",
                             font=("Courier New",12,"bold"),width=4,pady=2)
        self.q_lbl.pack(side="left",padx=2)
        self.quantum_var.trace_add("write",lambda *a:self.q_lbl.configure(text=str(self.quantum_var.get())))
        tk.Button(qbf,text=" + ",bg="#1A1A3A",fg="#AABBCC",font=("Courier New",11,"bold"),
                  relief="flat",cursor="hand2",
                  command=lambda:self.quantum_var.set(min(20,self.quantum_var.get()+1))).pack(side="left",padx=2)

        # Column headers
        hdr=tk.Frame(pad_f,bg="#0A0A20",pady=5,padx=6)
        hdr.pack(fill="x",pady=(8,0))
        for i,(lbl,w) in enumerate([("PID",8),("Arrival",18),("Burst",18),("Priority",18),("Color",6)]):
            tk.Label(hdr,text=lbl,bg="#0A0A20",fg="#2B7FFF",
                     font=("Courier New",10,"bold"),width=w,anchor="w").grid(row=0,column=i,padx=6)

        # Scrollable rows
        scroll_f=tk.Frame(pad_f,bg="#060614")
        scroll_f.pack(fill="both",expand=True,pady=4)
        canvas=tk.Canvas(scroll_f,bg="#060614",highlightthickness=0)
        sb=ttk.Scrollbar(scroll_f,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left",fill="both",expand=True)
        sb.pack(side="right",fill="y")
        self.proc_inner=tk.Frame(canvas,bg="#060614")
        canvas.create_window((0,0),window=self.proc_inner,anchor="nw")
        self.proc_inner.bind("<Configure>",
            lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        self.proc_rows=[]
        self._rebuild_proc_rows()

    def _change_n(self,delta):
        v=max(2,min(8,self.n_proc_var.get()+delta))
        self.n_proc_var.set(v);self.n_lbl.configure(text=str(v))
        self._rebuild_proc_rows()

    def _rebuild_proc_rows(self):
        n=self.n_proc_var.get()
        old=[{"arrival":r["arrival"].get(),"burst":r["burst"].get(),
              "priority":r["priority"].get(),"color":r["color_hex"]}
             for r in self.proc_rows]
        for w in self.proc_inner.winfo_children():w.destroy()
        self.proc_rows=[]
        for i in range(n):
            prev=old[i] if i<len(old) else{}
            rf=tk.Frame(self.proc_inner,bg="#0B0B20",pady=5,padx=6)
            rf.pack(fill="x",pady=2,padx=2)
            col=self.gantt_colors[i%len(self.gantt_colors)]
            fg2="#000000" if luma(col)>0.5 else "#FFFFFF"
            pid_lbl=tk.Label(rf,text=f"P{i}",bg=col,fg=fg2,
                             font=("Courier New",10,"bold"),width=4,pady=3,relief="flat")
            pid_lbl.grid(row=0,column=0,padx=(2,8))
            av=tk.StringVar(value=prev.get("arrival","0"))
            bv=tk.StringVar(value=prev.get("burst",str(i*2+2)))
            pv=tk.StringVar(value=prev.get("priority",str(i+1)))
            for ci,(var,w_) in enumerate([(av,10),(bv,10),(pv,10)]):
                e=tk.Entry(rf,textvariable=var,width=w_,bg="#0E0E28",fg="#DDEEFF",
                           insertbackground="#2B7FFF",relief="solid",bd=1,
                           font=("Courier New",10),highlightthickness=1,
                           highlightcolor="#2B7FFF",highlightbackground="#1A1A3A")
                e.grid(row=0,column=ci+1,padx=8)
            hex_c=prev.get("color",col)
            cb=tk.Button(rf,bg=hex_c,width=4,height=1,relief="solid",bd=1,cursor="hand2",
                         command=lambda idx=i:self._pick_color(idx))
            cb.grid(row=0,column=4,padx=6)
            self.proc_rows.append({"arrival":av,"burst":bv,"priority":pv,
                                   "color_btn":cb,"color_hex":hex_c,"pid_lbl":pid_lbl})

    def _pick_color(self,idx):
        cur=self.proc_rows[idx]["color_hex"]
        res=colorchooser.askcolor(color=cur,title=f"Color for P{idx}")
        if res and res[1]:
            h=res[1];self.proc_rows[idx]["color_hex"]=h
            self.proc_rows[idx]["color_btn"].configure(bg=h)
            fg2="#000000" if luma(h)>0.5 else "#FFFFFF"
            self.proc_rows[idx]["pid_lbl"].configure(bg=h,fg=fg2)
            self.gantt_colors[idx%len(self.gantt_colors)]=h
            self._sync_col_tab()

    # ── Deadlock Tab ──────────────────────────────────────
    def _build_dl_tab(self):
        f=self.dl_tab
        pad=tk.Frame(f,bg="#060614",padx=14,pady=10)
        pad.pack(fill="both",expand=True)
        # Controls
        ctrl=tk.Frame(pad,bg="#060614")
        ctrl.pack(fill="x",pady=(0,8))
        tk.Label(ctrl,text="Resource Types (1-5):",bg="#060614",fg="#AABBCC",
                 font=("Courier New",10)).pack(side="left")
        self.n_res_var=tk.IntVar(value=3)
        tk.Spinbox(ctrl,from_=1,to=5,width=4,textvariable=self.n_res_var,
                   bg="#0E0E28",fg="#DDEEFF",insertbackground="#2B7FFF",
                   font=("Courier New",10),relief="flat",
                   command=self._rebuild_dl).pack(side="left",padx=8)
        tk.Label(ctrl,text="  Processes (2-6):",bg="#060614",fg="#AABBCC",
                 font=("Courier New",10)).pack(side="left")
        self.n_dl_proc_var=tk.IntVar(value=4)
        tk.Spinbox(ctrl,from_=2,to=6,width=4,textvariable=self.n_dl_proc_var,
                   bg="#0E0E28",fg="#DDEEFF",insertbackground="#2B7FFF",
                   font=("Courier New",10),relief="flat",
                   command=self._rebuild_dl).pack(side="left",padx=8)
        tk.Button(ctrl,text="↺ Rebuild",bg="#1A1A3A",fg="#AABBCC",
                  font=("Courier New",9),relief="flat",padx=8,cursor="hand2",
                  command=self._rebuild_dl).pack(side="left",padx=12)

        # Total row
        self.total_f=tk.Frame(pad,bg="#0A0A20",padx=6,pady=5)
        self.total_f.pack(fill="x",pady=4)

        # Matrix notebook
        dl_nb=ttk.Notebook(pad,style="Dark.TNotebook")
        dl_nb.pack(fill="both",expand=True,pady=4)
        self.max_tab_f  =tk.Frame(dl_nb,bg="#060614",padx=10,pady=8)
        self.alloc_tab_f=tk.Frame(dl_nb,bg="#060614",padx=10,pady=8)
        dl_nb.add(self.max_tab_f,  text="  Max Demand  ")
        dl_nb.add(self.alloc_tab_f,text="  Allocated  ")
        self.total_vars=[];self.max_vars=[];self.alloc_vars=[]
        self._rebuild_dl()

    def _rebuild_dl(self):
        try:n_res=int(self.n_res_var.get());n_proc=int(self.n_dl_proc_var.get())
        except:n_res,n_proc=3,4
        n_res=max(1,min(5,n_res));n_proc=max(2,min(6,n_proc))
        rnames=[chr(ord("A")+j) for j in range(n_res)]
        ot=[v.get() for v in self.total_vars] if self.total_vars else[]
        om=[[v.get() for v in row] for row in self.max_vars]   if self.max_vars  else[]
        oa=[[v.get() for v in row] for row in self.alloc_vars] if self.alloc_vars else[]
        def so(m,r,c,d="0"):
            try:return m[r][c]
            except:return d
        for w in self.total_f.winfo_children():w.destroy()
        tk.Label(self.total_f,text="Total Instances →",bg="#0A0A20",fg="#2B7FFF",
                 font=("Courier New",10,"bold")).grid(row=0,column=0,padx=8)
        self.total_vars=[]
        for j in range(n_res):
            tk.Label(self.total_f,text=rnames[j],bg="#0A0A20",fg="#00D4D4",
                     font=("Courier New",10,"bold"),width=4).grid(row=0,column=j*2+1,padx=2)
            v=tk.StringVar(value=so(ot,j,0,"10") if j<len(ot) else"10")
            self.total_vars.append(v)
            tk.Entry(self.total_f,textvariable=v,width=5,bg="#0E0E28",fg="#DDEEFF",
                     insertbackground="#2B7FFF",relief="solid",bd=1,
                     font=("Courier New",10)).grid(row=0,column=j*2+2,padx=2)
        def build_mat(parent,old):
            for w in parent.winfo_children():w.destroy()
            for j,rn in enumerate(rnames):
                tk.Label(parent,text=rn,bg="#060614",fg="#00D4D4",
                         font=("Courier New",10,"bold"),width=6).grid(row=0,column=j+1,padx=2,pady=2)
            rv=[]
            for i in range(n_proc):
                tk.Label(parent,text=f"P{i}",bg="#060614",fg="#FFDD33",
                         font=("Courier New",10,"bold"),width=4).grid(row=i+1,column=0,padx=6)
                row_v=[]
                for j in range(n_res):
                    v=tk.StringVar(value=so(old,i,j,"0"))
                    tk.Entry(parent,textvariable=v,width=6,bg="#0E0E28",fg="#DDEEFF",
                             insertbackground="#2B7FFF",relief="solid",bd=1,
                             font=("Courier New",10)).grid(row=i+1,column=j+1,padx=2,pady=2)
                    row_v.append(v)
                rv.append(row_v)
            return rv
        self.max_vars  =build_mat(self.max_tab_f,  om)
        self.alloc_vars=build_mat(self.alloc_tab_f, oa)

    # ── Colors Tab ────────────────────────────────────────
    def _build_col_tab(self):
        f=self.col_tab
        pad=tk.Frame(f,bg="#060614",padx=14,pady=10)
        pad.pack(fill="both",expand=True)
        tk.Label(pad,text="Customize process colors for the Gantt chart:",
                 bg="#060614",fg="#556677",font=("Courier New",9)).pack(anchor="w",pady=(0,10))
        grid=tk.Frame(pad,bg="#060614")
        grid.pack(anchor="w")
        self.color_swatches=[]
        for i in range(8):
            col=self.gantt_colors[i]
            slot=tk.Frame(grid,bg="#0B0B20",padx=10,pady=8)
            slot.grid(row=i//4,column=i%4,padx=8,pady=6)
            fg2="#000000" if luma(col)>0.5 else "#FFFFFF"
            lbl=tk.Label(slot,text=f"P{i}",font=("Courier New",12,"bold"),
                         bg=col,fg=fg2,width=5,height=2,relief="solid",bd=1)
            lbl.pack()
            btn=tk.Button(slot,text="Change",font=("Courier New",8),bg="#1A1A3A",fg="#AAAACC",
                          relief="flat",padx=4,cursor="hand2",
                          command=lambda idx=i:self._pick_gantt_color(idx))
            btn.pack(pady=2)
            hl=tk.Label(slot,text=col,font=("Courier New",8),bg="#060614",fg="#445566")
            hl.pack()
            self.color_swatches.append((lbl,btn,hl))
        tk.Button(pad,text="↺  Reset to Defaults",bg="#141430",fg="#7788AA",
                  font=("Courier New",9),relief="flat",padx=10,pady=4,cursor="hand2",
                  command=self._reset_colors).pack(anchor="w",pady=10)

    def _pick_gantt_color(self,idx):
        res=colorchooser.askcolor(color=self.gantt_colors[idx],title=f"Gantt color P{idx}")
        if res and res[1]:
            self.gantt_colors[idx]=res[1];self._sync_col_tab()
            if idx<len(self.proc_rows):
                h=res[1];self.proc_rows[idx]["color_hex"]=h
                self.proc_rows[idx]["color_btn"].configure(bg=h)
                fg2="#000000" if luma(h)>0.5 else "#FFFFFF"
                self.proc_rows[idx]["pid_lbl"].configure(bg=h,fg=fg2)

    def _sync_col_tab(self):
        for i,(lbl,btn,hl) in enumerate(self.color_swatches):
            c=self.gantt_colors[i];lbl.configure(bg=c);hl.configure(text=c)
            lbl.configure(fg="#000000" if luma(c)>0.5 else "#FFFFFF")

    def _reset_colors(self):
        self.gantt_colors=list(DEFAULT_COLORS)
        self._sync_col_tab();self._rebuild_proc_rows()

    # ── Validation & Launch ───────────────────────────────
    def _gi(self,sv,label,mn=0,mx=None):
        try:v=int(sv.get())
        except:raise ValueError(f"'{label}' must be an integer.")
        if v<mn:raise ValueError(f"'{label}' must be ≥ {mn}.")
        if mx is not None and v>mx:raise ValueError(f"'{label}' must be ≤ {mx}.")
        return v

    def _collect_sched(self):
        idx=self.selected_algo
        procs=[]
        for i,row in enumerate(self.proc_rows):
            a=self._gi(row["arrival"],f"P{i} Arrival",0)
            b=self._gi(row["burst"],  f"P{i} Burst",  1)
            p=self._gi(row["priority"],f"P{i} Priority",1)
            procs.append({"pid":i,"arrival":a,"burst":b,"priority":p})
        km={0:"fcfs",1:"rr",2:"sjf",3:"srtf",4:"priority",5:"priority_pre"}
        dk=km[idx]
        data={"algo_idx":idx,dk:{"procs":procs}}
        # Store procs under all keys so sidebar switching works
        for k in km.values():
            if k not in data:
                data[k]={"procs":list(procs)}
        if idx==1:
            q=self._gi(self.quantum_var,"Time Quantum",1,20)
            data["rr"]["quantum"]=q
        else:
            data.setdefault("rr",{})["quantum"]=data.get("rr",{}).get("quantum",3)
        return data

    def _collect_dl(self):
        n_res=int(self.n_res_var.get());n_proc=int(self.n_dl_proc_var.get())
        rnames=[chr(ord("A")+j) for j in range(n_res)]
        total=[self._gi(v,f"Total {rnames[j]}",1) for j,v in enumerate(self.total_vars)]
        max_d=[[self._gi(self.max_vars[i][j],f"Max P{i} {rnames[j]}",0)
                for j in range(n_res)] for i in range(n_proc)]
        alloc=[[self._gi(self.alloc_vars[i][j],f"Alloc P{i} {rnames[j]}",0,max_d[i][j])
                for j in range(n_res)] for i in range(n_proc)]
        used=[sum(alloc[i][j] for i in range(n_proc)) for j in range(n_res)]
        for j in range(n_res):
            if used[j]>total[j]:
                raise ValueError(f"Total allocated for {rnames[j]} ({used[j]}) > total ({total[j]})")
        return{"algo_idx":6,"deadlock":{"alloc":alloc,"max_d":max_d,
                "total_res":total,"res_names":rnames,"n_res":n_res}}

    def _launch(self):
        try:
            idx=self.selected_algo
            if idx==6:data=self._collect_dl()
            else:data=self._collect_sched()
            data["gantt_colors"]=[hex_to_rgb(c) for c in self.gantt_colors]
            self.result=data
            self.root.destroy()
        except ValueError as e:messagebox.showerror("Input Error",str(e))
        except Exception as e:messagebox.showerror("Error",str(e))

    def run(self):
        self.root.mainloop()
        return self.result
