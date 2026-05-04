import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from .pdf_loader import load_pdf_images
from .calibration import Calibrator
from .curve_extractor import CurveExtractor
from .analyzer import analyze_bode
from .exporter import export_to_csv

class DigitizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Graph Digitizer & Analyzer")
        self.root.geometry("1400x900")
        
        self.images = []
        self.current_image_cv = None
        self.image_photo = None
        
        self.calibrator = Calibrator()
        self.extractor = CurveExtractor(self.calibrator)
        
        self.state = 'idle'
        self.temp_points = []
        self.zoom_factor = 0.3
        
        self.axis_labels = {
            'x': 'X',
            'left_y': 'Left Y',
            'right_y': 'Right Y'
        }
        self.plot_bg_color = 'white'
        self.grid_style = '-'
        self.grid_spacing_x = ''
        self.grid_spacing_ly = ''
        self.grid_spacing_ry = ''
        
        self.cursor_v = None
        self.cursor_h = None
        self.cursor_annot = None
        self.dragging = None
        
        self.build_ui()
        
    def on_left_mouse_wheel(self, event):
        amt = self._get_scroll_amt(event)
        self.left_canvas.yview_scroll(amt, "units")

    def build_ui(self):
        # Left Panel Configuration
        self.left_container = tk.Frame(self.root, width=280, bg="#f5f5f5")
        self.left_container.pack(side=tk.LEFT, fill=tk.Y)
        self.left_container.pack_propagate(False)
        
        self.left_canvas = tk.Canvas(self.left_container, bg="#f5f5f5", highlightthickness=0)
        self.left_scrollbar = tk.Scrollbar(self.left_container, orient="vertical", command=self.left_canvas.yview)
        
        self.left_panel = tk.Frame(self.left_canvas, bg="#f5f5f5", padx=5, pady=10)
        
        self.left_panel.bind(
            "<Configure>",
            lambda e: self.left_canvas.configure(
                scrollregion=self.left_canvas.bbox("all")
            )
        )
        
        self.left_canvas.create_window((0, 0), window=self.left_panel, anchor="nw", width=260)
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def _bind_mousewheel(event):
            self.left_canvas.bind_all("<MouseWheel>", self.on_left_mouse_wheel)
            self.left_canvas.bind_all("<Button-4>", self.on_left_mouse_wheel)
            self.left_canvas.bind_all("<Button-5>", self.on_left_mouse_wheel)
            
        def _unbind_mousewheel(event):
            self.left_canvas.unbind_all("<MouseWheel>")
            self.left_canvas.unbind_all("<Button-4>")
            self.left_canvas.unbind_all("<Button-5>")
            
        self.left_container.bind("<Enter>", _bind_mousewheel)
        self.left_container.bind("<Leave>", _unbind_mousewheel)
        
        tk.Label(self.left_panel, text="1. INPUT & VIEW", font=("Arial", 11, "bold"), bg="#f5f5f5").pack(anchor=tk.W, pady=(0, 5))
        tk.Button(self.left_panel, text="Load PDF", command=self.load_pdf, width=25).pack(pady=2)
        tk.Button(self.left_panel, text="Load CSV & Plot", command=self.load_csv, width=25).pack(pady=2)
        
        self.page_var = tk.StringVar()
        self.page_combo = ttk.Combobox(self.left_panel, textvariable=self.page_var, state="readonly", width=22)
        self.page_combo.pack(pady=5)
        self.page_combo.bind("<<ComboboxSelected>>", self.on_page_change)
        
        zoom_frame = tk.Frame(self.left_panel, bg="#f5f5f5")
        zoom_frame.pack(fill=tk.X, pady=2)
        tk.Button(zoom_frame, text="Zoom In (+)", command=self.zoom_in, width=10).pack(side=tk.LEFT, padx=(5, 2))
        tk.Button(zoom_frame, text="Zoom Out (-)", command=self.zoom_out, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(zoom_frame, text="Fit", command=self.zoom_fit, width=4).pack(side=tk.LEFT, padx=2)
        
        tk.Label(self.left_panel, text="2. CALIBRATION", font=("Arial", 11, "bold"), bg="#f5f5f5").pack(anchor=tk.W, pady=(20, 5))
        
        self.single_y_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.left_panel, text="Single Y Axis", variable=self.single_y_var, command=self.on_single_y_toggle, bg="#f5f5f5").pack(anchor=tk.W, pady=(0, 2))
        
        tk.Button(self.left_panel, text="Calibrate X Axis", command=lambda: self.start_calibration('X'), width=25).pack(pady=2)
        
        self.cal_left_y_btn = tk.Button(self.left_panel, text="Calibrate Left Y", command=lambda: self.start_calibration('Left Y'), width=25)
        self.cal_left_y_btn.pack(pady=2)
        
        self.cal_right_y_btn = tk.Button(self.left_panel, text="Calibrate Right Y", command=lambda: self.start_calibration('Right Y'), width=25)
        self.cal_right_y_btn.pack(pady=2)
        
        self.clear_calib_btn = tk.Button(self.left_panel, text="Clear Calibration", command=self.clear_calibration, width=25, bg="#ffcccc")
        self.clear_calib_btn.pack(pady=(10, 2))
        
        tk.Label(self.left_panel, text="3. DIGITIZE & ANALYZE", font=("Arial", 11, "bold"), bg="#f5f5f5").pack(anchor=tk.W, pady=(20, 5))
        
        sep_frame = tk.Frame(self.left_panel, bg="#f5f5f5")
        sep_frame.pack(anchor=tk.W, pady=(0, 5), fill=tk.X)
        self.separate_graphs_var = tk.BooleanVar(value=False)
        tk.Checkbutton(sep_frame, text="Separate Every Plot", variable=self.separate_graphs_var, command=self.replot, bg="#f5f5f5").pack(side=tk.LEFT)
        
        self.layout_var = tk.StringVar(value="Vertical")
        self.layout_combo = ttk.Combobox(sep_frame, textvariable=self.layout_var, values=["Vertical", "Horizontal", "Grid"], width=8, state="readonly")
        self.layout_combo.bind("<<ComboboxSelected>>", lambda e: self.replot())
        self.layout_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        tk.Button(self.left_panel, text="Extract Curve by Color", command=self.start_extraction, width=25).pack(pady=2)
        tk.Button(self.left_panel, text="Analyze Bode (0dB / PM)", command=self.analyze, width=25, bg="#4CAF50", fg="white", font=("Arial", 9, "bold")).pack(pady=(10, 2))
        
        bode_frame = tk.Frame(self.left_panel, bg="#f5f5f5")
        bode_frame.pack(pady=(0, 10))
        tk.Label(bode_frame, text="Annotate:", bg="#f5f5f5").pack(side=tk.LEFT)
        self.bode_annot_var = tk.StringVar(value="Both")
        ttk.Combobox(bode_frame, textvariable=self.bode_annot_var, values=["Both", "Only PM", "Only GM", "None"], width=10, state="readonly").pack(side=tk.LEFT, padx=(5, 0))
        
        tk.Label(self.left_panel, text="4. DATA PROCESSING", font=("Arial", 11, "bold"), bg="#f5f5f5").pack(anchor=tk.W, pady=(15, 5))
        tk.Button(self.left_panel, text="Smooth Curves (SavGol)", command=self.smooth_curves, width=25).pack(pady=2)
        tk.Button(self.left_panel, text="Resample (Uniform X Grid)", command=self.resample_curves, width=25).pack(pady=2)
        tk.Button(self.left_panel, text="Find Peaks/Valleys", command=self.find_peaks, width=25).pack(pady=2)
        
        tk.Label(self.left_panel, text="5. CURVE MANAGEMENT", font=("Arial", 11, "bold"), bg="#f5f5f5").pack(anchor=tk.W, pady=(15, 5))
        tk.Button(self.left_panel, text="Rename Curve", command=self.rename_curve, width=25).pack(pady=2)
        tk.Button(self.left_panel, text="Delete Curve", command=self.delete_curve, width=25).pack(pady=2)
        tk.Button(self.left_panel, text="Shift / Scale Curve", command=self.math_curve, width=25).pack(pady=2)
        tk.Button(self.left_panel, text="Curve Statistics", command=self.curve_stats, width=25).pack(pady=2)
        tk.Button(self.left_panel, text="Calculate Difference (A - B)", command=self.diff_curves, width=25).pack(pady=2)
        
        tk.Label(self.left_panel, text="6. VIEW & EXPORT", font=("Arial", 11, "bold"), bg="#f5f5f5").pack(anchor=tk.W, pady=(15, 5))
        
        self.show_cursors_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.left_panel, text="Show Measurement Cursors", variable=self.show_cursors_var, command=self.toggle_cursors, bg="#f5f5f5").pack(anchor=tk.W, pady=(0, 2))
        
        sync_frame = tk.Frame(self.left_panel, bg="#f5f5f5")
        sync_frame.pack(anchor=tk.W, pady=(0, 5), padx=20)
        tk.Label(sync_frame, text="Sync:", bg="#f5f5f5").pack(side=tk.LEFT)
        self.cursor_sync_var = tk.StringVar(value="X Only")
        sync_combo = ttk.Combobox(sync_frame, textvariable=self.cursor_sync_var, values=["X Only", "Y Only", "Both", "None"], state="readonly", width=10)
        sync_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        tk.Button(self.left_panel, text="Plot Settings (Labels/Colors)", command=self.open_plot_settings, width=25).pack(pady=2)
        tk.Button(self.left_panel, text="Set Plot Limits", command=self.set_plot_limits, width=25).pack(pady=(2, 10))
        tk.Button(self.left_panel, text="Export Data (CSV)", command=self.export_csv, width=25).pack(pady=2)
        tk.Button(self.left_panel, text="Export Plot (PNG)", command=self.export_png, width=25).pack(pady=2)
        tk.Button(self.left_panel, text="Export Plot (PDF)", command=self.export_pdf, width=25).pack(pady=2)
        
        self.status_var = tk.StringVar(value="Status: Idle\n\nLoad a PDF to begin.")
        tk.Label(self.left_panel, textvariable=self.status_var, wraplength=250, bg="#f5f5f5", fg="#003366", font=("Arial", 10, "bold")).pack(side=tk.BOTTOM, pady=20)
        
        # Right Panel (Splitter)
        self.right_panel = tk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Top Panel: Image interaction
        self.img_frame = tk.Frame(self.right_panel)
        self.right_panel.add(self.img_frame, minsize=350)
        
        self.canvas_x_scroll = tk.Scrollbar(self.img_frame, orient=tk.HORIZONTAL)
        self.canvas_x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas_y_scroll = tk.Scrollbar(self.img_frame, orient=tk.VERTICAL)
        self.canvas_y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.img_canvas = tk.Canvas(self.img_frame, bg="#e0e0e0", xscrollcommand=self.canvas_x_scroll.set, yscrollcommand=self.canvas_y_scroll.set)
        self.img_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas_x_scroll.config(command=self.img_canvas.xview)
        self.canvas_y_scroll.config(command=self.img_canvas.yview)
        self.img_canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Scroll Bindings (Windows and Linux/Mac)
        self.img_canvas.bind("<MouseWheel>", self.on_mouse_wheel_y)
        self.img_canvas.bind("<Button-4>", self.on_mouse_wheel_y)
        self.img_canvas.bind("<Button-5>", self.on_mouse_wheel_y)
        
        self.img_canvas.bind("<Shift-MouseWheel>", self.on_mouse_wheel_x)
        self.img_canvas.bind("<Shift-Button-4>", self.on_mouse_wheel_x)
        self.img_canvas.bind("<Shift-Button-5>", self.on_mouse_wheel_x)
        
        self.img_canvas.bind("<Control-MouseWheel>", self.on_mouse_wheel_zoom)
        self.img_canvas.bind("<Control-Button-4>", self.on_mouse_wheel_zoom)
        self.img_canvas.bind("<Control-Button-5>", self.on_mouse_wheel_zoom)
        
        # Bind canvas enter event to focus it so scrolling works without clicking first
        self.img_canvas.bind("<Enter>", lambda e: self.img_canvas.focus_set())
        
        # Bottom Panel: Matplotlib output
        self.plot_frame = tk.Frame(self.right_panel)
        self.right_panel.add(self.plot_frame, minsize=350)
        
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = None
        
        self.plot_canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.plot_canvas.draw()
        
        self.toolbar_frame = tk.Frame(self.plot_frame)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.plot_canvas, self.toolbar_frame)
        self.toolbar.update()
        
        self.coord_label = tk.Label(self.toolbar_frame, text="Cursor [X: -- , Y: --]", font=("Consolas", 11))
        self.coord_label.pack(side=tk.RIGHT, padx=10)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_plot_mouse_move)
        self.fig.canvas.mpl_connect('button_press_event', self.on_plot_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_plot_release)
        
        self.plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
    def on_single_y_toggle(self):
        if self.single_y_var.get():
            self.cal_left_y_btn.config(text="Calibrate Y Axis")
            self.cal_right_y_btn.pack_forget()
            self.axis_labels['left_y'] = 'Y Axis'
        else:
            self.cal_left_y_btn.config(text="Calibrate Left Y")
            self.cal_right_y_btn.pack(before=self.clear_calib_btn, pady=2)
            self.axis_labels['left_y'] = 'Left Y'
        self.replot()

    def toggle_cursors(self):
        if getattr(self, 'show_cursors_var', None) and self.show_cursors_var.get():
            self._create_cursors()
        else:
            self._remove_cursors()
        self.plot_canvas.draw_idle()
        
    def _create_cursors(self):
        self._remove_cursors()
        
        self.cursors_v = {}
        self.cursors_h = {}
        self.cursor_annots = {}
        
        axes_to_add = []
        separate = getattr(self, 'separate_graphs_var', None) and self.separate_graphs_var.get()
        if separate and hasattr(self, 'axes_list') and self.axes_list:
            axes_to_add = self.axes_list
        else:
            if getattr(self, 'ax1', None): axes_to_add = [self.ax1]
            elif getattr(self, 'ax2', None): axes_to_add = [self.ax2]
            
        if not axes_to_add: return
            
        import numpy as np
        
        main_ax = axes_to_add[0]
        xlim = main_ax.get_xlim()
        x_pos = np.sqrt(xlim[0] * xlim[1]) if (self.calibrator.calibrations.get('X', {}).get('is_log') and xlim[0]>0 and xlim[1]>0) else (xlim[0] + xlim[1]) / 2.0
        
        for ax in axes_to_add:
            ylim = ax.get_ylim()
            is_right = (ax == getattr(self, 'ax2', None))
            y_key = 'Right Y' if is_right else 'Left Y'
            is_log_y = self.calibrator.calibrations.get(y_key, {}).get('is_log')
            y_pos = np.sqrt(ylim[0] * ylim[1]) if (is_log_y and ylim[0]>0 and ylim[1]>0) else (ylim[0] + ylim[1]) / 2.0
            
            cv = ax.axvline(x_pos, color='magenta', linestyle='--', linewidth=2, picker=5)
            self.cursors_v[ax] = cv
            
            ch = ax.axhline(y_pos, color='magenta', linestyle='--', linewidth=2, picker=5)
            self.cursors_h[ax] = ch
            
            annot = ax.annotate("", xy=(x_pos, y_pos), xytext=(10, 10), 
                                textcoords='offset points',
                                bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="b", lw=1, alpha=0.8))
            self.cursor_annots[ax] = annot
            
        self._update_cursor_annot()
        
    def _remove_cursors(self):
        if hasattr(self, 'cursors_v'):
            for cv in self.cursors_v.values():
                try: cv.remove()
                except Exception: pass
            self.cursors_v = {}
        if hasattr(self, 'cursors_h'):
            for ch in self.cursors_h.values():
                try: ch.remove()
                except Exception: pass
            self.cursors_h = {}
        if hasattr(self, 'cursor_annots'):
            for annot in self.cursor_annots.values():
                try: annot.remove()
                except Exception: pass
            self.cursor_annots = {}
            
        for c in ['cursor_v', 'cursor_h', 'cursor_annot']:
            if getattr(self, c, None):
                try: getattr(self, c).remove()
                except Exception: pass
                setattr(self, c, None)
            
    def _update_cursor_annot(self):
        if not hasattr(self, 'cursors_v') or not self.cursors_v: return
        try:
            import numpy as np
            first_cv = list(self.cursors_v.values())[0]
            x_pos = first_cv.get_xdata()
            if isinstance(x_pos, (list, tuple, np.ndarray)): x_pos = x_pos[0]
            
            separate = getattr(self, 'separate_graphs_var', None) and self.separate_graphs_var.get()
            
            if separate:
                for ax, annot in self.cursor_annots.items():
                    if ax in self.cursors_h and ax in self.cursors_v:
                        curr_x_pos = self.cursors_v[ax].get_xdata()
                        if isinstance(curr_x_pos, (list, tuple, np.ndarray)): curr_x_pos = curr_x_pos[0]
                        
                        y_pos = self.cursors_h[ax].get_ydata()
                        if isinstance(y_pos, (list, tuple, np.ndarray)): y_pos = y_pos[0]
                        annot.xy = (curr_x_pos, y_pos)
                        annot.set_text(f"X: {curr_x_pos:.4g}\nY: {y_pos:.4g}")
            else:
                ax = self.ax1 if self.ax1 else self.ax2
                if ax in self.cursor_annots and ax in self.cursors_h and ax in self.cursors_v:
                    annot = self.cursor_annots[ax]
                    
                    curr_x_pos = self.cursors_v[ax].get_xdata()
                    if isinstance(curr_x_pos, (list, tuple, np.ndarray)): curr_x_pos = curr_x_pos[0]
                    
                    y_pos = self.cursors_h[ax].get_ydata()
                    if isinstance(y_pos, (list, tuple, np.ndarray)): y_pos = y_pos[0]
                    annot.xy = (curr_x_pos, y_pos)
                    
                    text = f"X: {curr_x_pos:.4g}\nLeft Y: {y_pos:.4g}"
                    if getattr(self, 'ax2', None) is not None and getattr(self, 'ax1', None) is not None:
                        disp_coords = self.ax1.transData.transform((curr_x_pos, y_pos))
                        ax2_coords = self.ax2.transData.inverted().transform(disp_coords)
                        text += f"\nRight Y: {ax2_coords[1]:.4g}"
                    elif getattr(self, 'ax2', None) is not None and getattr(self, 'ax1', None) is None:
                        text = f"X: {curr_x_pos:.4g}\nRight Y: {y_pos:.4g}"
                    annot.set_text(text)
        except Exception:
            pass

    def on_plot_press(self, event):
        if not event.inaxes: return
        
        self.dragging = None
        self.dragging_h_ax = None
        self.dragging_v_ax = None
        
        cursor_handled = False
        if getattr(self, 'show_cursors_var', None) and self.show_cursors_var.get():
            if hasattr(self, 'cursors_v'):
                for ax, cv in self.cursors_v.items():
                    contains, _ = cv.contains(event)
                    if contains:
                        self.dragging = 'v'
                        self.dragging_v_ax = ax
                        cursor_handled = True
                        break
            if not cursor_handled and hasattr(self, 'cursors_h'):
                for ax, ch in self.cursors_h.items():
                    contains, _ = ch.contains(event)
                    if contains:
                        self.dragging = 'h'
                        self.dragging_h_ax = ax
                        cursor_handled = True
                        break
                        
        if cursor_handled: return
        
        if hasattr(self, 'extractor') and getattr(self.extractor, 'curves', None) and event.button == 1:
            import numpy as np
            min_dist = float('inf')
            closest_curve = None
            closest_pt = None
            
            for ax in getattr(self, 'axes_list', []):
                if event.inaxes != ax: continue
                for line in ax.lines:
                    label = line.get_label()
                    if label and label in self.extractor.curves:
                        xdata, ydata = line.get_xdata(), line.get_ydata()
                        if len(xdata) == 0: continue
                        
                        try:
                            pts = np.column_stack((xdata, ydata))
                            disp_pts = ax.transData.transform(pts)
                            click_disp = ax.transData.transform((event.xdata, event.ydata))
                            
                            dists = np.sqrt(np.sum((disp_pts - click_disp)**2, axis=1))
                            idx = np.argmin(dists)
                            
                            if dists[idx] < 15 and dists[idx] < min_dist:
                                min_dist = dists[idx]
                                closest_curve = label
                                closest_pt = (xdata[idx], ydata[idx])
                        except Exception:
                            pass
                            
            if not hasattr(self, 'click_annots'):
                self.click_annots = []
                
            for ann in self.click_annots:
                try: ann.remove()
                except Exception: pass
            self.click_annots.clear()
                
            if closest_curve and closest_pt:
                def format_sci(val):
                    if val == 0: return "0"
                    s = f"{val:.4g}"
                    if 'e' not in s: return s
                    base, exp = s.split('e')
                    exp = int(exp)
                    if exp == 0: return base
                    return f"{base} x 10^{exp}"
                    
                x_str, y_str = format_sci(closest_pt[0]), format_sci(closest_pt[1])
                
                fig_w, fig_h = self.fig.bbox.width, self.fig.bbox.height
                x_offset = -70 if event.x > fig_w * 0.8 else 15
                y_offset = -45 if event.y > fig_h * 0.8 else 15
                
                ann = event.inaxes.annotate(f"{closest_curve}\nX: {x_str}\nY: {y_str}", 
                                      xy=closest_pt, xytext=(x_offset, y_offset), 
                                      textcoords="offset points",
                                      bbox=dict(boxstyle="round4", fc="lightyellow", alpha=0.9, ec="black"),
                                      arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2", color="black"),
                                      fontsize=9, weight='bold', clip_on=False)
                self.click_annots.append(ann)
            
            self.plot_canvas.draw()
            
    def on_plot_release(self, event):
        self.dragging = None
        self.dragging_h_ax = None
        self.dragging_v_ax = None

    def on_plot_mouse_move(self, event):
        if event.inaxes:
            self.coord_label.config(text=f"Cursor [X: {event.xdata:.4g} , Y: {event.ydata:.4g}]")
            if getattr(self, 'dragging', None):
                sync_mode = getattr(self, 'cursor_sync_var', tk.StringVar(value="X Only")).get()
                
                if self.dragging == 'v' and hasattr(self, 'cursors_v'):
                    if sync_mode in ["X Only", "Both"]:
                        for ax, cv in self.cursors_v.items():
                            cv.set_xdata([event.xdata, event.xdata])
                    else:
                        ax = getattr(self, 'dragging_v_ax', None)
                        if ax and ax in self.cursors_v:
                            x_val = event.xdata
                            if event.inaxes != ax:
                                ax_coord = ax.transData.inverted().transform((event.x, event.y))
                                x_val = ax_coord[0]
                            self.cursors_v[ax].set_xdata([x_val, x_val])
                            
                elif self.dragging == 'h' and hasattr(self, 'cursors_h'):
                    ax_dragged = getattr(self, 'dragging_h_ax', None)
                    if sync_mode in ["Y Only", "Both"]:
                        for ax, ch in self.cursors_h.items():
                            ch.set_ydata([event.ydata, event.ydata])
                    else:
                        if ax_dragged and ax_dragged in self.cursors_h:
                            y_val = event.ydata
                            if event.inaxes != ax_dragged:
                                ax_coord = ax_dragged.transData.inverted().transform((event.x, event.y))
                                y_val = ax_coord[1]
                            self.cursors_h[ax_dragged].set_ydata([y_val, y_val])
                            
                self._update_cursor_annot()
                self.plot_canvas.draw_idle()
        else:
            self.coord_label.config(text="Cursor [X: -- , Y: --]")

    def set_status(self, text):
        self.status_var.set(f"Status:\n{text}")
        
    def load_pdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not filepath: return
        self.set_status("Extracting PDF pages at 300 DPI...\nThis may take a moment.")
        self.root.update()
        try:
            self.images = load_pdf_images(filepath)
            self.page_combo['values'] = [img[0] for img in self.images]
            if self.images:
                self.page_combo.current(0)
                self.on_page_change(None)
            self.set_status(f"Loaded {len(self.images)} pages successfully.\nProceed to CALIBRATION.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF: {e}")
            self.set_status("Idle")
            
    def load_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not filepath: return
        self.set_status("Loading CSV data...")
        self.root.update()
        try:
            import pandas as pd
            import numpy as np
            df = pd.read_csv(filepath)
            
            cols = df.columns.tolist()
            new_curves = {}
            
            has_x_suffix = any(c.endswith('_X') for c in cols)
            if has_x_suffix:
                for col in cols:
                    if col.endswith('_X'):
                        base_name = col[:-2]
                        y_col = f"{base_name}_Y"
                        if y_col in cols:
                            x_data = df[col].dropna().values
                            y_data = df[y_col].dropna().values
                            if len(x_data) > 0 and len(y_data) > 0:
                                new_curves[base_name] = {
                                    'x': x_data,
                                    'y': y_data,
                                    'y_axis': 'Left Y'
                                }
            else:
                if len(cols) >= 2:
                    x_col = cols[0]
                    x_data = df[x_col].dropna().values
                    for y_col in cols[1:]:
                        y_data = df[y_col].dropna().values
                        min_len = min(len(x_data), len(y_data))
                        if min_len > 0:
                            new_curves[y_col] = {
                                'x': x_data[:min_len],
                                'y': y_data[:min_len],
                                'y_axis': 'Left Y'
                            }
                            
            if not new_curves:
                raise ValueError("Could not find valid X/Y data columns in the CSV.")
                
            # Pop up dialog to configure axes and curves
            dialog = tk.Toplevel(self.root)
            dialog.title("CSV Data Configuration")
            dialog.geometry("450x500")
            dialog.transient(self.root)
            dialog.grab_set()
            
            tk.Label(dialog, text="Configure Axes:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))
            
            num_y_axes_var = tk.StringVar(value="1")
            frame_y_axes = tk.Frame(dialog)
            frame_y_axes.pack(fill=tk.X, padx=10)
            tk.Label(frame_y_axes, text="Number of Y Axes:").pack(side=tk.LEFT)
            ttk.Radiobutton(frame_y_axes, text="1 (Left Y Only)", variable=num_y_axes_var, value="1", command=lambda: update_axes_ui()).pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(frame_y_axes, text="2 (Left & Right Y)", variable=num_y_axes_var, value="2", command=lambda: update_axes_ui()).pack(side=tk.LEFT, padx=5)
            
            x_log_var = tk.BooleanVar(value=False)
            left_y_log_var = tk.BooleanVar(value=False)
            right_y_log_var = tk.BooleanVar(value=False)
            
            log_frame = tk.Frame(dialog)
            log_frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Checkbutton(log_frame, text="X Axis Logarithmic", variable=x_log_var).pack(anchor=tk.W)
            tk.Checkbutton(log_frame, text="Left Y Axis Logarithmic", variable=left_y_log_var).pack(anchor=tk.W)
            right_y_check = tk.Checkbutton(log_frame, text="Right Y Axis Logarithmic", variable=right_y_log_var)
            
            def update_axes_ui():
                if num_y_axes_var.get() == "2":
                    right_y_check.pack(anchor=tk.W)
                    for combo in curve_combos:
                        combo['state'] = 'readonly'
                else:
                    right_y_check.pack_forget()
                    right_y_log_var.set(False)
                    for combo in curve_combos:
                        combo.set("Left Y")
                        combo['state'] = 'disabled'
            
            tk.Label(dialog, text="Assign Curves to Axes:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(15, 5))
            
            curves_frame = tk.Frame(dialog)
            curves_frame.pack(fill=tk.BOTH, expand=True, padx=10)
            
            # Add scrollbar if there are many curves
            canvas = tk.Canvas(curves_frame)
            scrollbar = tk.Scrollbar(curves_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            curve_combos = []
            curve_vars = []
            for name in new_curves.keys():
                row = tk.Frame(scrollable_frame)
                row.pack(fill=tk.X, pady=2)
                # Ensure long names don't break the UI
                display_name = name if len(name) < 30 else name[:27] + "..."
                tk.Label(row, text=display_name, width=30, anchor=tk.W).pack(side=tk.LEFT)
                var = tk.StringVar(value="Left Y")
                curve_vars.append((name, var))
                combo = ttk.Combobox(row, textvariable=var, values=["Left Y", "Right Y"], state="disabled", width=10)
                combo.pack(side=tk.LEFT)
                curve_combos.append(combo)
                
            update_axes_ui()
            
            dialog_result = {'proceed': False}
            
            def on_submit():
                dialog_result['proceed'] = True
                dialog.destroy()
                
            tk.Button(dialog, text="Apply & Plot", command=on_submit, width=20, bg="#4CAF50", fg="white").pack(pady=15)
            
            self.root.wait_window(dialog)
            
            if not dialog_result['proceed']:
                self.set_status("CSV loading cancelled.")
                return
                
            # Apply user choices
            self.calibrator.calibrations['X'] = {'is_log': x_log_var.get()}
            self.calibrator.calibrations['Left Y'] = {'is_log': left_y_log_var.get()}
            if num_y_axes_var.get() == "2":
                self.calibrator.calibrations['Right Y'] = {'is_log': right_y_log_var.get()}
                self.single_y_var.set(False)
                self.on_single_y_toggle()
            else:
                if 'Right Y' in self.calibrator.calibrations:
                    del self.calibrator.calibrations['Right Y']
                self.single_y_var.set(True)
                self.on_single_y_toggle()
                
            for name, var in curve_vars:
                new_curves[name]['y_axis'] = var.get()

            self.extractor.curves.clear()
            self.extractor.curves.update(new_curves)
            
            self.replot()
            self.set_status(f"Loaded {len(new_curves)} curves from CSV successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")
            self.set_status("Idle")
            
    def on_page_change(self, event):
        idx = self.page_combo.current()
        if idx < 0: return
        self.current_image_cv = self.images[idx][1].copy()
        self.zoom_fit()
        
    def update_image_display(self):
        if self.current_image_cv is None: return
        
        width = int(self.current_image_cv.shape[1] * self.zoom_factor)
        height = int(self.current_image_cv.shape[0] * self.zoom_factor)
        if width < 10 or height < 10: return
        dim = (width, height)
        
        interp = cv2.INTER_AREA if self.zoom_factor < 1.0 else cv2.INTER_CUBIC
        resized = cv2.resize(self.current_image_cv, dim, interpolation=interp)
        
        rgb_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        self.image_photo = ImageTk.PhotoImage(image=pil_img)
        
        self.img_canvas.delete("all")
        self.img_canvas.create_image(0, 0, image=self.image_photo, anchor=tk.NW)
        self.img_canvas.config(scrollregion=self.img_canvas.bbox(tk.ALL))

    def zoom_in(self):
        if self.current_image_cv is None: return
        self.zoom_factor *= 1.2
        self.update_image_display()
        
    def zoom_out(self):
        if self.current_image_cv is None: return
        self.zoom_factor /= 1.2
        self.update_image_display()
        
    def zoom_fit(self):
        if self.current_image_cv is None: return
        self.root.update_idletasks()
        canvas_width = self.img_canvas.winfo_width()
        img_width = self.current_image_cv.shape[1]
        if canvas_width > 10 and img_width > 0:
            self.zoom_factor = (canvas_width - 10) / img_width
        else:
            self.zoom_factor = 0.3
        self.update_image_display()

    def _get_scroll_amt(self, event):
        if getattr(event, 'num', 0) == 4: return -1
        if getattr(event, 'num', 0) == 5: return 1
        if getattr(event, 'delta', 0) > 0: return -1
        if getattr(event, 'delta', 0) < 0: return 1
        return 0

    def on_mouse_wheel_y(self, event):
        amt = self._get_scroll_amt(event)
        self.img_canvas.yview_scroll(amt, "units")

    def on_mouse_wheel_x(self, event):
        amt = self._get_scroll_amt(event)
        self.img_canvas.xview_scroll(amt, "units")

    def on_mouse_wheel_zoom(self, event):
        if self.current_image_cv is None: return
        amt = self._get_scroll_amt(event)
        if amt < 0:
            self.zoom_factor *= 1.1
        elif amt > 0:
            self.zoom_factor /= 1.1
        self.update_image_display()

    def start_calibration(self, axis):
        if self.current_image_cv is None: return
        self.state = f'calib|{axis}|1'
        self.temp_points = []
        display_axis = "Y" if axis == 'Left Y' and hasattr(self, 'single_y_var') and self.single_y_var.get() else axis
        self.set_status(f"ACTION REQUIRED:\nClick the FIRST reference point directly on the {display_axis} axis in the image above.")
        
    def clear_calibration(self):
        self.calibrator.calibrations.clear()
        self.extractor.curves.clear()
        self.state = 'idle'
        self.temp_points = []
        self.fig.clear()
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = None
        self.plot_canvas.draw()
        
        if hasattr(self, 'images') and self.images:
            idx = self.page_combo.current()
            if idx >= 0:
                self.current_image_cv = self.images[idx][1].copy()
                self.update_image_display()
                
        self.set_status("Calibrations and curves cleared.")
        
    def _snap_to_tick(self, axis, px, py):
        import numpy as np
        h, w = self.current_image_cv.shape[:2]
        gray = cv2.cvtColor(self.current_image_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        window = 10
        x_start = max(0, px - window)
        x_end = min(w, px + window + 1)
        y_start = max(0, py - window)
        y_end = min(h, py + window + 1)
        
        roi = thresh[y_start:y_end, x_start:x_end]
        if roi.size == 0: return px, py
        
        if axis == 'X':
            col_sums = np.sum(roi, axis=0)
            best_local_x = np.argmax(col_sums)
            if col_sums[best_local_x] > 0:
                return x_start + best_local_x, py
        else:
            row_sums = np.sum(roi, axis=1)
            best_local_y = np.argmax(row_sums)
            if row_sums[best_local_y] > 0:
                return px, y_start + best_local_y
        return px, py

    def on_canvas_click(self, event):
        if self.current_image_cv is None: return
        x = self.img_canvas.canvasx(event.x)
        y = self.img_canvas.canvasy(event.y)
        px, py = int(x / self.zoom_factor), int(y / self.zoom_factor)
        
        h, w = self.current_image_cv.shape[:2]
        px = max(0, min(px, w - 1))
        py = max(0, min(py, h - 1))
        
        if self.state.startswith('calib|'):
            parts = self.state.split('|')
            axis = parts[1]
            step = parts[2]
            
            px, py = self._snap_to_tick(axis, px, py)
            
            # Draw visual feedback
            radius = max(3, int(5 / self.zoom_factor))
            cv2.circle(self.current_image_cv, (px, py), radius, (0, 0, 255), -1)
            self.update_image_display()
            
            if step == '1':
                self.temp_points.append(px if axis == 'X' else py)
                self.state = f'calib|{axis}|2'
                display_axis = "Y" if axis == 'Left Y' and hasattr(self, 'single_y_var') and self.single_y_var.get() else axis
                self.set_status(f"ACTION REQUIRED:\nClick the SECOND reference point on the {display_axis} axis.")
            elif step == '2':
                self.temp_points.append(px if axis == 'X' else py)
                self.state = 'idle'
                self.prompt_calibration_values(axis)
                
        elif self.state == 'extract':
            self.state = 'idle'
            self.set_status("Extracting and smoothing curve...")
            self.root.update()
            try:
                self.extractor.extract_curve(self.temp_curve_info['name'], self.current_image_cv, px, py, self.temp_curve_info['axis'])
                self.replot()
                self.set_status("Extraction complete.\nYou can add more or Analyze.")
            except Exception as e:
                messagebox.showerror("Extraction Error", str(e))
                self.set_status("Idle")
                
    def prompt_calibration_values(self, axis):
        dialog = tk.Toplevel(self.root)
        title_axis = "Y Axis" if axis == 'Left Y' and hasattr(self, 'single_y_var') and self.single_y_var.get() else axis
        dialog.title(f"Calibrate {title_axis}")
        dialog.geometry("380x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Pixel 1:").grid(row=0, column=0, padx=5, pady=10)
        p1_entry = tk.Entry(dialog, width=8)
        p1_entry.insert(0, str(self.temp_points[0]))
        p1_entry.grid(row=0, column=1)
        
        tk.Label(dialog, text="Real Value 1:").grid(row=0, column=2, padx=5, pady=10)
        v1_entry = tk.Entry(dialog, width=12)
        v1_entry.grid(row=0, column=3)
        
        tk.Label(dialog, text="Pixel 2:").grid(row=1, column=0, padx=5, pady=10)
        p2_entry = tk.Entry(dialog, width=8)
        p2_entry.insert(0, str(self.temp_points[1]))
        p2_entry.grid(row=1, column=1)
        
        tk.Label(dialog, text="Real Value 2:").grid(row=1, column=2, padx=5, pady=10)
        v2_entry = tk.Entry(dialog, width=12)
        v2_entry.grid(row=1, column=3)
        
        log_var = tk.BooleanVar()
        tk.Checkbutton(dialog, text="Logarithmic Scale", variable=log_var).grid(row=2, columnspan=4)
        
        def submit():
            try:
                v1, v2 = float(v1_entry.get()), float(v2_entry.get())
                p1, p2 = int(p1_entry.get()), int(p2_entry.get())
                self.calibrator.calibrate_axis(axis, p1, p2, v1, v2, log_var.get())
                self.set_status(f"{axis} axis calibrated.")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid values entered.", parent=dialog)
                
        tk.Button(dialog, text="Apply Calibration", command=submit, width=20).grid(row=3, columnspan=4, pady=10)
        
    def start_extraction(self):
        if 'X' not in self.calibrator.calibrations:
            messagebox.showwarning("Error", "Calibrate the X Axis before extracting.")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Configure Curve")
        dialog.geometry("320x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Curve Name:").grid(row=0, column=0, padx=10, pady=10)
        name_entry = tk.Entry(dialog)
        name_entry.insert(0, f"Curve {len(self.extractor.curves)+1}")
        name_entry.grid(row=0, column=1)
        
        tk.Label(dialog, text="Target Y Axis:").grid(row=1, column=0, padx=10, pady=10)
        is_single = hasattr(self, 'single_y_var') and self.single_y_var.get()
        values = ["Y Axis"] if is_single else ["Left Y", "Right Y"]
        axis_var = tk.StringVar(value=values[0])
        ttk.Combobox(dialog, textvariable=axis_var, values=values, state="readonly").grid(row=1, column=1)
        
        def submit():
            target = axis_var.get()
            if target == "Y Axis":
                target = "Left Y"
            if target not in self.calibrator.calibrations:
                messagebox.showerror("Error", f"{target} is not calibrated yet.", parent=dialog)
                return
            self.temp_curve_info = {'name': name_entry.get(), 'axis': target}
            self.state = 'extract'
            self.set_status(f"ACTION REQUIRED:\nClick directly on the colored '{name_entry.get()}' line in the image.")
            dialog.destroy()
            
        tk.Button(dialog, text="Ready to Click", command=submit, width=15).grid(row=2, columnspan=2, pady=10)

    def replot(self):
        saved_limits = {}
        if getattr(self, 'ax1', None):
            saved_limits['ax1_xlim'] = self.ax1.get_xlim()
            saved_limits['ax1_ylim'] = self.ax1.get_ylim()
        if getattr(self, 'ax2', None):
            saved_limits['ax2_xlim'] = self.ax2.get_xlim()
            saved_limits['ax2_ylim'] = self.ax2.get_ylim()
            
        self.fig.clear()
        
        has_left = any('Left' in c['y_axis'] for c in self.extractor.curves.values())
        has_right = any('Right' in c['y_axis'] for c in self.extractor.curves.values())
        separate = hasattr(self, 'separate_graphs_var') and self.separate_graphs_var.get()
        
        n_curves = len(self.extractor.curves)
        self.axes_list = []
        ax_is_right = {}
        
        layout_mode = getattr(self, 'layout_var', tk.StringVar(value="Vertical")).get()
        
        if separate and n_curves > 0:
            import math
            if layout_mode == "Horizontal":
                rows, cols = 1, n_curves
            elif layout_mode == "Grid":
                cols = math.ceil(math.sqrt(n_curves))
                rows = math.ceil(n_curves / cols)
            else:
                rows, cols = n_curves, 1
                
            left_axes = []
            right_axes = []
            for i, (name, data) in enumerate(self.extractor.curves.items()):
                is_right = 'Right' in data['y_axis']
                sy = right_axes[0] if is_right and right_axes else (left_axes[0] if not is_right and left_axes else None)
                sx = self.axes_list[0] if i > 0 else None
                ax = self.fig.add_subplot(rows, cols, i+1, sharex=sx, sharey=sy)
                self.axes_list.append(ax)
                ax_is_right[ax] = is_right
                if is_right: right_axes.append(ax)
                else: left_axes.append(ax)
                
            self.ax1 = left_axes[0] if left_axes else None
            self.ax2 = right_axes[0] if right_axes else None
        else:
            if has_left and has_right and not separate:
                self.ax1 = self.fig.add_subplot(111)
                self.ax2 = self.ax1.twinx()
            elif has_left:
                self.ax1 = self.fig.add_subplot(111)
                self.ax2 = None
            elif has_right:
                self.ax1 = None
                self.ax2 = self.fig.add_subplot(111)
            else:
                self.ax1 = self.fig.add_subplot(111)
                self.ax2 = None
                
            if self.ax1: 
                self.axes_list.append(self.ax1)
                ax_is_right[self.ax1] = False
            if self.ax2: 
                self.axes_list.append(self.ax2)
                ax_is_right[self.ax2] = True
                
        colors = [
            'tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple',
            'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan',
            'navy', 'gold', 'crimson', 'teal', 'magenta'
        ]
        
        for idx, (name, data) in enumerate(self.extractor.curves.items()):
            if 'color' not in data:
                data['color'] = colors[idx % len(colors)]
            if 'linestyle' not in data:
                data['linestyle'] = '--' if 'Right' in data['y_axis'] else '-'
                
            color = data['color']
            ls = data['linestyle']
            
            target_ax = self.axes_list[idx] if separate and n_curves > 0 else (self.ax2 if 'Right' in data['y_axis'] else self.ax1)
            
            if target_ax is not None:
                target_ax.plot(data['x'], data['y'], label=name, color=color, linestyle=ls, linewidth=2)
                
                import numpy as np
                if 'peaks' in data and data['peaks']:
                    px = np.array(data['x'])[data['peaks']]
                    py = np.array(data['y'])[data['peaks']]
                    target_ax.plot(px, py, '^', color='green', markersize=8)
                    for px_val, py_val in zip(px, py):
                        target_ax.annotate(f"{py_val:.2f}", (px_val, py_val), textcoords="offset points", xytext=(0,5), ha='center', color='green', fontsize=8)
                        
                if 'valleys' in data and data['valleys']:
                    vx = np.array(data['x'])[data['valleys']]
                    vy = np.array(data['y'])[data['valleys']]
                    target_ax.plot(vx, vy, 'v', color='red', markersize=8)
                    for vx_val, vy_val in zip(vx, vy):
                        target_ax.annotate(f"{vy_val:.2f}", (vx_val, vy_val), textcoords="offset points", xytext=(0,-12), ha='center', color='red', fontsize=8)
                
        gs = getattr(self, 'grid_style', '-')
        for i, ax in enumerate(self.axes_list):
            is_right = ax_is_right.get(ax, False)
            y_key = 'Right Y' if is_right else 'Left Y'
            
            if 'X' in self.calibrator.calibrations and self.calibrator.calibrations['X']['is_log']:
                ax.set_xscale('log')
            if y_key in self.calibrator.calibrations and self.calibrator.calibrations[y_key]['is_log']:
                ax.set_yscale('log')
                
            if gs != 'None':
                ax.grid(True, which='major', linestyle=gs, alpha=0.5)
                ax.grid(True, which='minor', linestyle=':' if gs == '-' else gs, alpha=0.3)
            else:
                ax.grid(False)
                
            label_key = 'right_y' if is_right else 'left_y'
            ax.set_ylabel(self.axis_labels[label_key])
            
            if not separate or n_curves <= 1 or layout_mode in ["Horizontal", "Grid"]:
                ax.set_xlabel(self.axis_labels['x'])
                ax.tick_params(labelbottom=True)
            else:
                if i == len(self.axes_list) - 1:
                    ax.set_xlabel(self.axis_labels['x'])
                else:
                    ax.tick_params(labelbottom=False)
                
            if hasattr(self, 'plot_bg_color'):
                ax.set_facecolor(self.plot_bg_color)
                
        from matplotlib.ticker import MultipleLocator
        try:
            for ax in self.axes_list:
                if getattr(self, 'grid_spacing_x', ''):
                    ax.xaxis.set_major_locator(MultipleLocator(float(self.grid_spacing_x)))
                
                is_right = ax_is_right.get(ax, False)
                spacing_key = 'grid_spacing_ry' if is_right else 'grid_spacing_ly'
                if getattr(self, spacing_key, ''):
                    ax.yaxis.set_major_locator(MultipleLocator(float(getattr(self, spacing_key))))
        except Exception:
            pass
            
        self.draggable_legends = []
        if separate:
            for ax in self.axes_list:
                leg = ax.legend(loc='upper right', framealpha=0.9)
                if leg: 
                    d_leg = leg.set_draggable(True)
                    self.draggable_legends.append(d_leg)
        else:
            handles, labels = [], []
            if getattr(self, 'ax1', None):
                h, l = self.ax1.get_legend_handles_labels()
                handles.extend(h)
                labels.extend(l)
            if getattr(self, 'ax2', None):
                h, l = self.ax2.get_legend_handles_labels()
                handles.extend(h)
                labels.extend(l)
                
            if handles:
                target_legend_ax = self.ax2 if getattr(self, 'ax2', None) else self.ax1
                if target_legend_ax:
                    leg = target_legend_ax.legend(handles, labels, loc='upper left', framealpha=0.9)
                    if leg: 
                        d_leg = leg.set_draggable(True)
                        self.draggable_legends.append(d_leg)
            
        self.fig.tight_layout()
        
        if hasattr(self, 'plot_bg_color'):
            self.fig.patch.set_facecolor(self.plot_bg_color)
                
        if getattr(self, 'show_cursors_var', None) and self.show_cursors_var.get():
            self._create_cursors()
            
        if 'ax1_xlim' in saved_limits and getattr(self, 'ax1', None):
            try:
                self.ax1.set_xlim(saved_limits['ax1_xlim'])
                self.ax1.set_ylim(saved_limits['ax1_ylim'])
            except Exception: pass
        if 'ax2_xlim' in saved_limits and getattr(self, 'ax2', None):
            try:
                self.ax2.set_xlim(saved_limits['ax2_xlim'])
                self.ax2.set_ylim(saved_limits['ax2_ylim'])
            except Exception: pass
            
        self.plot_canvas.draw()
        
    def smooth_curves(self):
        if not self.extractor.curves:
            messagebox.showwarning("Warning", "No curves to smooth.")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Smooth Curves")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Window Length (odd):").pack(pady=5)
        window_entry = tk.Entry(dialog)
        window_entry.insert(0, "11")
        window_entry.pack()
        
        tk.Label(dialog, text="Polynomial Order:").pack(pady=5)
        poly_entry = tk.Entry(dialog)
        poly_entry.insert(0, "3")
        poly_entry.pack()
        
        def apply():
            try:
                from scipy.signal import savgol_filter
                w = int(window_entry.get())
                p = int(poly_entry.get())
                if w % 2 == 0: w += 1
                for name, data in self.extractor.curves.items():
                    if len(data['y']) > w:
                        data['y'] = savgol_filter(data['y'], w, p)
                self.replot()
                self.set_status("Curves smoothed using Savitzky-Golay filter.")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to smooth: {e}")
                
        tk.Button(dialog, text="Apply", command=apply).pack(pady=10)

    def resample_curves(self):
        if not self.extractor.curves:
            messagebox.showwarning("Warning", "No curves to resample.")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Resample Curves")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Number of Points:").pack(pady=5)
        pts_entry = tk.Entry(dialog)
        pts_entry.insert(0, "500")
        pts_entry.pack()
        
        def apply():
            try:
                import numpy as np
                from scipy.interpolate import interp1d
                n_pts = int(pts_entry.get())
                
                for name, data in self.extractor.curves.items():
                    x, y = np.array(data['x']), np.array(data['y'])
                    sort_idx = np.argsort(x)
                    x, y = x[sort_idx], y[sort_idx]
                    
                    x_unique, unique_idx = np.unique(x, return_index=True)
                    y_unique = y[unique_idx]
                    
                    if len(x_unique) < 2: continue
                    
                    is_log = False
                    if 'X' in self.calibrator.calibrations and self.calibrator.calibrations['X']['is_log']:
                        is_log = True
                        
                    if is_log and x_unique[0] > 0 and x_unique[-1] > 0:
                        new_x = np.logspace(np.log10(x_unique[0]), np.log10(x_unique[-1]), n_pts)
                    else:
                        new_x = np.linspace(x_unique[0], x_unique[-1], n_pts)
                        
                    f = interp1d(x_unique, y_unique, kind='linear', fill_value="extrapolate")
                    new_y = f(new_x)
                    
                    data['x'] = new_x
                    data['y'] = new_y
                    
                self.replot()
                self.set_status(f"Resampled all curves to {n_pts} points.")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to resample: {e}")
                
        tk.Button(dialog, text="Apply", command=apply).pack(pady=10)

    def find_peaks(self):
        if not self.extractor.curves: return
        
        try:
            from scipy.signal import find_peaks
            import numpy as np
            
            for name, data in self.extractor.curves.items():
                y = np.array(data['y'])
                x = np.array(data['x'])
                
                peaks, _ = find_peaks(y, prominence=np.ptp(y)*0.05) 
                valleys, _ = find_peaks(-y, prominence=np.ptp(y)*0.05)
                
                if 'peaks' not in data: data['peaks'] = []
                data['peaks'] = peaks.tolist()
                
                if 'valleys' not in data: data['valleys'] = []
                data['valleys'] = valleys.tolist()
                
            self.replot()
            self.set_status("Found peaks and valleys.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to find peaks: {e}")
            
    def rename_curve(self):
        if not self.extractor.curves: return
        dialog = tk.Toplevel(self.root)
        dialog.title("Rename Curve")
        dialog.geometry("300x150")
        tk.Label(dialog, text="Select Curve:").pack(pady=5)
        curve_var = tk.StringVar(value=list(self.extractor.curves.keys())[0])
        ttk.Combobox(dialog, textvariable=curve_var, values=list(self.extractor.curves.keys()), state="readonly").pack()
        tk.Label(dialog, text="New Name:").pack(pady=5)
        name_entry = tk.Entry(dialog)
        name_entry.pack()
        def apply():
            old = curve_var.get()
            new = name_entry.get()
            if new and old in self.extractor.curves and new not in self.extractor.curves:
                self.extractor.curves[new] = self.extractor.curves.pop(old)
                self.replot()
                dialog.destroy()
        tk.Button(dialog, text="Rename", command=apply).pack(pady=10)

    def delete_curve(self):
        if not self.extractor.curves: return
        dialog = tk.Toplevel(self.root)
        dialog.title("Delete Curve")
        dialog.geometry("300x120")
        tk.Label(dialog, text="Select Curve:").pack(pady=5)
        curve_var = tk.StringVar(value=list(self.extractor.curves.keys())[0])
        ttk.Combobox(dialog, textvariable=curve_var, values=list(self.extractor.curves.keys()), state="readonly").pack()
        def apply():
            target = curve_var.get()
            if target in self.extractor.curves:
                del self.extractor.curves[target]
                self.replot()
                dialog.destroy()
        tk.Button(dialog, text="Delete", command=apply).pack(pady=10)

    def math_curve(self):
        if not self.extractor.curves: return
        dialog = tk.Toplevel(self.root)
        dialog.title("Shift / Scale Curve")
        dialog.geometry("300x250")
        tk.Label(dialog, text="Select Curve:").pack()
        curve_var = tk.StringVar(value=list(self.extractor.curves.keys())[0])
        ttk.Combobox(dialog, textvariable=curve_var, values=list(self.extractor.curves.keys()), state="readonly").pack(pady=5)
        
        f = tk.Frame(dialog)
        f.pack(pady=5)
        tk.Label(f, text="X Multiplier:").grid(row=0, column=0)
        x_scale = tk.Entry(f, width=10); x_scale.insert(0, "1")
        x_scale.grid(row=0, column=1)
        tk.Label(f, text="X Offset:").grid(row=0, column=2)
        x_off = tk.Entry(f, width=10); x_off.insert(0, "0")
        x_off.grid(row=0, column=3)
        
        tk.Label(f, text="Y Multiplier:").grid(row=1, column=0)
        y_scale = tk.Entry(f, width=10); y_scale.insert(0, "1")
        y_scale.grid(row=1, column=1)
        tk.Label(f, text="Y Offset:").grid(row=1, column=2)
        y_off = tk.Entry(f, width=10); y_off.insert(0, "0")
        y_off.grid(row=1, column=3)
        
        def apply():
            try:
                import numpy as np
                target = curve_var.get()
                if target in self.extractor.curves:
                    xs, xo = float(x_scale.get()), float(x_off.get())
                    ys, yo = float(y_scale.get()), float(y_off.get())
                    self.extractor.curves[target]['x'] = np.array(self.extractor.curves[target]['x']) * xs + xo
                    self.extractor.curves[target]['y'] = np.array(self.extractor.curves[target]['y']) * ys + yo
                    self.replot()
                    dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        tk.Button(dialog, text="Apply", command=apply).pack(pady=10)

    def curve_stats(self):
        if not self.extractor.curves: return
        dialog = tk.Toplevel(self.root)
        dialog.title("Curve Statistics")
        dialog.geometry("300x250")
        tk.Label(dialog, text="Select Curve:").pack(pady=5)
        curve_var = tk.StringVar(value=list(self.extractor.curves.keys())[0])
        cb = ttk.Combobox(dialog, textvariable=curve_var, values=list(self.extractor.curves.keys()), state="readonly")
        cb.pack()
        
        stats_label = tk.Label(dialog, text="", justify=tk.LEFT, font=("Courier", 10))
        stats_label.pack(pady=10)
        
        def update_stats(*args):
            try:
                import numpy as np
                target = curve_var.get()
                if target in self.extractor.curves:
                    y = np.array(self.extractor.curves[target]['y'])
                    x = np.array(self.extractor.curves[target]['x'])
                    
                    if len(y) == 0: return
                    vmin, vmax = np.min(y), np.max(y)
                    mean = np.mean(y)
                    rms = np.sqrt(np.mean(y**2))
                    ptp = vmax - vmin
                    
                    try:
                        area = np.trapezoid(y, x) if len(x) > 1 else 0
                    except AttributeError:
                        area = np.trapz(y, x) if len(x) > 1 else 0
                    
                    text = f"Points: {len(y)}\n"
                    text += f"Min Y: {vmin:.4g}\n"
                    text += f"Max Y: {vmax:.4g}\n"
                    text += f"Peak-to-Peak: {ptp:.4g}\n"
                    text += f"Mean Y: {mean:.4g}\n"
                    text += f"RMS Y: {rms:.4g}\n"
                    text += f"Area: {area:.4g}"
                    stats_label.config(text=text)
            except Exception as e:
                stats_label.config(text=f"Error computing stats:\n{e}")
        
        cb.bind("<<ComboboxSelected>>", update_stats)
        update_stats()

    def diff_curves(self):
        if len(self.extractor.curves) < 2:
            messagebox.showwarning("Warning", "Need at least 2 curves.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Calculate Difference")
        dialog.geometry("300x250")
        
        tk.Label(dialog, text="Curve A:").pack(pady=2)
        var_a = tk.StringVar(value=list(self.extractor.curves.keys())[0])
        ttk.Combobox(dialog, textvariable=var_a, values=list(self.extractor.curves.keys()), state="readonly").pack()
        
        tk.Label(dialog, text="Curve B (to subtract):").pack(pady=2)
        var_b = tk.StringVar(value=list(self.extractor.curves.keys())[1])
        ttk.Combobox(dialog, textvariable=var_b, values=list(self.extractor.curves.keys()), state="readonly").pack()
        
        tk.Label(dialog, text="New Curve Name:").pack(pady=2)
        name_entry = tk.Entry(dialog)
        name_entry.insert(0, "Difference")
        name_entry.pack()
        
        def apply():
            try:
                import numpy as np
                from scipy.interpolate import interp1d
                ca = var_a.get()
                cb = var_b.get()
                nname = name_entry.get()
                if not nname or ca == cb: return
                
                xa, ya = np.array(self.extractor.curves[ca]['x']), np.array(self.extractor.curves[ca]['y'])
                xb, yb = np.array(self.extractor.curves[cb]['x']), np.array(self.extractor.curves[cb]['y'])
                
                # Resample B to A's x grid where they overlap
                xmin = max(np.min(xa), np.min(xb))
                xmax = min(np.max(xa), np.max(xb))
                
                mask = (xa >= xmin) & (xa <= xmax)
                new_x = xa[mask]
                new_ya = ya[mask]
                
                if len(new_x) == 0:
                    messagebox.showwarning("Warning", "Curves do not overlap on X axis.")
                    return
                
                fb = interp1d(xb, yb, kind='linear')
                new_yb = fb(new_x)
                
                diff_y = new_ya - new_yb
                
                self.extractor.curves[nname] = {
                    'x': new_x,
                    'y': diff_y,
                    'y_axis': self.extractor.curves[ca]['y_axis']
                }
                self.replot()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
        tk.Button(dialog, text="Calculate", command=apply).pack(pady=10)
            
    def analyze(self):
        res = analyze_bode(self.extractor.curves)
        if 'error' in res:
            messagebox.showwarning("Analysis Error", res['error'])
            return
            
        self.replot()  # Wipe any previous annotations from the plot before drawing new ones
            
        info = "Bode Analysis Results:\n\n"
        
        def format_sci(val):
            if val == 0: return "0"
            s = f"{val:.2e}"
            base, exp = s.split('e')
            exp = int(exp)
            if exp == 0: return base
            return f"{base} x 10^{exp}"
        
        annot_mode = getattr(self, 'bode_annot_var', tk.StringVar(value="Both")).get()
        
        # Phase Margin (Red)
        for r in res['results']:
            freq_str = format_sci(r['crossover_freq'])
            info += f"Phase Margin: {r['phase_margin']:.2f}° (at {freq_str})\n"
            
            if annot_mode in ["Both", "Only PM"]:
                if hasattr(self, 'axes_list') and self.axes_list:
                    for ax in self.axes_list:
                        if ax: ax.axvline(r['crossover_freq'], color='r', linestyle='-.', alpha=0.8)
                else:
                    if self.ax1 is not None: self.ax1.axvline(r['crossover_freq'], color='r', linestyle='-.', alpha=0.8)
                    if self.ax2 is not None: self.ax2.axvline(r['crossover_freq'], color='r', linestyle='-.', alpha=0.8)
                
                phase_name = res.get('phase_name')
                phase_ax = None
                if hasattr(self, 'axes_list') and self.axes_list:
                    for idx, (name, _) in enumerate(self.extractor.curves.items()):
                        if name == phase_name and idx < len(self.axes_list):
                            phase_ax = self.axes_list[idx]
                            break
                if not phase_ax: phase_ax = self.ax2

                if phase_ax is not None:
                    phase_ax.plot(r['crossover_freq'], r['curve_y'], 'ro', markersize=8, markeredgecolor='black')
                    phase_ax.annotate(f" PM: {r['phase_margin']:.1f}°", (r['crossover_freq'], r['curve_y']), color='red', weight='bold')

        info += "\n"
        
        # Gain Margin (Blue)
        for r in res.get('results_gm', []):
            freq_str = format_sci(r['phase_crossover_freq'])
            info += f"Gain Margin: {r['gain_margin']:.2f} dB (at {freq_str})\n"
            
            if annot_mode in ["Both", "Only GM"]:
                if hasattr(self, 'axes_list') and self.axes_list:
                    for ax in self.axes_list:
                        if ax: ax.axvline(r['phase_crossover_freq'], color='b', linestyle=':', alpha=0.8)
                else:
                    if self.ax1 is not None: self.ax1.axvline(r['phase_crossover_freq'], color='b', linestyle=':', alpha=0.8)
                    if self.ax2 is not None: self.ax2.axvline(r['phase_crossover_freq'], color='b', linestyle=':', alpha=0.8)
                
                gain_name = res.get('gain_name')
                gain_ax = None
                if hasattr(self, 'axes_list') and self.axes_list:
                    for idx, (name, _) in enumerate(self.extractor.curves.items()):
                        if name == gain_name and idx < len(self.axes_list):
                            gain_ax = self.axes_list[idx]
                            break
                if not gain_ax: gain_ax = self.ax1

                if gain_ax is not None:
                    # Assuming Gain Margin = 0 - Gain. So Gain = -GM
                    gain_val = -r['gain_margin']
                    gain_ax.plot(r['phase_crossover_freq'], gain_val, 'bo', markersize=8, markeredgecolor='black')
                    gain_ax.annotate(f" GM: {r['gain_margin']:.1f} dB", (r['phase_crossover_freq'], gain_val), color='blue', weight='bold')
        
        self.plot_canvas.draw()
        messagebox.showinfo("Bode Analysis Results", info)
        
    def set_plot_limits(self):
        if not self.ax1 and not self.ax2: return
        dialog = tk.Toplevel(self.root)
        dialog.title("Set Export Limits")
        dialog.geometry("300x350" if self.ax1 and self.ax2 else "300x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_ax = self.ax1 if self.ax1 else self.ax2
        xlim = main_ax.get_xlim()
        
        tk.Label(dialog, text="X Min:").grid(row=0, column=0, padx=5, pady=5)
        x_min_entry = tk.Entry(dialog, width=15)
        x_min_entry.insert(0, f"{xlim[0]:.4g}")
        x_min_entry.grid(row=0, column=1)
        
        tk.Label(dialog, text="X Max:").grid(row=1, column=0, padx=5, pady=5)
        x_max_entry = tk.Entry(dialog, width=15)
        x_max_entry.insert(0, f"{xlim[1]:.4g}")
        x_max_entry.grid(row=1, column=1)

        current_row = 2
        
        if self.ax1:
            ylim1 = self.ax1.get_ylim()
            label_prefix = "Left Y" if self.ax2 else "Y"
            tk.Label(dialog, text=f"{label_prefix} Min:").grid(row=current_row, column=0, padx=5, pady=5)
            y_min_entry = tk.Entry(dialog, width=15)
            y_min_entry.insert(0, f"{ylim1[0]:.4g}")
            y_min_entry.grid(row=current_row, column=1)
            current_row += 1
            
            tk.Label(dialog, text=f"{label_prefix} Max:").grid(row=current_row, column=0, padx=5, pady=5)
            y_max_entry = tk.Entry(dialog, width=15)
            y_max_entry.insert(0, f"{ylim1[1]:.4g}")
            y_max_entry.grid(row=current_row, column=1)
            current_row += 1

        if self.ax2:
            ylim2 = self.ax2.get_ylim()
            label_prefix = "Right Y" if self.ax1 else "Y"
            tk.Label(dialog, text=f"{label_prefix} Min:").grid(row=current_row, column=0, padx=5, pady=5)
            y2_min_entry = tk.Entry(dialog, width=15)
            y2_min_entry.insert(0, f"{ylim2[0]:.4g}")
            y2_min_entry.grid(row=current_row, column=1)
            current_row += 1
            
            tk.Label(dialog, text=f"{label_prefix} Max:").grid(row=current_row, column=0, padx=5, pady=5)
            y2_max_entry = tk.Entry(dialog, width=15)
            y2_max_entry.insert(0, f"{ylim2[1]:.4g}")
            y2_max_entry.grid(row=current_row, column=1)
            current_row += 1
            
        def apply():
            try:
                xmin, xmax = float(x_min_entry.get()), float(x_max_entry.get())
                if self.ax1:
                    self.ax1.set_xlim(xmin, xmax)
                    ymin, ymax = float(y_min_entry.get()), float(y_max_entry.get())
                    self.ax1.set_ylim(ymin, ymax)
                if self.ax2:
                    self.ax2.set_xlim(xmin, xmax)
                    y2min, y2max = float(y2_min_entry.get()), float(y2_max_entry.get())
                    self.ax2.set_ylim(y2min, y2max)
                self.plot_canvas.draw()
                self.set_status("Export limits updated.")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid limit values.", parent=dialog)
                
        def reset():
            if self.ax1: self.ax1.autoscale()
            if self.ax2: self.ax2.autoscale()
            self.plot_canvas.draw()
            dialog.destroy()
            
        tk.Button(dialog, text="Apply", command=apply, width=10).grid(row=current_row, column=0, pady=10)
        tk.Button(dialog, text="Auto / Reset", command=reset, width=12).grid(row=current_row, column=1, pady=10)

    def open_plot_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Plot Settings")
        dialog.geometry("350x650")
        dialog.transient(self.root)
        dialog.grab_set()
        
        color_options = [
            'tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan',
            'blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 'black', 'white',
            'navy', 'darkblue', 'royalblue', 'deepskyblue', 'teal', 'darkcyan', 'darkgreen', 'forestgreen', 'limegreen',
            'gold', 'yellow', 'darkorange', 'tomato', 'firebrick', 'crimson', 'magenta', 'indigo', 'darkorchid', 'darkviolet',
            'violet', 'hotpink', 'salmon', 'sienna', 'chocolate', 'saddlebrown', 'maroon', 'darkgray', 'silver', 'lightgray'
        ]
        
        # --- Axis Labels ---
        tk.Label(dialog, text="Axis Labels & Appearance", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        
        frame_axes = tk.Frame(dialog)
        frame_axes.pack(fill=tk.X, padx=20)
        
        tk.Label(frame_axes, text="X Axis:").grid(row=0, column=0, sticky=tk.W, pady=2)
        x_entry = tk.Entry(frame_axes, width=25)
        x_entry.insert(0, self.axis_labels['x'])
        x_entry.grid(row=0, column=1, pady=2, padx=5)
        
        tk.Label(frame_axes, text="Left Y Axis:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ly_entry = tk.Entry(frame_axes, width=25)
        ly_entry.insert(0, self.axis_labels['left_y'])
        ly_entry.grid(row=1, column=1, pady=2, padx=5)
        
        tk.Label(frame_axes, text="Right Y Axis:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ry_entry = tk.Entry(frame_axes, width=25)
        ry_entry.insert(0, self.axis_labels['right_y'])
        ry_entry.grid(row=2, column=1, pady=2, padx=5)
        
        tk.Label(frame_axes, text="Background:").grid(row=3, column=0, sticky=tk.W, pady=2)
        bg_var = tk.StringVar(value=getattr(self, 'plot_bg_color', 'white'))
        bg_combo = ttk.Combobox(frame_axes, textvariable=bg_var, values=color_options, width=22)
        bg_combo.grid(row=3, column=1, pady=2, padx=5)
        
        # --- Grid Settings ---
        tk.Label(dialog, text="Grid Settings", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        frame_grid = tk.Frame(dialog)
        frame_grid.pack(fill=tk.X, padx=20)
        
        tk.Label(frame_grid, text="Grid Style:").grid(row=0, column=0, sticky=tk.W, pady=2)
        grid_style_var = tk.StringVar(value=getattr(self, 'grid_style', '-'))
        grid_style_combo = ttk.Combobox(frame_grid, textvariable=grid_style_var, values=['-', '--', '-.', ':', 'None'], width=10, state='readonly')
        grid_style_combo.grid(row=0, column=1, pady=2, padx=5, sticky=tk.W)
        
        tk.Label(frame_grid, text="X Spacing:").grid(row=1, column=0, sticky=tk.W, pady=2)
        grid_x_var = tk.StringVar(value=getattr(self, 'grid_spacing_x', ''))
        grid_x_entry = tk.Entry(frame_grid, textvariable=grid_x_var, width=12)
        grid_x_entry.grid(row=1, column=1, pady=2, padx=5, sticky=tk.W)
        
        tk.Label(frame_grid, text="Left Y Spacing:").grid(row=2, column=0, sticky=tk.W, pady=2)
        grid_ly_var = tk.StringVar(value=getattr(self, 'grid_spacing_ly', ''))
        grid_ly_entry = tk.Entry(frame_grid, textvariable=grid_ly_var, width=12)
        grid_ly_entry.grid(row=2, column=1, pady=2, padx=5, sticky=tk.W)
        
        tk.Label(frame_grid, text="Right Y Spacing:").grid(row=3, column=0, sticky=tk.W, pady=2)
        grid_ry_var = tk.StringVar(value=getattr(self, 'grid_spacing_ry', ''))
        grid_ry_entry = tk.Entry(frame_grid, textvariable=grid_ry_var, width=12)
        grid_ry_entry.grid(row=3, column=1, pady=2, padx=5, sticky=tk.W)
        
        # --- Curve Styles ---
        tk.Label(dialog, text="Curve Styles", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        frame_curves = tk.Frame(dialog)
        frame_curves.pack(fill=tk.BOTH, expand=True, padx=20)
        
        tk.Label(frame_curves, text="Curve").grid(row=0, column=0, sticky=tk.W, padx=2)
        tk.Label(frame_curves, text="Color").grid(row=0, column=1, padx=2)
        tk.Label(frame_curves, text="Line").grid(row=0, column=2, padx=2)
        
        curve_vars = {}
        for idx, (name, data) in enumerate(self.extractor.curves.items()):
            row = idx + 1
            tk.Label(frame_curves, text=f"{name[:10]}:").grid(row=row, column=0, sticky=tk.W, pady=2)
            
            c_var = tk.StringVar(value=data.get('color', 'tab:blue'))
            c_combo = ttk.Combobox(frame_curves, textvariable=c_var, values=color_options, width=12)
            c_combo.grid(row=row, column=1, padx=2)
            
            ls_var = tk.StringVar(value=data.get('linestyle', '-'))
            ls_combo = ttk.Combobox(frame_curves, textvariable=ls_var, values=['-', '--', '-.', ':'], width=5, state='readonly')
            ls_combo.grid(row=row, column=2, padx=2)
            
            curve_vars[name] = (c_var, ls_var)
            
        if not self.extractor.curves:
            tk.Label(frame_curves, text="No curves extracted yet.").grid(row=1, column=0, columnspan=3, pady=10)
            
        def apply():
            self.axis_labels['x'] = x_entry.get()
            self.axis_labels['left_y'] = ly_entry.get()
            self.axis_labels['right_y'] = ry_entry.get()
            self.plot_bg_color = bg_var.get()
            self.grid_style = grid_style_var.get()
            self.grid_spacing_x = grid_x_var.get()
            self.grid_spacing_ly = grid_ly_var.get()
            self.grid_spacing_ry = grid_ry_var.get()
            
            for name, (c_var, ls_var) in curve_vars.items():
                self.extractor.curves[name]['color'] = c_var.get()
                self.extractor.curves[name]['linestyle'] = ls_var.get()
                
            self.replot()
            self.set_status("Plot settings updated.")
            dialog.destroy()
            
        tk.Button(dialog, text="Apply Settings", command=apply, width=15, bg="#4CAF50", fg="white").pack(pady=20)

    def export_csv(self):
        if not self.extractor.curves: return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="digitized_data.csv")
        if filepath:
            if self.ax1 is not None:
                xlim = self.ax1.get_xlim()
                filtered_curves = {}
                import numpy as np
                for name, data in self.extractor.curves.items():
                    mask = (data['x'] >= min(xlim)) & (data['x'] <= max(xlim))
                    filtered_curves[name] = {
                        'x': data['x'][mask],
                        'y': data['y'][mask],
                        'y_axis': data['y_axis']
                    }
                export_to_csv(filtered_curves, filepath)
            else:
                export_to_csv(self.extractor.curves, filepath)
            self.set_status("Data exported successfully.")
            
    def export_png(self):
        if not self.extractor.curves: return
        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")], initialfile="clean_plot.png")
        if filepath:
            orig_size = self.fig.get_size_inches()
            self.fig.set_size_inches(16, 12)
            self.fig.savefig(filepath, dpi=400, bbox_inches='tight')
            self.fig.set_size_inches(orig_size[0], orig_size[1])
            self.plot_canvas.draw()
            self.set_status("High-res plot exported successfully.")

    def export_pdf(self):
        if not self.extractor.curves: return
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile="clean_plot.pdf")
        if filepath:
            orig_size = self.fig.get_size_inches()
            self.fig.set_size_inches(16, 12)
            self.fig.savefig(filepath, dpi=400, bbox_inches='tight')
            self.fig.set_size_inches(orig_size[0], orig_size[1])
            self.plot_canvas.draw()
            self.set_status("High-res plot exported to PDF successfully.")
