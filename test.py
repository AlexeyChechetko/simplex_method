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
        self.root.minsize(1000,250)
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
        self.input_frame.place( relx=0.71, rely=0.005, relwidth=0.287, relheight=0.987)
        
        if self.visualization_mode:
            self.plot_frame = ttk.Frame(self.main_frame,borderwidth = 1, relief =  "solid")
            self.plot_frame.place( relx=0.005, rely=0.005, relwidth=0.7, relheight=0.987)
        
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
        self.update_objective_entries() 

    def setup_ui(self):
        title_text = "Графическое решение" if self.visualization_mode else "Аналитическое решение"
        ttk.Label(self.input_frame, text=title_text, font=("Arial", 12)).pack(pady=10)
        
        objective_frame = ttk.Frame(self.input_frame,borderwidth = 1, relief =  "solid")
        objective_frame.pack(fill=tk.X, padx=5, pady=5)
        self.objective_container = ttk.Frame(objective_frame,borderwidth = 1, relief =  "solid")
        self.objective_container.pack()
        
        mode_frame = ttk.Frame(objective_frame)
        #ttk.Label(mode_frame , text="Целевая функция", font=("Arial", 12)).pack(pady=10)
        mode_frame.pack(pady=5)
        ttk.Radiobutton(mode_frame, text="Максимум", variable=self.mode, value="Максимум").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Минимум", variable=self.mode, value="Минимум").pack(side=tk.LEFT)

        constraints_frame = ttk.Frame(self.input_frame,borderwidth = 1, relief =  "solid" )
        constraints_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(constraints_frame , text="Ограничения", font=("Arial", 12)).pack(pady=10)

        self.constraints_container = ttk.Frame(constraints_frame)
        self.constraints_container.pack()
        ttk.Button(constraints_frame, text="Добавить ограничение", command=self.add_constraint).pack(pady=5)

        if self.visualization_mode:
            step_frame = ttk.LabelFrame(self.input_frame, text="Шаг перемещения")
            step_frame.pack(fill=tk.X, padx=5, pady=5)
            ttk.Entry(step_frame, textvariable=self.step_size, width=10).pack()

        self.info_label = ttk.Label(self.input_frame, text="Решение не найдено")
        self.info_label.pack(pady=10)

        control_frame = ttk.Frame(self.input_frame, borderwidth = 1, relief =  "solid")
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

    def update_objective_entries(self):
        for widget in self.objective_container.winfo_children():
            widget.destroy()

        if hasattr(self, 'fixed_container'):
            for widget in self.fixed_container.winfo_children():
                widget.destroy()
            self.fixed_container.destroy()
            self.fixed_container = None

        if self.visualization_mode and self.var_count > 2:
            if not hasattr(self, 'fixed_frame'):
                self.fixed_frame = ttk.LabelFrame(self.input_frame, text="Фиксируемые переменные")
                self.fixed_frame.pack(fill=tk.X, padx=5, pady=5)
            self.fixed_container = ttk.Frame(self.fixed_frame)
            self.fixed_container.pack()

        total_vars = self.var_count
        self.objective_coeffs = []
        self.fixed_values = []

        for i in range(total_vars):
            coeff = tk.DoubleVar()
            self.objective_coeffs.append(coeff)
            ttk.Entry(self.objective_container, textvariable=coeff, width=5).pack(side=tk.LEFT)
            if i < total_vars - 1:
                ttk.Label(self.objective_container, text=f"* x{i+1} +").pack(side=tk.LEFT)
            else:
                ttk.Label(self.objective_container, text=f"* x{i+1}").pack(side=tk.LEFT)

        if self.visualization_mode and total_vars > 2:
            for i in range(2, total_vars):
                frame = ttk.Frame(self.fixed_container)
                frame.pack(fill=tk.X, pady=2)
                val = tk.DoubleVar()
                self.fixed_values.append(val)
                ttk.Label(frame, text=f"x{i+1} = ").pack(side=tk.LEFT)
                ttk.Entry(frame, textvariable=val, width=8).pack(side=tk.LEFT)


    def add_constraint(self):
        frame = ttk.Frame(self.constraints_container)
        frame.pack(fill=tk.X, pady=2)
        vars_count = self.var_count
        coeffs = [tk.DoubleVar() for _ in range(vars_count)]
        for i, var in enumerate(coeffs):
            ttk.Entry(frame, textvariable=var, width=4).pack(side=tk.LEFT)
            ttk.Label(frame, text=f"x{i+1} ").pack(side=tk.LEFT)
            if i < vars_count - 1:
                ttk.Label(frame, text="+").pack(side=tk.LEFT)
        sign = tk.StringVar(value="<=")
        b = tk.DoubleVar()
        ttk.Combobox(frame, textvariable=sign, values=["<=", ">=", "="], width=3).pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=b, width=5).pack(side=tk.LEFT)
        ttk.Button(frame, text="X", command=lambda: self.remove_constraint(frame)).pack(side=tk.LEFT, padx=5)
        self.constraints_widgets.append((frame, coeffs, sign, b))


    def remove_constraint(self, frame):
        frame.destroy()
        self.constraints_widgets = [c for c in self.constraints_widgets if c[0] != frame]    


    def read_constraints(self):
        constraints = []
        for _, coeffs, sign_var, b_var in self.constraints_widgets:
            a = [v.get() for v in coeffs]
            constraints.append((a, sign_var.get(), b_var.get()))
        return constraints

    def plot_constraints(self):
        self.ax.clear()
        self.ax.set_xlabel("x1")
        self.ax.set_ylabel("x2")
        self.ax.grid(True, linestyle='-', linewidth=0.5)
        self.ax.axhline(0, color='black', linewidth=0.4)
        self.ax.axvline(0, color='black', linewidth=0.4)

        constraints = self.read_constraints()
        y_min, y_max = -20, 20
        x_min , x_max = -20, 20
        x = np.linspace(x_min, x_max, 400)
        
        x_grid,y_grid = np.meshgrid(x, np.linspace(y_min, y_max, 400))
        intersect = (x_grid==x_grid)

        self.vertices = []
        i = 1
        #draw constraints
        for a, sign, b in constraints:
            all_colors = ['b', 'g','blue' , 'c','y','k' ]
            
            color = all_colors[i]
            a1, a2 = int(a[0]) , int(a[1])
            rhs = int(b) - sum(ak * vk.get() for ak, vk in zip(a[2:], self.fixed_values))# right side of constraint
            
            if abs(a2) > 1e-8:
                y = (rhs - a1 * x) / a2
                self.ax.plot(x, y, color = color)

            elif abs(a1) > 1e-8:
                x_val = rhs / a1
                self.ax.axvline(x = x_val,ymin = y_min,  ymax = y_max )
            i += 1            
            if sign == "<=":
                intersect &= (a1 * x_grid + a2 * y_grid <= rhs)
            elif sign == ">=":
                intersect &= (a1 * x_grid + a2 * y_grid >= rhs)
            elif sign == "=":
                intersect &= (a1 * x_grid + a2 * y_grid == rhs)

        plt.imshow( intersect.astype(int) , extent=(x_grid.min(),x_grid.max(),y_grid.min(),y_grid.max()),origin="lower", cmap="Greys", alpha = 0.3)        
        #draw obj line 
        obj_coeffs = [v.get() for v in self.objective_coeffs]

        if self.current_point:

            full_point = list(self.current_point) + [vk.get() for vk in self.fixed_values]
            z = sum(c * x for c, x in zip(obj_coeffs, full_point))

            if  abs(obj_coeffs[1]) > 1e-8:
                y_obj = (z - obj_coeffs[0] * x)/obj_coeffs[1]
                self.ax.plot(x, y_obj, color= 'r')
            elif abs(obj_coeffs[0]) > 1e-8:
                x_obj = (z)/obj_coeffs[0]
                self.ax.axvline(x = x_obj,ymin = y_min,  ymax = y_max , color = 'r')

        # search interseption points
        for comb in itertools.combinations(constraints, 2):
            a_coefs1, _ , b_coef1 = comb[0] 
            a_coefs2, _ , b_coef2 = comb[1]
            A = np.array([a_coefs1[:2], a_coefs2[:2]])
            rhs1 = b_coef1 - sum(ak * vk.get() for ak, vk in zip(a_coefs1[2:], self.fixed_values))
            rhs2 = b_coef2 - sum(ak * vk.get() for ak, vk in zip(a_coefs2[2:], self.fixed_values))
            b_vec = np.array([rhs1, rhs2])
            if np.linalg.matrix_rank(A) == 2:
                try:
                    sol = np.linalg.solve(A, b_vec)
                    full_point = list(sol) + [vk.get() for vk in self.fixed_values]
                    if self.is_feasible(full_point):
                        self.vertices.append(tuple(sol))
                except Exception:
                    pass

        for vx, vy in self.vertices:
            self.ax.plot(vx, vy, 'ko')
            self.ax.text(vx + 0.3, vy + 0.3, f"({vx:.1f}, {vy:.1f})", fontsize=8)

        if self.current_point:
            self.ax.plot(self.current_point[0], self.current_point[1], 'ro', markersize=10)

        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.canvas.draw()   


    def is_feasible(self, point):
        for coeffs, sign, b in self.read_constraints():
            lhs = sum(a * x for a, x in zip(coeffs, point))
            if sign == "<=" and lhs > b + 1e-8:
                return False
            if sign == ">=" and lhs < b - 1e-8:
                return False
            if sign == "=" and abs(lhs - b) > 1e-8:
                return False
        return True      


    def solve(self):
        self.manual_mode = False
        self.plot_constraints()
        if not self.vertices:
            self.info_label.config(text="Нет допустимых вершин")
            return
        coeffs = [v.get() for v in self.objective_coeffs]
        values = []
        for v in self.vertices:
            full_point = list(v) + [vk.get() for vk in self.fixed_values]
            z = sum(c * x for c, x in zip(coeffs, full_point))
            values.append((z, v))
        best = max(values) if self.mode.get() == "Максимум" else min(values)
        self.current_point = best[1]
        self.update_info()
        self.plot_constraints() 

    def start_manual_mode(self):
        self.manual_mode = True
        self.plot_constraints()

        obj_coeffs = [v.get() for v in self.objective_coeffs]

        self.z_obj = 0
        if self.vertices:
            full_point = list(self.vertices[0]) + [vk.get() for vk in self.fixed_values]
            self.z_obj = sum(c * x for c, x in zip(obj_coeffs, full_point))
            self.current_point = self.vertices[0]
        
        self.update_info()
        self.plot_constraints()   


    def move_up(self, event):
        if self.manual_mode:
            self.move_line(1)

    def move_down(self, event):
        if self.manual_mode:
            self.move_line(-1)

    def move_line(self, dir):        
        self.z_obj = self.z_obj + dir* self.step_size.get()
        obj_coeffs = [v.get() for v in self.objective_coeffs]
        constraints = self.read_constraints()
        interseptions = []

        for constr in constraints:
            a_coefs, _ , b_coef = constr 

            A = np.array([a_coefs[:2], obj_coeffs[:2]])
            rhs1 = b_coef - sum(ak * vk.get() for ak, vk in zip(a_coefs[2:], self.fixed_values))
            rhs2 = self.z_obj - sum(ak * vk.get() for ak, vk in zip(obj_coeffs[2:], self.fixed_values))
            b_vec = np.array([rhs1, rhs2])
            if np.linalg.matrix_rank(A) == 2:
                try:
                    sol = np.linalg.solve(A, b_vec)
                    full_point = list(sol) + [vk.get() for vk in self.fixed_values]
                    if self.is_feasible(full_point):
                        interseptions.append( (sum(c * x for c, x in zip(obj_coeffs, full_point)),  tuple(sol)) )
                except Exception:
                    pass
        
        if interseptions:
            self.current_point = max(interseptions)[1] if self.mode.get() == "Максимум" else min(interseptions)[1]
        else:
            self.z_obj = self.z_obj - dir* self.step_size.get()
              
        
        self.update_info()
        self.plot_constraints()   



    def update_info(self):
        if not self.current_point:
            self.info_label.config(text="Решение не найдено")
        else:
            full_point = list(self.current_point) + [vk.get() for vk in self.fixed_values]
            z = sum(c.get() * x for c, x in zip(self.objective_coeffs, full_point))
            point_str = ", ".join(f"{x:.2f}" for x in full_point)
            self.info_label.config(text=f"x = ({point_str})\nЦелевая функция = {z:.2f}")    
    

    def reset_all(self):
        for frame, *_ in self.constraints_widgets:
            frame.destroy()
        self.constraints_widgets.clear()

        self.extra_var_count.set(0)
        self.update_objective_entries()

        self.vertices.clear()
        self.current_point = None
        self.manual_mode = False
        self.edge_path.clear()
        self.info_label.config(text="Решение не найдено")
        self.plot_constraints()   

    

    def on_scroll(self, event):
        base_scale = 1.1
        ax = self.ax

        xdata = event.xdata
        ydata = event.ydata

        if xdata is None or ydata is None:
            return

        scale_factor = base_scale if event.button == 'up' else 1 / base_scale

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        new_xlim = [
            xdata - (xdata - xlim[0]) * scale_factor,
            xdata + (xlim[1] - xdata) * scale_factor
        ]
        new_ylim = [
            ydata - (ydata - ylim[0]) * scale_factor,
            ydata + (ylim[1] - ydata) * scale_factor
        ]

        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)
        self.canvas.draw()   

    def new_problem(self):
        if self.main_frame:
            self.main_frame.destroy()
            
        self.setup_screen = ttk.Frame(self.root)
        self.setup_screen.pack(padx=20, pady=20)
        
        ttk.Label(self.setup_screen, text="Введите количество переменных:", font=("Arial", 12)).pack(pady=10)
        
        self.var_count_input = tk.IntVar(value=2)
        var_selector = ttk.Spinbox(self.setup_screen, from_=1, to=10, textvariable=self.var_count_input, width=5)
        var_selector.pack(pady=10)
        
        self.use_visualization = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.setup_screen, text="С отрисовкой", variable=self.use_visualization).pack(pady=5)
        
        ttk.Button(self.setup_screen, text="Продолжить", command=self.initialize_solver).pack(pady=10) 

if __name__ == "__main__":
    root = tk.Tk()
    app = LPVisualizer(root)
    root.mainloop()