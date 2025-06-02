import itertools
import numpy as np
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# TODO: перевести систему ограничений в ограничения типа равенства

class LPVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Графическое исследование ЗЛП (проекция)")
        
        self.setup_screen = ttk.Frame(root)
        self.setup_screen.pack(padx=20, pady=20)
        
        ttk.Label(self.setup_screen, text="Введите количество переменных:", font=("Arial", 12)).pack(pady=10)
        
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
        
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)
        
        if self.visualization_mode:
            self.plot_frame = ttk.Frame(self.main_frame)
            self.plot_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
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
        
        objective_frame = ttk.LabelFrame(self.input_frame, text="Целевая функция")
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
        self.ax.grid(True, linestyle='--', linewidth=0.5)
        self.ax.axhline(0, color='black', linewidth=1)
        self.ax.axvline(0, color='black', linewidth=1)

        constraints = self.read_constraints()
        x = np.linspace(-20, 20, 400)
        y_min, y_max = -20, 20
        self.vertices = []

        for a, sign, b in constraints:
            a1, a2 = a[:2]
            rhs = b - sum(ak * vk.get() for ak, vk in zip(a[2:], self.fixed_values))
            
            if abs(a2) > 1e-8:
                y = (rhs - a1 * x) / a2
                self.ax.plot(x, y, 'b--')
                if sign == "<=":
                    if a2 > 0:
                        self.ax.fill_between(x, y, y_min, color="blue", alpha=0.1)
                    else:
                        self.ax.fill_between(x, y, y_max, color="blue", alpha=0.1)
                elif sign == ">=":
                    if a2 > 0:
                        self.ax.fill_between(x, y, y_max, color="blue", alpha=0.1)
                    else:
                        self.ax.fill_between(x, y, y_min, color="blue", alpha=0.1)
            elif abs(a1) > 1e-8:
                x_val = rhs / a1
                self.ax.plot([x_val, x_val], [y_min, y_max], 'b--')
                if sign == "<=":
                    if a1 > 0:
                        self.ax.fill_betweenx(np.linspace(y_min, y_max, 400), -100, x_val, color="blue", alpha=0.1)
                    else:
                        self.ax.fill_betweenx(np.linspace(y_min, y_max, 400), x_val, 100, color="blue", alpha=0.1)
                elif sign == ">=":
                    if a1 > 0:
                        self.ax.fill_betweenx(np.linspace(y_min, y_max, 400), x_val, 100, color="blue", alpha=0.1)
                    else:
                        self.ax.fill_betweenx(np.linspace(y_min, y_max, 400), -100, x_val, color="blue", alpha=0.1)

        for comb in itertools.combinations(constraints, 2):
            a1, s1, b1 = comb[0]
            a2, s2, b2 = comb[1]
            A = np.array([a1[:2], a2[:2]])
            rhs1 = b1 - sum(ak * vk.get() for ak, vk in zip(a1[2:], self.fixed_values))
            rhs2 = b2 - sum(ak * vk.get() for ak, vk in zip(a2[2:], self.fixed_values))
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
        if not self.vertices:
            self.info_label.config(text="Нет допустимых вершин")
            return
            
        if len(self.vertices) == 1:
            self.current_point = self.vertices[0]
            full_point = list(self.current_point) + [vk.get() for vk in self.fixed_values]
            z = sum(c.get() * x for c, x in zip(self.objective_coeffs, full_point))
            point_str = ", ".join(f"{x:.2f}" for x in full_point)
            self.info_label.config(text=f"x = ({point_str})\nЦелевая функция = {z:.2f}")
            self.plot_constraints()
            return
            
        if len(self.vertices) == 2:
            self.edge_path = self.vertices
            self.edge_index = 0
            self.current_point = self.edge_path[0]
            self.update_info()
            self.plot_constraints()
            return
            
        poly = Polygon(self.vertices)
        if not poly.is_valid:
            poly = poly.convex_hull
        self.edge_path = list(poly.exterior.coords)[:-1]
        self.edge_index = 0
        self.current_point = self.edge_path[0]
        self.update_info()
        self.plot_constraints()

    def move_up(self, event):
        if self.manual_mode:
            self.move_along_edge(1)

    def move_down(self, event):
        if self.manual_mode:
            self.move_along_edge(-1)

    def move_along_edge(self, direction):
        if not self.edge_path or self.current_point is None:
            return
        step = self.step_size.get()
        p1 = np.array(self.current_point)
        next_idx = (self.edge_index + direction) % len(self.edge_path)
        p2 = np.array(self.edge_path[next_idx])
        edge_vector = p2 - p1
        length = np.linalg.norm(edge_vector)
        if length < 1e-8:
            return
        dir_vector = edge_vector / length
        new_point = p1 + dir_vector * step
        if np.linalg.norm(new_point - p2) < step:
            self.edge_index = next_idx
            new_point = p2
        full_point = list(new_point) + [vk.get() for vk in self.fixed_values]
        if self.is_feasible(full_point):
            self.current_point = tuple(new_point)
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

    def solve_analytical(self):
        constraints = self.read_constraints()
        if not constraints:
            self.info_label.config(text="Нет ограничений")
            return
            
        is_maximization = self.mode.get() == "Максимум"
        obj_coeffs = [coeff.get() for coeff in self.objective_coeffs]
        
        if len(constraints) < self.var_count:
            try:
                dual_result = self.solve_dual_problem(obj_coeffs, constraints, is_maximization)
                if dual_result["status"] == "optimal":
                    solution_str = "Решение двойственной задачи:\n"
                    for i, val in enumerate(dual_result["y"]):
                        solution_str += f"y{i+1} = {val:.4f}\n"
                    solution_str += f"\nЗначение целевой функции = {dual_result['objective_value']:.4f}"
                    self.info_label.config(text=solution_str)
                else:
                    self.info_label.config(text=f"Не удалось найти решение:\n{dual_result['status']}")
            except Exception as e:
                self.info_label.config(text=f"Ошибка при решении двойственной задачи:\n{str(e)}")
            return
        
        ineq_constraints = []
        eq_constraints = []
        geq_constraints = []
        
        for coeffs, sign, rhs in constraints:
            if sign == "<=":
                ineq_constraints.append((coeffs, rhs))
            elif sign == "=":
                eq_constraints.append((coeffs, rhs))
            elif sign == ">=":
                geq_constraints.append((coeffs, rhs))
        
        try:
            result = self.simplex_method(obj_coeffs, ineq_constraints, eq_constraints, geq_constraints, is_maximization)
            
            if result["status"] == "optimal":
                solution_str = "Оптимальное решение:\n"
                for i, val in enumerate(result["x"]):
                    solution_str += f"x{i+1} = {val:.4f}\n"
                    
                solution_str += f"\nЗначение целевой функции = {result['objective_value']:.4f}"
                
                self.info_label.config(text=solution_str)
            else:
                self.info_label.config(text=f"Не удалось найти решение:\n{result['status']}")
        except Exception as e:
            self.info_label.config(text=f"Ошибка при решении задачи:\n{str(e)}")

    def solve_dual_problem(self, obj_coeffs, constraints, is_maximization):
        A = np.array([c for c, _, _ in constraints])
        b = np.array([b for _, _, b in constraints])
        dual_obj_coeffs = b.tolist()
        dual_constraints = []
        for i in range(len(obj_coeffs)):
            coeffs = A[:, i].tolist()
            dual_constraints.append((coeffs, '>=', obj_coeffs[i]))
        ineq_constraints = [ (c, rhs) for c, sign, rhs in dual_constraints if sign == '>=']
        eq_constraints = []
        geq_constraints = []
        result = self.simplex_method(dual_obj_coeffs, ineq_constraints, eq_constraints, geq_constraints, False)
        if result["status"] == "optimal":
            return {
                "status": "optimal",
                "y": result["x"],
                "objective_value": result["objective_value"]
            }
        else:
            return {
                "status": result["status"],
                "y": None,
                "objective_value": None
            }

    def simplex_method(self, obj_coeffs, ineq_constraints, eq_constraints, geq_constraints, is_maximization):
        num_vars = len(obj_coeffs)
        max_iterations = 100
        
        c = obj_coeffs.copy()
        if not is_maximization:
            c = [-coef for coef in c]
            
        num_slack_vars = len(ineq_constraints)
        num_surplus_vars = len(geq_constraints)
        num_artificial_vars = len(eq_constraints) + num_surplus_vars
        
        total_vars = num_vars + num_slack_vars + num_surplus_vars + num_artificial_vars
        
        num_constraints = len(ineq_constraints) + len(eq_constraints) + len(geq_constraints)
        tableau = np.zeros((num_constraints + 1, total_vars + 1))
        
        tableau[0, :num_vars] = [-v for v in c]
        
        M = 1000
        artificial_start = num_vars + num_slack_vars + num_surplus_vars
        if num_artificial_vars > 0:
            tableau[0, artificial_start:artificial_start + num_artificial_vars] = [M] * num_artificial_vars
        
        row = 1
        
        for i, (coeffs, rhs) in enumerate(ineq_constraints):
            tableau[row, :num_vars] = coeffs
            tableau[row, num_vars + i] = 1
            tableau[row, -1] = rhs
            row += 1
        
        for i, (coeffs, rhs) in enumerate(eq_constraints):
            tableau[row, :num_vars] = coeffs
            artificial_idx = artificial_start + i
            tableau[row, artificial_idx] = 1
            tableau[row, -1] = rhs
            row += 1
        
        for i, (coeffs, rhs) in enumerate(geq_constraints):
            tableau[row, :num_vars] = coeffs
            surplus_idx = num_vars + num_slack_vars + i
            tableau[row, surplus_idx] = -1
            artificial_idx = artificial_start + len(eq_constraints) + i
            tableau[row, artificial_idx] = 1
            tableau[row, -1] = rhs
            row += 1
        
        for i in range(num_artificial_vars):
            artificial_idx = artificial_start + i
            for j in range(1, num_constraints + 1):
                if tableau[j, artificial_idx] == 1:
                    tableau[0, :] -= M * tableau[j, :]
                    break
        
        iterations = 0
        while iterations < max_iterations:
            pivot_col = np.argmin(tableau[0, :-1])
            if tableau[0, pivot_col] >= -1e-10:
                break
                
            ratios = []
            for i in range(1, num_constraints + 1):
                if tableau[i, pivot_col] > 1e-10:
                    ratio = tableau[i, -1] / tableau[i, pivot_col]
                    ratios.append((ratio, i))
                    
            if not ratios:
                return {"status": "unbounded", "x": None, "objective_value": None, "iterations": iterations}
                
            _, pivot_row = min(ratios)
            
            pivot_element = tableau[pivot_row, pivot_col]
            tableau[pivot_row, :] /= pivot_element
            
            for i in range(num_constraints + 1):
                if i != pivot_row:
                    factor = tableau[i, pivot_col]
                    tableau[i, :] -= factor * tableau[pivot_row, :]
                    
            iterations += 1
        
        solution = np.zeros(num_vars)
        for j in range(num_vars):
            is_basic = True
            basic_row = -1
            
            for i in range(1, num_constraints + 1):
                if abs(tableau[i, j]) > 1e-10:
                    if abs(tableau[i, j] - 1) < 1e-10 and basic_row == -1:
                        basic_row = i
                    else:
                        is_basic = False
                        break
                        
            if is_basic and basic_row != -1:
                solution[j] = tableau[basic_row, -1]
        
        direct_obj_value = sum(obj_coeffs[i] * solution[i] for i in range(len(solution)))
        
        for j in range(artificial_start, artificial_start + num_artificial_vars):
            for i in range(1, num_constraints + 1):
                if abs(tableau[i, j] - 1) < 1e-10 and abs(tableau[i, -1]) > 1e-10:
                    return {"status": "infeasible", "x": None, "objective_value": None, "iterations": iterations}
        
        return {
            "status": "optimal",
            "x": solution,
            "objective_value": direct_obj_value,
            "iterations": iterations,
            "tableau": tableau
        }

if __name__ == "__main__":
    root = tk.Tk()
    app = LPVisualizer(root)
    root.mainloop()