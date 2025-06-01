import itertools
import numpy as np
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class LPVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Графическое исследование ЗЛП (проекция)")
        self.root.minsize(500,250)
        self.setup_screen = ttk.Frame(root, borderwidth = 1, relief =  "solid")
        self.setup_screen.place(relx=0.1, rely=0.1, anchor="nw", relwidth=0.8, relheight=0.8)
        
        ttk.Label(self.setup_screen, text="Введите количество переменных:", font=("Arial", 15)).pack(pady=10)
        
        self.var_count_input = tk.IntVar(value=2)
        var_selector = ttk.Spinbox(self.setup_screen, from_=1, to=10, textvariable=self.var_count_input, width=5)
        var_selector.pack(pady=10)
        
        self.use_visualization = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.setup_screen, text="С отрисовкой", variable=self.use_visualization).pack(pady=5)
        
        ttk.Button(self.setup_screen, text="Продолжить", command=self.initialize_solver).pack(pady=10)
        
        self.main_frame = None


    def initialize_solver(self):
        self.setup_screen.destroy()
        
        self.var_count = self.var_count_input.get()
        self.visualization_mode = self.use_visualization.get()
        
        self.main_frame = ttk.Frame(self.root, borderwidth = 1, relief =  "solid")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.input_frame = ttk.Frame(self.main_frame, borderwidth = 1, relief =  "solid")
        self.input_frame.place( relx=0.78, rely=0.05, relwidth=0.2, relheight=0.9)
        
        if self.visualization_mode:
            self.plot_frame = ttk.Frame(self.main_frame,borderwidth = 1, relief =  "solid")
            self.plot_frame.place( relx=0.05, rely=0.05, relwidth=0.7, relheight=0.9)
        
        self.extra_var_count = tk.IntVar(value=0)
        self.step_size = tk.DoubleVar(value=0.5)
        self.mode = tk.StringVar(value="Максимум")
        
        self.constraints_widgets = []
        self.vertices = []
        self.current_point = None
        self.manual_mode = False
        self.edge_path = []
        
        self.objective_coeffs = []
        self.fixed_values = []
        
        self.setup_ui()
        #self.update_objective_entries()

    def setup_ui(self):
        title_text = "Графическое решение" if self.visualization_mode else "Аналитическое решение"
        ttk.Label(self.input_frame, text=title_text, font=("Arial", 12)).pack(pady=10)
        
        objective_frame = ttk.LabelFrame(self.input_frame, text="Целевая функция",borderwidth = 1, relief =  "solid")
        objective_frame.pack(fill=tk.X, padx=5, pady=5)
        self.objective_container = ttk.Frame(objective_frame)
        self.objective_container.pack()
        
        mode_frame = ttk.Frame(objective_frame)
        mode_frame.pack(pady=5)
        ttk.Radiobutton(mode_frame, text="Максимум", variable=self.mode, value="Максимум").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Минимум", variable=self.mode, value="Минимум").pack(side=tk.LEFT)

        constraints_frame = ttk.LabelFrame(self.input_frame, text="Ограничения")
        constraints_frame.pack(fill=tk.X, padx=5, pady=5)
        self.constraints_container = ttk.Frame(constraints_frame)
        self.constraints_container.pack()
        ttk.Button(constraints_frame, text="Добавить ограничение", command=self.add_constraint).pack(pady=5)

        if self.visualization_mode:
            step_frame = ttk.LabelFrame(self.input_frame, text="Шаг перемещения")
            step_frame.pack(fill=tk.X, padx=5, pady=5)
            ttk.Entry(step_frame, textvariable=self.step_size, width=10).pack()

        self.info_label = ttk.Label(self.input_frame, text="Решение не найдено")
        self.info_label.pack(pady=10)

        control_frame = ttk.Frame(self.input_frame)
        control_frame.pack(pady=5)
        
        if self.visualization_mode:
            ttk.Button(control_frame, text="Обновить график", command=self.plot_constraints).pack(fill=tk.X, pady=2)
            ttk.Button(control_frame, text="Автоматический расчёт", command=self.solve).pack(fill=tk.X, pady=2)
            ttk.Button(control_frame, text="Ручной расчёт", command=self.start_manual_mode).pack(fill=tk.X, pady=2)
        else:
            ttk.Button(control_frame, text="Решить задачу", command=self.solve_analytical).pack(fill=tk.X, pady=2)
            
        ttk.Button(control_frame, text="Сбросить всё", command=self.reset_all).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Новая задача", command=self.new_problem).pack(fill=tk.X, pady=2)

        if self.visualization_mode:
            self.fig, self.ax = plt.subplots()
            self.ax.set_xlabel("x1")
            self.ax.set_ylabel("x2")
            self.ax.grid(True, linestyle='--', linewidth=0.5)
            self.ax.axhline(0, color='black', linewidth=1)
            self.ax.axvline(0, color='black', linewidth=1)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)
            
            self.root.bind("<Up>", self.move_up)
            self.root.bind("<Down>", self.move_down)

if __name__ == "__main__":
    root = tk.Tk()
    app = LPVisualizer(root)
    root.mainloop()