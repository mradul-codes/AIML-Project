import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import sys
import time
from pathlib import Path

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
HAND_DIR    = BASE_DIR / "hand-gesture-recognition-mediapipe-main" / "hand-gesture-recognition-mediapipe-main"
HAND_SCRIPT = HAND_DIR / "app.py"
FACE_DIR    = BASE_DIR / "Facial emotion system"
FACE_SCRIPT = FACE_DIR / "test.py"
# ─────────────────────────────────────────────────────────────────────────────

GESTURES = ["Open", "Close", "Pointer", "OK", "Stop", "Clockwise", "Counter CW", "Move"]
EMOTIONS = ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise"]

# ── Colors ────────────────────────────────────────────────────────────────────
BG0    = "#07080f"
BG1    = "#0d0e18"
BG2    = "#12131f"
BG3    = "#181928"
BG4    = "#1e1f30"
BG5    = "#252638"
GOLD   = "#c8a84b"
GOLD2  = "#e8c870"
GOLD3  = "#7a6030"
BLUE   = "#4a9eff"
BLUE2  = "#7ab8ff"
VIOLET = "#a855f7"
VIO2   = "#c084fc"
GREEN  = "#22c55e"
GREEN2 = "#4ade80"
AMBER  = "#f59e0b"
RED    = "#ef4444"
WHITE  = "#f0f4ff"
FG1    = "#c8d0f0"
FG2    = "#6068a0"
FG3    = "#30304a"
FG4    = "#1e1e2e"


class BlinkDot(tk.Canvas):
    """Simple reliable blinking dot."""
    def __init__(self, parent, size=10, **kw):
        bg = kw.pop("bg", BG3)
        super().__init__(parent, width=size, height=size,
                         bg=bg, highlightthickness=0)
        self._size   = size
        self._color  = FG3
        self._active = False
        self._on     = True
        self._redraw()

    def _redraw(self):
        self.delete("all")
        s = self._size
        col = self._color if self._on else FG4
        self.create_oval(1, 1, s-1, s-1, fill=col, outline="")

    def start(self, color=GREEN):
        self._color  = color
        self._active = True
        self._blink()

    def stop(self):
        self._active = False
        self._color  = FG3
        self._on     = True
        self._redraw()

    def _blink(self):
        if not self._active:
            return
        self._on = not self._on
        self._redraw()
        self.after(600, self._blink)


def make_label(parent, text, font, fg, bg, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)


def make_button(parent, text, bg, fg, cmd, font=("Consolas", 10, "bold"), pady=11):
    return tk.Button(
        parent, text=text,
        font=font, fg=fg, bg=bg,
        activebackground=bg, activeforeground=WHITE,
        relief="flat", bd=0,
        padx=16, pady=pady,
        cursor="hand2",
        command=cmd
    )


def hsep(parent, bg=BG4):
    tk.Frame(parent, bg=bg, height=1).pack(fill="x")


class ModuleCard(tk.Frame):
    def __init__(self, parent, cfg, on_launch, on_stop, **kw):
        super().__init__(parent, bg=BG0, **kw)
        self.cfg      = cfg
        self._launch  = on_launch
        self._stop    = on_stop
        self.running  = False
        self._start_t = None
        self._build()

    def _build(self):
        cfg = self.cfg
        acc = cfg["accent"]
        acc2 = cfg["accent2"]

        # outer accent border
        outer = tk.Frame(self, bg=acc, padx=1, pady=1)
        outer.pack(fill="both", expand=True)

        card = tk.Frame(outer, bg=BG2)
        card.pack(fill="both", expand=True)

        # ── Top stripe ───────────────────────────────────────────────
        stripe = tk.Frame(card, bg=BG3, pady=0)
        stripe.pack(fill="x")
        tk.Frame(stripe, bg=acc, height=3).pack(fill="x")

        stripe_inner = tk.Frame(stripe, bg=BG3, padx=16, pady=8)
        stripe_inner.pack(fill="x")
        make_label(stripe_inner, cfg["mod_id"],
                   ("Consolas", 8), FG3, BG3).pack(side="left")
        self._status_badge = make_label(stripe_inner, "● STANDBY",
                                        ("Consolas", 8), FG3, BG3)
        self._status_badge.pack(side="right")

        # ── Header ───────────────────────────────────────────────────
        hdr = tk.Frame(card, bg=BG3, padx=18, pady=16)
        hdr.pack(fill="x")

        left = tk.Frame(hdr, bg=BG3)
        left.pack(side="left", fill="both", expand=True)

        # icon box
        icon_box = tk.Frame(left, bg=acc, width=48, height=48)
        icon_box.pack_propagate(False)
        icon_box.pack(anchor="w")
        make_label(icon_box, cfg["icon"],
                   ("Consolas", 18, "bold"), BG0, acc).place(
            relx=0.5, rely=0.5, anchor="center")

        make_label(left, cfg["title"],
                   ("Consolas", 15, "bold"), WHITE, BG3,
                   anchor="w").pack(fill="x", pady=(10, 0))
        make_label(left, cfg["subtitle"],
                   ("Consolas", 8), FG2, BG3,
                   anchor="w").pack(fill="x", pady=(3, 0))

        # tech tags
        tag_row = tk.Frame(left, bg=BG3)
        tag_row.pack(anchor="w", pady=(10, 0))
        for t in cfg["tags"]:
            f = tk.Frame(tag_row, bg=BG5,
                         highlightbackground=FG4,
                         highlightthickness=1)
            f.pack(side="left", padx=(0, 5))
            make_label(f, f" {t} ",
                       ("Consolas", 7), acc, BG5,
                       pady=2).pack()

        # right: dot + uptime
        right = tk.Frame(hdr, bg=BG3)
        right.pack(side="right", anchor="n", padx=(10, 0))

        self.dot = BlinkDot(right, size=12, bg=BG3)
        self.dot.pack(pady=(4, 8))

        uptime_f = tk.Frame(right, bg=BG4,
                             highlightbackground=FG4,
                             highlightthickness=1)
        uptime_f.pack()
        make_label(uptime_f, "UPTIME",
                   ("Consolas", 7), FG3, BG4,
                   padx=12, pady=3).pack()
        self.uptime_lbl = make_label(uptime_f, "  —  ",
                                      ("Consolas", 9, "bold"), FG2, BG4,
                                      padx=12, pady=4)
        self.uptime_lbl.pack()

        # ── Divider ──────────────────────────────────────────────────
        tk.Frame(card, bg=BG4, height=1).pack(fill="x")

        # ── Chips ────────────────────────────────────────────────────
        chip_area = tk.Frame(card, bg=BG2, padx=18, pady=14)
        chip_area.pack(fill="x")

        make_label(chip_area, cfg["chip_label"],
                   ("Consolas", 7), FG3, BG2,
                   anchor="w").pack(fill="x", pady=(0, 8))

        grid = tk.Frame(chip_area, bg=BG2)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for i, name in enumerate(cfg["chips"]):
            ri, col = divmod(i, 2)
            cell = tk.Frame(grid, bg=BG3,
                            highlightbackground=BG4,
                            highlightthickness=1)
            cell.grid(row=ri, column=col, padx=2, pady=2, sticky="ew")
            row_f = tk.Frame(cell, bg=BG3)
            row_f.pack(fill="x", padx=10, pady=6)
            make_label(row_f, "▸ ",
                       ("Consolas", 8), acc, BG3).pack(side="left")
            make_label(row_f, name,
                       ("Consolas", 8), FG1, BG3).pack(side="left")

        # ── Divider ──────────────────────────────────────────────────
        tk.Frame(card, bg=BG4, height=1).pack(fill="x")

        # ── Button ───────────────────────────────────────────────────
        btn_wrap = tk.Frame(card, bg=BG2, padx=18, pady=16)
        btn_wrap.pack(fill="x")

        self.btn = make_button(btn_wrap,
                               text=cfg["btn_start"],
                               bg=acc, fg=BG0,
                               cmd=self._toggle)
        self.btn.pack(fill="x")

        stat_row = tk.Frame(btn_wrap, bg=BG2)
        stat_row.pack(fill="x", pady=(10, 0))

        self.stat_lbl = make_label(stat_row, "◉  IDLE",
                                    ("Consolas", 8), FG3, BG2)
        self.stat_lbl.pack(side="left")

        hint = "ESC to stop" if "01" in cfg["mod_id"] else "Q to stop"
        make_label(stat_row, hint,
                   ("Consolas", 7), FG3, BG2).pack(side="right")

    def _toggle(self):
        if not self.running:
            self._launch()
        else:
            self._stop()

    def set_running(self, val):
        self.running = val
        cfg = self.cfg
        if val:
            self._start_t = time.time()
            self.btn.config(text=cfg["btn_stop"],
                            bg=AMBER, fg=BG0,
                            activebackground=AMBER)
            self.stat_lbl.config(text="◉  RUNNING", fg=GREEN2)
            self._status_badge.config(text="● ACTIVE", fg=GREEN2)
            self.dot.start(GREEN)
        else:
            self._start_t = None
            self.btn.config(text=cfg["btn_start"],
                            bg=cfg["accent"], fg=BG0,
                            activebackground=cfg["accent"])
            self.stat_lbl.config(text="◉  IDLE", fg=FG3)
            self._status_badge.config(text="● STANDBY", fg=FG3)
            self.uptime_lbl.config(text="  —  ", fg=FG2)
            self.dot.stop()

    def tick(self):
        if self.running and self._start_t:
            e = int(time.time() - self._start_t)
            h, rem = divmod(e, 3600)
            m, s   = divmod(rem, 60)
            self.uptime_lbl.config(
                text=f"{h:02d}:{m:02d}:{s:02d}", fg=GREEN2)


class LogPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG0, **kw)

        hdr = tk.Frame(self, bg=BG0)
        hdr.pack(fill="x", pady=(0, 6))
        make_label(hdr, "SYSTEM LOG",
                   ("Consolas", 8, "bold"), FG2, BG0).pack(side="left")
        tk.Button(hdr, text="CLEAR",
                  font=("Consolas", 7), fg=FG3, bg=BG0,
                  bd=0, relief="flat",
                  activebackground=BG0, activeforeground=GOLD,
                  cursor="hand2",
                  command=self._clear).pack(side="right")

        border = tk.Frame(self, bg=BG4, padx=1, pady=1)
        border.pack(fill="both", expand=True)

        inner = tk.Frame(border, bg=BG1)
        inner.pack(fill="both", expand=True)

        self.txt = tk.Text(inner,
                           font=("Consolas", 8),
                           bg=BG1, fg=FG1,
                           relief="flat", bd=0,
                           state="disabled",
                           height=7, wrap="word",
                           padx=12, pady=8,
                           selectbackground=BG4,
                           insertbackground=GOLD)
        sb = tk.Scrollbar(inner, command=self.txt.yview,
                          bg=BG4, troughcolor=BG1,
                          relief="flat", width=5, bd=0)
        self.txt.configure(yscrollcommand=sb.set)
        self.txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        for tag, col in [("gold", GOLD2), ("blue", BLUE2),
                         ("violet", VIO2), ("green", GREEN2),
                         ("red", RED), ("amber", AMBER),
                         ("dim", FG2), ("ts", FG3)]:
            self.txt.tag_configure(tag, foreground=col)

    def write(self, msg, tag="dim"):
        self.txt.configure(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.txt.insert("end", f"  {ts}  ", "ts")
        self.txt.insert("end", f"{msg}\n", tag)
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def _clear(self):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.configure(state="disabled")


class AIVisionGUI:
    def __init__(self, root):
        self.root      = root
        self.root.title("AI Vision Suite  v4.0")
        self.root.configure(bg=BG0)
        self.root.resizable(True, True)
        self.hand_proc = None
        self.face_proc = None
        self._tick_job = None
        self._build()
        self._center()
        self._tick()

    def _build(self):
        r = self.root

        # ── Nav bar ───────────────────────────────────────────────────────
        nav = tk.Frame(r, bg=BG1, padx=28)
        nav.pack(fill="x")
        tk.Frame(nav, bg=GOLD3, height=1).pack(fill="x")

        nav_row = tk.Frame(nav, bg=BG1)
        nav_row.pack(fill="x", pady=13)

        # logo
        logo = tk.Frame(nav_row, bg=BG1)
        logo.pack(side="left")
        make_label(logo, "AI", ("Consolas", 18, "bold"), GOLD, BG1).pack(side="left")
        make_label(logo, "VISION", ("Consolas", 18, "bold"), WHITE, BG1).pack(side="left", padx=(4,0))
        make_label(nav_row, "SUITE", ("Consolas", 8), FG3, BG1).pack(side="left", padx=(8,0))

        # right
        self.clock_var = tk.StringVar()
        make_label(nav_row, "", ("Consolas", 1), BG1, BG1).pack(side="right", padx=(0,0))
        tk.Label(nav_row, textvariable=self.clock_var,
                 font=("Consolas", 9), fg=FG3, bg=BG1).pack(side="right", padx=(12,0))
        make_label(nav_row, "v4.0", ("Consolas", 8), FG3, BG1).pack(side="right")

        tk.Frame(nav, bg=BG4, height=1).pack(fill="x")

        # ── Hero ──────────────────────────────────────────────────────────
        hero = tk.Frame(r, bg=BG1, padx=32, pady=24)
        hero.pack(fill="x")

        left_h = tk.Frame(hero, bg=BG1)
        left_h.pack(side="left")

        make_label(left_h, "REAL-TIME COMPUTER VISION PLATFORM",
                   ("Consolas", 8), GOLD3, BG1,
                   anchor="w").pack(fill="x")

        title_row = tk.Frame(left_h, bg=BG1)
        title_row.pack(anchor="w", pady=(6,0))
        make_label(title_row, "DETECTION",
                   ("Consolas", 28, "bold"), WHITE, BG1).pack(side="left")
        make_label(title_row, " HUB",
                   ("Consolas", 28, "bold"), GOLD, BG1).pack(side="left")

        make_label(left_h,
                   "Deploy AI modules with one click  ·  Hand Gesture  ·  Facial Emotion",
                   ("Consolas", 8), FG2, BG1,
                   anchor="w").pack(fill="x", pady=(8,0))

        # metric badges
        right_h = tk.Frame(hero, bg=BG1)
        right_h.pack(side="right", anchor="e")

        for lbl, val, col in [("MODULES", "2", GOLD),
                               ("STATUS", "ONLINE", GREEN2),
                               ("BUILD", "v4.0", FG2)]:
            f = tk.Frame(right_h, bg=BG3,
                         highlightbackground=BG4,
                         highlightthickness=1)
            f.pack(side="left", padx=6)
            make_label(f, lbl, ("Consolas", 7), FG3, BG3, padx=16, pady=5).pack()
            make_label(f, val, ("Consolas", 11, "bold"), col, BG3, padx=16, pady=7).pack()

        tk.Frame(r, bg=BG4, height=1).pack(fill="x", padx=32)

        # ── Module cards ──────────────────────────────────────────────────
        body = tk.Frame(r, bg=BG0, padx=26, pady=20)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1, uniform="c")
        body.columnconfigure(1, weight=1, uniform="c")
        body.rowconfigure(0, weight=1)

        hand_cfg = {
            "mod_id":     "MOD-01",
            "accent":     BLUE,
            "accent2":    BLUE2,
            "icon":       "H",
            "title":      "HAND GESTURE",
            "subtitle":   "MediaPipe  ·  TFLite  ·  21-point Landmark",
            "tags":       ["MediaPipe", "TFLite", "Real-time"],
            "chip_label": "CLASSIFIED GESTURES",
            "chips":      GESTURES,
            "btn_start":  "▶   LAUNCH  HAND GESTURE",
            "btn_stop":   "■   STOP  HAND GESTURE",
        }
        face_cfg = {
            "mod_id":     "MOD-02",
            "accent":     VIOLET,
            "accent2":    VIO2,
            "icon":       "F",
            "title":      "FACIAL EMOTION",
            "subtitle":   "Keras CNN  ·  HaarCascade  ·  7-Class",
            "tags":       ["Keras", "OpenCV", "HaarCascade"],
            "chip_label": "CLASSIFIED EMOTIONS",
            "chips":      EMOTIONS,
            "btn_start":  "▶   LAUNCH  FACIAL EMOTION",
            "btn_stop":   "■   STOP  FACIAL EMOTION",
        }

        self.hand_card = ModuleCard(body, hand_cfg,
                                    on_launch=self._start_hand,
                                    on_stop=self._stop_hand)
        self.hand_card.grid(row=0, column=0, sticky="nsew", padx=(0,10))

        self.face_card = ModuleCard(body, face_cfg,
                                    on_launch=self._start_face,
                                    on_stop=self._stop_face)
        self.face_card.grid(row=0, column=1, sticky="nsew", padx=(10,0))

        # ── Log ───────────────────────────────────────────────────────────
        log_wrap = tk.Frame(r, bg=BG0, padx=26)
        log_wrap.pack(fill="x")
        self.log = LogPanel(log_wrap)
        self.log.pack(fill="x")

        # ── Footer ────────────────────────────────────────────────────────
        footer = tk.Frame(r, bg=BG1, padx=26, pady=10)
        footer.pack(fill="x", pady=(16, 0))
        tk.Frame(footer, bg=BG4, height=1).pack(fill="x", pady=(0, 8))

        self.status_var = tk.StringVar(value="SYSTEM READY  —  ALL MODULES ONLINE")
        tk.Label(footer, textvariable=self.status_var,
                 font=("Consolas", 8), fg=FG2, bg=BG1,
                 anchor="w").pack(side="left")
        make_label(footer,
                   "AI Vision Suite  ·  Real-Time Detection Platform",
                   ("Consolas", 8), FG3, BG1).pack(side="right")

        self.log.write("System initialized. All modules online.", "gold")

    def _center(self):
        w, h = 960, 840
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _tick(self):
        self.clock_var.set(time.strftime("%Y-%m-%d   %H:%M:%S"))
        self.hand_card.tick()
        self.face_card.tick()
        self._tick_job = self.root.after(1000, self._tick)

    # ── Hand ─────────────────────────────────────────────────────────────────
    def _start_hand(self):
        if not HAND_SCRIPT.exists():
            messagebox.showerror("Not Found",
                f"Cannot find:\n{HAND_SCRIPT}\n\n"
                "Place gui_launcher.py in the 'Aiml project' folder.")
            self.log.write(f"ERROR: {HAND_SCRIPT} not found", "red")
            return
        self.hand_card.set_running(True)
        self.status_var.set("MOD-01  HAND GESTURE  —  ACTIVE")
        self.log.write("MOD-01  Hand Gesture launched. Press ESC to stop.", "blue")

        def _run():
            self.hand_proc = subprocess.Popen(
                [sys.executable, str(HAND_SCRIPT)],
                cwd=str(HAND_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True)
            for line in self.hand_proc.stdout:
                l = line.strip()
                if l:
                    self.root.after(0, lambda x=l:
                        self.log.write(f"[HAND] {x}", "dim"))
            self.hand_proc.wait()
            self.root.after(0, self._hand_done)

        threading.Thread(target=_run, daemon=True).start()

    def _stop_hand(self):
        if self.hand_proc and self.hand_proc.poll() is None:
            self.hand_proc.terminate()
            self.log.write("MOD-01  Stopped by user.", "amber")

    def _hand_done(self):
        self.hand_proc = None
        self.hand_card.set_running(False)
        self.status_var.set("MOD-01  HAND GESTURE  —  STOPPED")
        self.log.write("MOD-01  Hand Gesture exited.", "dim")

    # ── Face ─────────────────────────────────────────────────────────────────
    def _start_face(self):
        if not FACE_SCRIPT.exists():
            messagebox.showerror("Not Found",
                f"Cannot find:\n{FACE_SCRIPT}\n\n"
                "Place gui_launcher.py in the 'Aiml project' folder.")
            self.log.write(f"ERROR: {FACE_SCRIPT} not found", "red")
            return
        self.face_card.set_running(True)
        self.status_var.set("MOD-02  FACIAL EMOTION  —  ACTIVE")
        self.log.write("MOD-02  Facial Emotion launched. Press Q to stop.", "violet")

        def _run():
            self.face_proc = subprocess.Popen(
                [sys.executable, str(FACE_SCRIPT)],
                cwd=str(FACE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True)
            for line in self.face_proc.stdout:
                l = line.strip()
                if l:
                    self.root.after(0, lambda x=l:
                        self.log.write(f"[FACE] {x}", "dim"))
            self.face_proc.wait()
            self.root.after(0, self._face_done)

        threading.Thread(target=_run, daemon=True).start()

    def _stop_face(self):
        if self.face_proc and self.face_proc.poll() is None:
            self.face_proc.terminate()
            self.log.write("MOD-02  Stopped by user.", "amber")

    def _face_done(self):
        self.face_proc = None
        self.face_card.set_running(False)
        self.status_var.set("MOD-02  FACIAL EMOTION  —  STOPPED")
        self.log.write("MOD-02  Facial Emotion exited.", "dim")

    def on_close(self):
        for p in (self.hand_proc, self.face_proc):
            if p and p.poll() is None:
                p.terminate()
        if self._tick_job:
            self.root.after_cancel(self._tick_job)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app  = AIVisionGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
