import tkinter as tk
from tkinter import colorchooser, ttk, messagebox
import time
import json
import os
import keyboard

CONFIG_FILE = "stream_timer_config.json"

class OverlayWindow:
    def __init__(self, parent, config):
        self.window = tk.Toplevel(parent)
        self.window.title("STREAM TIMER lite - OVERLAY")
        self.window.geometry("600x250")
        self.window.configure(bg=config['bg_color'])
        self.window.attributes("-topmost", config.get('always_on_top', True))
        
        self.config = config
        self.label = tk.Label(
            self.window, 
            text=self.config['text'], 
            font=(self.config['font_family'], self.config['font_size'], "bold"),
            fg=self.config['fg_color'], 
            bg=self.config['bg_color']
        )
        self.label.pack(expand=True, fill="both")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.is_open = True

    def on_close(self):
        self.is_open = False
        self.window.destroy()

    def update_view(self, config):
        self.config = config
        if self.is_open:
            self.label.config(
                text=self.config['text'],
                font=(self.config['font_family'], self.config['font_size'], "bold"),
                fg=self.config['fg_color'],
                bg=self.config['bg_color']
            )
            self.window.config(bg=self.config['bg_color'])
            self.window.attributes("-topmost", self.config.get('always_on_top', True))

class StreamTimerLite:
    def __init__(self, root):
        self.root = root
        self.root.title("STREAM TIMER lite")
        self.root.geometry("480x800")
        self.root.configure(bg="#111827") # Tailwind Slate 900

        # Default Settings
        self.config = {
            'text': "00:00",
            'font_family': "Impact",
            'font_size': 72,
            'fg_color': "#FFFFFF",
            'bg_color': "#00FF00",
            'prefix': "",
            'always_on_top': True,
            'play_sound': True
        }
        
        self.load_settings()
        self.start_time = 0
        self.target_seconds = 0
        self.running = False
        self.mode = "countdown"
        self.count_val = 0
        self.overlay = None

        self.setup_ui()
        self.setup_hotkeys()
        self.open_overlay()

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
            except: pass

    def save_settings(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

    def setup_ui(self):
        # Professional Header
        header = tk.Frame(self.root, bg="#1F2937", height=60)
        header.pack(fill="x")
        tk.Label(header, text="STREAM TIMER", font=("Helvetica", 16, "bold"), bg="#1F2937", fg="#60A5FA").pack(side="left", padx=20, pady=10)
        tk.Label(header, text="lite", font=("Helvetica", 12, "italic"), bg="#1F2937", fg="#9CA3AF").pack(side="left")

        container = tk.Frame(self.root, bg="#111827")
        container.pack(fill="both", expand=True, padx=25, pady=10)

        # Style Helper
        label_style = {"bg": "#111827", "fg": "#9CA3AF", "font": ("Segoe UI", 9, "bold")}

        # SECTION: OVERLAY CONTROL
        self.create_section_label(container, "OVERLAY MANAGEMENT")
        btn_frame = tk.Frame(container, bg="#111827")
        btn_frame.pack(fill="x", pady=5)
        
        tk.Button(btn_frame, text="RECOVER OVERLAY", command=self.open_overlay, bg="#3B82F6", fg="white", relief="flat", font=("Segoe UI", 10, "bold"), height=2).pack(fill="x")
        
        ontop_cb = tk.Checkbutton(container, text="Always on Top", bg="#111827", fg="white", selectcolor="#111827", 
                                  activebackground="#111827", activeforeground="white", command=self.toggle_ontop)
        if self.config['always_on_top']: ontop_cb.select()
        ontop_cb.pack(anchor="w", pady=5)

        # SECTION: DESIGN
        self.create_section_label(container, "VISUAL STYLING")
        design_card = tk.Frame(container, bg="#1F2937", padx=15, pady=15)
        design_card.pack(fill="x", pady=5)

        tk.Button(design_card, text="Background Color", command=self.choose_bg, width=18).grid(row=0, column=0, pady=5, padx=2)
        tk.Button(design_card, text="Text Color", command=self.choose_fg, width=18).grid(row=0, column=1, pady=5, padx=2)

        tk.Label(design_card, text="Font Family", **label_style).grid(row=1, column=0, columnspan=2, pady=(10,0))
        self.font_box = ttk.Combobox(design_card, values=["Impact", "Arial", "Verdana", "Courier New", "Tahoma"])
        self.font_box.set(self.config['font_family'])
        self.font_box.bind("<<ComboboxSelected>>", self.update_design)
        self.font_box.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        tk.Label(design_card, text="Font Size", **label_style).grid(row=3, column=0, columnspan=2, pady=(10,0))
        self.size_scale = tk.Scale(design_card, from_=20, to=200, orient="horizontal", bg="#1F2937", fg="white", highlightthickness=0, command=self.update_design)
        self.size_scale.set(self.config['font_size'])
        self.size_scale.grid(row=4, column=0, columnspan=2, sticky="ew")

        # SECTION: CONTENT
        self.create_section_label(container, "CONTENT & LABELS")
        self.prefix_entry = tk.Entry(container, bg="#1F2937", fg="white", insertbackground="white", borderwidth=5, relief="flat", font=("Segoe UI", 11))
        self.prefix_entry.insert(0, self.config['prefix'])
        self.prefix_entry.pack(fill="x", pady=5)
        self.prefix_entry.bind("<KeyRelease>", self.update_design)

        # SECTION: TIMER ENGINE
        self.create_section_label(container, "TIMER ENGINE")
        engine_card = tk.Frame(container, bg="#1F2937", padx=15, pady=15)
        engine_card.pack(fill="x", pady=5)

        tk.Label(engine_card, text="Minutes:", bg="#1F2937", fg="white").pack(side="left")
        self.time_entry = tk.Entry(engine_card, width=8, font=("Segoe UI", 12), bg="#111827", fg="#10B981", borderwidth=0)
        self.time_entry.insert(0, "5")
        self.time_entry.pack(side="left", padx=10)

        t_btn_frame = tk.Frame(container, bg="#111827")
        t_btn_frame.pack(fill="x", pady=10)
        tk.Button(t_btn_frame, text="START COUNTDOWN", bg="#10B981", fg="white", relief="flat", command=self.start_countdown, font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(t_btn_frame, text="STOPWATCH", bg="#6366F1", fg="white", relief="flat", command=self.start_stopwatch, font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(t_btn_frame, text="RESET", bg="#EF4444", fg="white", relief="flat", command=self.reset_all, font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x", padx=2)

        # SECTION: COUNTER
        self.create_section_label(container, "LIVE COUNTER (F8/F9)")
        c_btn_frame = tk.Frame(container, bg="#111827")
        c_btn_frame.pack(fill="x", pady=5)
        tk.Button(c_btn_frame, text="+ ADD", bg="#F59E0B", fg="white", font=("Segoe UI", 12, "bold"), relief="flat", command=self.inc_counter).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(c_btn_frame, text="- SUB", bg="#D97706", fg="white", font=("Segoe UI", 12, "bold"), relief="flat", command=self.dec_counter).pack(side="left", expand=True, fill="x", padx=2)

    def create_section_label(self, parent, text):
        lbl = tk.Label(parent, text=text, bg="#111827", fg="#4B5563", font=("Segoe UI", 8, "bold"))
        lbl.pack(anchor="w", pady=(15, 2))

    def setup_hotkeys(self):
        keyboard.add_hotkey('f8', self.inc_counter)
        keyboard.add_hotkey('f9', self.dec_counter)
        keyboard.add_hotkey('f10', self.reset_all)

    def open_overlay(self):
        if self.overlay is None or not self.overlay.is_open:
            self.overlay = OverlayWindow(self.root, self.config)
        self.refresh_overlay_text()

    def update_design(self, event=None):
        self.config['font_family'] = self.font_box.get()
        self.config['font_size'] = self.size_scale.get()
        self.config['prefix'] = self.prefix_entry.get()
        self.refresh_overlay_text()
        self.save_settings()

    def toggle_ontop(self):
        self.config['always_on_top'] = not self.config['always_on_top']
        self.refresh_overlay_text()
        self.save_settings()

    def refresh_overlay_text(self):
        if self.overlay: self.overlay.update_view(self.config)

    def choose_bg(self):
        color = colorchooser.askcolor(title="Select BG", initialcolor=self.config['bg_color'])[1]
        if color: self.config['bg_color'] = color; self.update_design()

    def choose_fg(self):
        color = colorchooser.askcolor(title="Select Font", initialcolor=self.config['fg_color'])[1]
        if color: self.config['fg_color'] = color; self.update_design()

    def update_loop(self):
        if not self.running: return
        elapsed = time.time() - self.start_time
        if self.mode == "countdown":
            remaining = self.target_seconds - elapsed
            if remaining <= 0:
                self.config['text'] = f"{self.config['prefix']} 00:00"
                self.running = False
                self.root.bell()
            else:
                mins, secs = divmod(int(remaining), 60)
                self.config['text'] = f"{self.config['prefix']} {mins:02d}:{secs:02d}"
        else:
            mins, secs = divmod(int(elapsed), 60)
            self.config['text'] = f"{self.config['prefix']} {mins:02d}:{secs:02d}"
        self.refresh_overlay_text()
        self.root.after(100, self.update_loop)

    def start_countdown(self):
        try:
            self.target_seconds = int(self.time_entry.get()) * 60
            self.start_time = time.time()
            self.mode = "countdown"
            self.running = True
            self.update_loop()
        except: pass

    def start_stopwatch(self):
        self.start_time = time.time()
        self.mode = "stopwatch"
        self.running = True
        self.update_loop()

    def reset_all(self):
        self.running = False
        self.count_val = 0
        self.config['text'] = "00:00"
        self.refresh_overlay_text()

    def inc_counter(self):
        self.running = False
        self.count_val += 1
        self.config['text'] = f"{self.config['prefix']} {self.count_val}"
        self.refresh_overlay_text()

    def dec_counter(self):
        self.running = False
        self.count_val -= 1
        self.config['text'] = f"{self.config['prefix']} {self.count_val}"
        self.refresh_overlay_text()

if __name__ == "__main__":
    root = tk.Tk()
    app = StreamTimerLite(root)
    root.mainloop()