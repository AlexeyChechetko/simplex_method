import numpy as np
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import traceback # Для детального вывода ошибок


class SimplexMethodCore:
    def __init__(self, epsilon=1e-9):
        self.epsilon = epsilon
        self.basis_vars_indices = [] 
        self.num_constraints = 0
        self.total_vars_in_tableau = 0 

    def _find_entering_variable_idx(self, tableau):
        obj_function_row = tableau[-1, :-1] 
        candidate_indices = []
        for j in range(len(obj_function_row)): 
            if obj_function_row[j] < -self.epsilon: 
                candidate_indices.append(j)
        if not candidate_indices: return None 
        return min(candidate_indices) 

    def _find_leaving_row_idx(self, tableau, entering_var_col_idx):
        min_ratio = float('inf')
        candidate_leaving_rows_indices = []
        for i in range(self.num_constraints): 
            pivot_column_element = tableau[i, entering_var_col_idx]
            if pivot_column_element > self.epsilon: 
                current_rhs = tableau[i, -1]
                if current_rhs < -self.epsilon : 
                    continue 
                ratio = current_rhs / pivot_column_element
                if ratio >= -self.epsilon: 
                    if ratio < min_ratio - self.epsilon:
                        min_ratio = ratio
                        candidate_leaving_rows_indices = [i]
                    elif abs(ratio - min_ratio) < self.epsilon: 
                        candidate_leaving_rows_indices.append(i)

        if not candidate_leaving_rows_indices: 
            all_pivot_elements_non_positive_in_col = all(tableau[i, entering_var_col_idx] <= self.epsilon for i in range(self.num_constraints))
            if all_pivot_elements_non_positive_in_col:
                raise Exception(f"Неограниченность: нет положительных элементов в столбце {entering_var_col_idx}.")
            else: 
                raise Exception(f"Нет подходящей выходящей строки для столбца {entering_var_col_idx} (возможно, все RHS < 0 или другие проблемы).")

        if len(candidate_leaving_rows_indices) == 1:
            return candidate_leaving_rows_indices[0]
        else: 
            min_basis_var_idx_in_candidates = float('inf')
            chosen_row_idx = -1
            for row_idx in candidate_leaving_rows_indices:
                if self.basis_vars_indices[row_idx] < min_basis_var_idx_in_candidates:
                    min_basis_var_idx_in_candidates = self.basis_vars_indices[row_idx]
                    chosen_row_idx = row_idx
            if chosen_row_idx == -1:
                if candidate_leaving_rows_indices: 
                    return candidate_leaving_rows_indices[0] 
                raise Exception("Критическая ошибка в _find_leaving_row_idx: нет кандидатов после проверки для правила Блэнда.")
            return chosen_row_idx
            
    def _pivot(self, tableau, leaving_row_idx, entering_var_col_idx):
        pivot_element = tableau[leaving_row_idx, entering_var_col_idx]
        if abs(pivot_element) < self.epsilon:
            raise Exception(f"Разрешающий элемент [{leaving_row_idx},{entering_var_col_idx}] близок к нулю ({pivot_element}).")
        tableau[leaving_row_idx, :] /= pivot_element
        for i in range(tableau.shape[0]):
            if i != leaving_row_idx:
                factor = tableau[i, entering_var_col_idx]
                tableau[i, :] -= factor * tableau[leaving_row_idx, :]
        self.basis_vars_indices[leaving_row_idx] = entering_var_col_idx

    def _run_simplex_iterations(self, tableau, phase_name="Phase", artificial_indices_phase1=None):
        max_iters = (tableau.shape[1] + self.num_constraints) * 20
        for iteration in range(max_iters):
            entering_idx = self._find_entering_variable_idx(tableau)
            if entering_idx is None:
                return tableau, "optimal" 

            if phase_name == "Фаза II" and artificial_indices_phase1 and entering_idx in artificial_indices_phase1:
                tableau[-1, entering_idx] = 1e7 
                continue 
            try:
                leaving_idx = self._find_leaving_row_idx(tableau, entering_idx)
            except Exception as e:
                if "Неограниченность" in str(e).lower() or "unbounded" in str(e).lower(): # более общее условие
                    return tableau, "unbounded"
                # print(f"Исключение в _find_leaving_row_idx ({phase_name}): {e}") # Отладка
                raise e 

            self._pivot(tableau, leaving_idx, entering_idx)
        return tableau, "max_iterations_reached"

    def solve(self, c_orig, A_orig, b_orig, constraint_types_orig, objective_type='maximize'):
        num_constraints_orig, num_vars_orig = A_orig.shape
        self.num_constraints = num_constraints_orig

        c_transformed = np.array(c_orig, dtype=float)
        if objective_type == 'minimize':
            c_transformed = -c_transformed

        A_std = np.array(A_orig, dtype=float)
        b_std = np.array(b_orig, dtype=float)
        constraint_types_std = list(constraint_types_orig)

        for i in range(num_constraints_orig):
            if b_std[i] < -self.epsilon:
                A_std[i, :] *= -1
                b_std[i] *= -1
                if constraint_types_std[i] == '<=': constraint_types_std[i] = '>='
                elif constraint_types_std[i] == '>=': constraint_types_std[i] = '<='
        
        num_slack, num_surplus, num_artificial = 0, 0, 0
        artificial_var_global_indices = [] 
        
        col_idx_slack_start = num_vars_orig
        temp_ct = [] 
        for i in range(num_constraints_orig):
            if constraint_types_std[i] == '<=': temp_ct.append('s')
            elif constraint_types_std[i] == '>=': temp_ct.append('e_a') 
            elif constraint_types_std[i] == '=': temp_ct.append('a')   
        
        num_slack = temp_ct.count('s')
        num_surplus = temp_ct.count('e_a')
        num_artificial = temp_ct.count('e_a') + temp_ct.count('a')

        col_idx_surplus_start = col_idx_slack_start + num_slack
        col_idx_artificial_start = col_idx_surplus_start + num_surplus
        self.total_vars_in_tableau = num_vars_orig + num_slack + num_surplus + num_artificial

        tableau = np.zeros((num_constraints_orig + 1, self.total_vars_in_tableau + 1))
        self.basis_vars_indices = [-1] * num_constraints_orig 

        tableau[:num_constraints_orig, :num_vars_orig] = A_std
        tableau[:num_constraints_orig, -1] = b_std 

        current_s_offset, current_e_offset, current_a_offset = 0, 0, 0
        for i in range(num_constraints_orig):
            if constraint_types_std[i] == '<=':
                idx = col_idx_slack_start + current_s_offset
                tableau[i, idx] = 1.0
                self.basis_vars_indices[i] = idx
                current_s_offset += 1
            elif constraint_types_std[i] == '>=':
                idx_e = col_idx_surplus_start + current_e_offset
                tableau[i, idx_e] = -1.0
                current_e_offset += 1
                idx_a = col_idx_artificial_start + current_a_offset
                tableau[i, idx_a] = 1.0
                self.basis_vars_indices[i] = idx_a
                artificial_var_global_indices.append(idx_a)
                current_a_offset += 1
            elif constraint_types_std[i] == '=':
                idx_a = col_idx_artificial_start + current_a_offset
                tableau[i, idx_a] = 1.0
                self.basis_vars_indices[i] = idx_a
                artificial_var_global_indices.append(idx_a)
                current_a_offset += 1
        
        if num_artificial > 0:
            c_phase1_target = np.zeros(self.total_vars_in_tableau)
            for art_idx in artificial_var_global_indices:
                c_phase1_target[art_idx] = -1.0 
            
            cb_p_sum = np.zeros(self.total_vars_in_tableau + 1)
            for r in range(num_constraints_orig):
                basis_var_idx = self.basis_vars_indices[r]
                coeff_in_phase1_obj = 0.0
                if basis_var_idx in artificial_var_global_indices:
                    coeff_in_phase1_obj = -1.0
                cb_p_sum += coeff_in_phase1_obj * tableau[r, :]
            
            tableau[-1, :self.total_vars_in_tableau] = cb_p_sum[:self.total_vars_in_tableau] - c_phase1_target
            tableau[-1, -1] = cb_p_sum[-1]

            tableau, status_phase1 = self._run_simplex_iterations(tableau, "Фаза I", artificial_var_global_indices)

            if status_phase1 == "unbounded": 
                return {"status": "infeasible (Фаза I неограничена, ошибка)", "x": None, "objective_value": None}
            if status_phase1 == "max_iterations_reached":
                 return {"status": "Фаза I: превышено число итераций", "x": None, "objective_value": None}

            phase1_opt_val = tableau[-1, -1] # Это max(-W)
            if phase1_opt_val < -self.epsilon: # Если max(-W) < 0, то min(W) > 0
                return {"status": "infeasible (Фаза I: сумма искусств. > 0)", "x": None, "objective_value": None}

            for r_idx in range(num_constraints_orig):
                if self.basis_vars_indices[r_idx] in artificial_var_global_indices and \
                   abs(tableau[r_idx, -1]) > self.epsilon:
                    return {"status": "infeasible (Фаза I: искусств. в базисе > 0)", "x": None, "objective_value": None}
        
        tableau[-1, :] = 0.0 
        tableau[-1, :num_vars_orig] = -c_transformed 

        for r in range(num_constraints_orig):
            basis_var_idx = self.basis_vars_indices[r]
            coeff_in_orig_obj = 0.0
            if basis_var_idx < num_vars_orig: 
                coeff_in_orig_obj = c_transformed[basis_var_idx]
            
            # Важно: НЕ вычитаем для строк, где в базисе искусственная переменная
            # (даже если она там с нулевым значением), т.к. ее коэф. в исходной цели = 0.
            if basis_var_idx not in artificial_var_global_indices:
                 if abs(coeff_in_orig_obj) > self.epsilon:
                    tableau[-1, :] -= coeff_in_orig_obj * tableau[r, :]
        
        # Для Фазы II, искусственные переменные не должны входить.
        # Если они не в базисе, их Z-коэффициент делаем очень невыгодным.
        # Если они остались в базисе (с нулевым значением), их Z-коэффициент УЖЕ должен быть 0
        # после коррекции Z-строки выше, так как их коэф. в исходной цели 0.
        M_penalty = 1e7 
        for art_idx in artificial_var_global_indices:
            # if art_idx not in self.basis_vars_indices: # Только если не в базисе
            #     tableau[-1, art_idx] = M_penalty
            # Более безопасный подход: всегда делаем их невыгодными, если они не должны быть там.
            # Но _run_simplex_iterations уже имеет проверку. Здесь просто убедимся, что их Z-коэфф. не привлекателен.
            if art_idx < self.total_vars_in_tableau : # Проверка границ
                if tableau[-1, art_idx] < -self.epsilon : # Если он почему-то стал выгодным
                     tableau[-1, art_idx] = M_penalty


        tableau, status_phase2 = self._run_simplex_iterations(tableau, "Фаза II", artificial_var_global_indices)

        if status_phase2 == "max_iterations_reached":
            return {"status": "Фаза II: превышено число итераций", "x": None, "objective_value": None}
        if status_phase2 == "unbounded":
            return {"status": "unbounded", "x": None, "objective_value": None}

        solution = np.zeros(num_vars_orig)
        for r in range(num_constraints_orig):
            basis_var_idx = self.basis_vars_indices[r]
            if basis_var_idx < num_vars_orig:
                val = tableau[r, -1]
                solution[basis_var_idx] = val if val > -self.epsilon else 0.0
        
        final_opt_value_transformed = tableau[-1, -1] # Это значение для максимизации c_transformed*x
        
        # Корректируем значение, если исходная задача была на минимизацию
        final_opt_value = final_opt_value_transformed
        if objective_type == 'minimize':
            final_opt_value = -final_opt_value_transformed 
            
        for r in range(num_constraints_orig):
            if tableau[r, -1] < -self.epsilon :
                return {"status": "error (финальное решение недопустимо)", "x": solution, "objective_value": final_opt_value}

        return {"status": "optimal", "x": solution, "objective_value": final_opt_value}


class LPVisualizer:
    def __init__(self, root):
        # ... (ваш код __init__ из предыдущего ответа) ...
        self.root = root
        self.root.title("Графическое исследование ЗЛП (проекция)")
        
        self.setup_screen = ttk.Frame(root)
        self.setup_screen.pack(padx=20, pady=20)
        
        ttk.Label(self.setup_screen, text="Введите количество переменных:", font=("Arial", 12)).pack(pady=10)
        
        self.var_count_input = tk.IntVar(value=2) 
        var_selector = ttk.Spinbox(self.setup_screen, from_=1, to=10, textvariable=self.var_count_input, width=5)
        var_selector.pack(pady=10)
        
        self.use_visualization = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.setup_screen, text="С отрисовкой (только для 2-3 переменных)", variable=self.use_visualization).pack(pady=5)
        
        ttk.Button(self.setup_screen, text="Продолжить", command=self.initialize_solver_ui).pack(pady=10) 
        
        self.main_frame = None
        self.simplex_core = SimplexMethodCore() 

    def initialize_solver_ui(self): 
        self.setup_screen.destroy()
        
        self.var_count = self.var_count_input.get()
        self.visualization_mode = self.use_visualization.get()

        if self.visualization_mode and self.var_count > 3 : 
            print("Визуализация поддерживается только для 2 или 3 исходных переменных. Переключаюсь в аналитический режим.")
            self.visualization_mode = False
        elif self.visualization_mode and self.var_count == 1:
            print("Визуализация для 1 переменной не очень информативна. Переключаюсь в аналитический режим.")
            self.visualization_mode = False

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y, anchor='nw') 
        
        if self.visualization_mode and self.var_count >=2: 
            self.plot_frame = ttk.Frame(self.main_frame)
            self.plot_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.step_size = tk.DoubleVar(value=0.5) 
        self.mode = tk.StringVar(value="Максимум") 
        
        self.constraints_widgets = []
        self.vertices_2d = [] 
        self.current_point_2d = None
        self.manual_mode_2d = False 
        self.edge_path_2d = []
        
        self.objective_coeffs_vars = [] 
        self.fixed_values_vars = []   
        
        self.setup_ui_elements() 
        self.update_objective_and_fixed_entries() 

    def setup_ui_elements(self): 
        title_text = f"Графическое решение ({self.var_count}D -> 2D проекция)" if self.visualization_mode and self.var_count >= 2 else f"Аналитическое решение ({self.var_count} переменных)"
        ttk.Label(self.input_frame, text=title_text, font=("Arial", 12)).pack(pady=10)
        
        objective_frame = ttk.LabelFrame(self.input_frame, text="Целевая функция")
        objective_frame.pack(fill=tk.X, padx=5, pady=5)
        self.objective_container = ttk.Frame(objective_frame) 
        self.objective_container.pack(fill=tk.X)
        
        mode_frame = ttk.Frame(objective_frame)
        mode_frame.pack(pady=5)
        ttk.Radiobutton(mode_frame, text="Максимум", variable=self.mode, value="Максимум").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Минимум", variable=self.mode, value="Минимум").pack(side=tk.LEFT, padx=5)

        if self.visualization_mode and self.var_count > 2:
            self.fixed_vars_frame = ttk.LabelFrame(self.input_frame, text=f"Фиксировать x3..x{self.var_count} для 2D (x1,x2)")
            self.fixed_vars_frame.pack(fill=tk.X, padx=5, pady=5)
            self.fixed_vars_container = ttk.Frame(self.fixed_vars_frame)
            self.fixed_vars_container.pack(fill=tk.X)

        constraints_frame = ttk.LabelFrame(self.input_frame, text="Ограничения")
        constraints_frame.pack(fill=tk.X, padx=5, pady=5)
        self.constraints_container = ttk.Frame(constraints_frame) 
        self.constraints_container.pack(fill=tk.X)
        ttk.Button(constraints_frame, text="Добавить ограничение", command=self.add_constraint_ui).pack(pady=5) 

        if self.visualization_mode and self.var_count ==2 : 
            step_frame = ttk.LabelFrame(self.input_frame, text="Шаг ручного перемещения (для 2D)")
            step_frame.pack(fill=tk.X, padx=5, pady=5)
            ttk.Entry(step_frame, textvariable=self.step_size, width=10).pack()

        self.info_label = ttk.Label(self.input_frame, text="Введите данные и решите задачу.", wraplength=300)
        self.info_label.pack(pady=10, fill=tk.X)

        control_frame = ttk.Frame(self.input_frame)
        control_frame.pack(pady=5, fill=tk.X)
        
        if self.visualization_mode and self.var_count >= 2:
            ttk.Button(control_frame, text="Решить и показать график", command=self.solve_and_visualize).pack(fill=tk.X, pady=2)
            if self.var_count == 2: 
                 ttk.Button(control_frame, text="Ручной режим (2D)", command=self.start_manual_mode_2d).pack(fill=tk.X, pady=2)
        else:
            ttk.Button(control_frame, text="Решить задачу (аналитически)", command=self.solve_analytical_only).pack(fill=tk.X, pady=2)
            
        ttk.Button(control_frame, text="Сбросить всё", command=self.reset_all_ui).pack(fill=tk.X, pady=2) 
        ttk.Button(control_frame, text="Новая задача (изменить кол-во пер.)", command=self.new_problem_setup).pack(fill=tk.X, pady=2) 

        if self.visualization_mode and self.var_count >= 2:
            self.fig, self.ax = plt.subplots(figsize=(6,5)) 
            self.ax.set_xlabel("x1") 
            self.ax.set_ylabel("x2")
            self.ax.grid(True, linestyle='--', linewidth=0.5)
            self.ax.axhline(0, color='black', linewidth=0.7)
            self.ax.axvline(0, color='black', linewidth=0.7)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(fill=tk.BOTH, expand=True)
            
            if self.var_count == 2: 
                self.root.bind("<Up>", lambda e: self.move_along_edge_2d(1))
                self.root.bind("<Down>", lambda e: self.move_along_edge_2d(-1))
                self.root.bind("<Left>", lambda e: self.move_along_edge_2d(-1)) 
                self.root.bind("<Right>", lambda e: self.move_along_edge_2d(1)) 

    def update_objective_and_fixed_entries(self): 
        for widget in self.objective_container.winfo_children():
            widget.destroy()
        self.objective_coeffs_vars = []

        for i in range(self.var_count):
            coeff_var = tk.DoubleVar(value=0.0) 
            self.objective_coeffs_vars.append(coeff_var)
            entry_frame = ttk.Frame(self.objective_container)
            entry_frame.pack(side=tk.LEFT, padx=2)
            ttk.Entry(entry_frame, textvariable=coeff_var, width=5).pack(side=tk.LEFT)
            label_text = f"x{i+1}"
            if i < self.var_count - 1:
                label_text += " +"
            ttk.Label(entry_frame, text=label_text).pack(side=tk.LEFT)

        if hasattr(self, 'fixed_vars_frame') and self.fixed_vars_frame.winfo_exists(): # Проверяем, существует ли фрейм
            for widget in self.fixed_vars_container.winfo_children(): # Очищаем контейнер
                widget.destroy()
            if not (self.visualization_mode and self.var_count > 2) : # Если он больше не нужен, удаляем сам фрейм
                self.fixed_vars_frame.destroy()
                delattr(self, 'fixed_vars_frame')
                if hasattr(self, 'fixed_vars_container'): delattr(self, 'fixed_vars_container')


        if self.visualization_mode and self.var_count > 2:
            if not hasattr(self, 'fixed_vars_frame') or not self.fixed_vars_frame.winfo_exists(): # Создаем, если нет или был удален
                # Найдем constraints_frame, чтобы вставить fixed_vars_frame перед ним
                # Это немного хрупко, лучше иметь родительский фрейм для input_frame и добавлять в него.
                # Пока оставим так или найдем более надежный способ позиционирования.
                # Попробуем вставить перед последними 3 элементами (info_label, control_frame)
                # Или проще всего, если constraints_frame уже создан, то перед ним.
                # В self.setup_ui_elements fixed_vars_frame создается после objective_frame.
                # Значит, при обновлении он должен быть пересоздан, если его нет.
                
                # Позиционирование может быть сложным при обновлении. Проще всего пересоздавать часть UI.
                # Для простоты, если fixed_vars_frame был удален, мы его создадим снова.
                # Но это может нарушить порядок. Лучше скрывать/показывать.
                # Пока оставим так: если его нет, создаем.
                if not hasattr(self, 'fixed_vars_frame') or not self.fixed_vars_frame.winfo_exists():
                    self.fixed_vars_frame = ttk.LabelFrame(self.input_frame, text=f"Фиксировать x3..x{self.var_count} для 2D (x1,x2)")
                    # Пытаемся вставить перед constraints_frame, если он есть
                    children = self.input_frame.winfo_children()
                    constraints_frame_found = None
                    for child in children:
                        if isinstance(child, ttk.LabelFrame) and "Ограничения" in child.cget("text"):
                            constraints_frame_found = child
                            break
                    if constraints_frame_found:
                        self.fixed_vars_frame.pack(fill=tk.X, padx=5, pady=5, before=constraints_frame_found)
                    else: # Если не нашли, просто пакуем
                         self.fixed_vars_frame.pack(fill=tk.X, padx=5, pady=5)

                    self.fixed_vars_container = ttk.Frame(self.fixed_vars_frame)
                    self.fixed_vars_container.pack(fill=tk.X)

            self.fixed_values_vars = []
            for i in range(2, self.var_count): 
                val_var = tk.DoubleVar(value=0.0) 
                self.fixed_values_vars.append(val_var)
                fix_entry_frame = ttk.Frame(self.fixed_vars_container)
                fix_entry_frame.pack(fill=tk.X, pady=1)
                ttk.Label(fix_entry_frame, text=f"x{i+1} = ").pack(side=tk.LEFT)
                ttk.Entry(fix_entry_frame, textvariable=val_var, width=8).pack(side=tk.LEFT)

    def add_constraint_ui(self): 
        frame = ttk.Frame(self.constraints_container)
        frame.pack(fill=tk.X, pady=2)
        coeffs_vars_in_row = [] 
        for i in range(self.var_count):
            coeff_var = tk.DoubleVar(value=0.0)
            coeffs_vars_in_row.append(coeff_var)
            ttk.Entry(frame, textvariable=coeff_var, width=4).pack(side=tk.LEFT)
            label_text = f"x{i+1}"
            if i < self.var_count - 1:
                label_text += " +"
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT, padx=(0,2))

        sign_var = tk.StringVar(value="<=")
        b_var = tk.DoubleVar(value=0.0)
        ttk.Combobox(frame, textvariable=sign_var, values=["<=", ">=", "="], width=3, state="readonly").pack(side=tk.LEFT, padx=2)
        ttk.Entry(frame, textvariable=b_var, width=5).pack(side=tk.LEFT)
        ttk.Button(frame, text="X", command=lambda f=frame: self.remove_constraint_ui(f), width=2).pack(side=tk.LEFT, padx=5)
        self.constraints_widgets.append({"frame": frame, "coeffs": coeffs_vars_in_row, "sign": sign_var, "b": b_var})

    def remove_constraint_ui(self, frame_to_remove): 
        for i, widget_dict in enumerate(self.constraints_widgets):
            if widget_dict["frame"] == frame_to_remove:
                self.constraints_widgets.pop(i)
                break
        frame_to_remove.destroy()
        
    def reset_all_ui(self): 
        for widget_dict in self.constraints_widgets:
            widget_dict["frame"].destroy()
        self.constraints_widgets.clear()
        self.update_objective_and_fixed_entries() 
        self.vertices_2d.clear()
        self.current_point_2d = None
        self.manual_mode_2d = False
        self.edge_path_2d.clear()
        self.info_label.config(text="Данные сброшены. Введите новые.")
        if self.visualization_mode and self.var_count >=2 and hasattr(self, 'ax') and self.ax.figure is not None: # Проверка на None
            self.ax.clear()
            self.ax.set_xlabel("x1")
            self.ax.set_ylabel("x2")
            self.ax.grid(True, linestyle='--', linewidth=0.5)
            self.ax.axhline(0, color='black', linewidth=0.7)
            self.ax.axvline(0, color='black', linewidth=0.7)
            self.canvas.draw()
            
    def new_problem_setup(self): 
        if self.main_frame:
            self.main_frame.destroy()
            self.main_frame = None 
            if hasattr(self, 'fig'): # Закрываем фигуру Matplotlib, если она была
                plt.close(self.fig)
                delattr(self, 'fig')
                delattr(self, 'ax')
                delattr(self, 'canvas')


        self.setup_screen = ttk.Frame(self.root)
        self.setup_screen.pack(padx=20, pady=20)
        ttk.Label(self.setup_screen, text="Введите количество переменных:", font=("Arial", 12)).pack(pady=10)
        # self.var_count_input уже существует, просто используем его
        var_selector = ttk.Spinbox(self.setup_screen, from_=1, to=10, textvariable=self.var_count_input, width=5)
        var_selector.pack(pady=10)
        # self.use_visualization уже существует
        ttk.Checkbutton(self.setup_screen, text="С отрисовкой (только для 2-3 переменных)", variable=self.use_visualization).pack(pady=5)
        ttk.Button(self.setup_screen, text="Продолжить", command=self.initialize_solver_ui).pack(pady=10)

    def _get_data_from_ui(self):
        try:
            c = np.array([var.get() for var in self.objective_coeffs_vars])
            A_list = []
            b_list = []
            ct_list = []
            for constr_widget in self.constraints_widgets:
                A_list.append([var.get() for var in constr_widget["coeffs"]])
                b_list.append(constr_widget["b"].get())
                ct_list.append(constr_widget["sign"].get())
            A = np.array(A_list) if A_list else np.empty((0, self.var_count))
            b = np.array(b_list) if b_list else np.empty(0)
            objective_mode = "maximize" if self.mode.get() == "Максимум" else "minimize"
            return c, A, b, ct_list, objective_mode
        except Exception as e:
            self.info_label.config(text=f"Ошибка чтения данных: {str(e)}")
            return None, None, None, None, None

    def solve_analytical_only(self): 
        data = self._get_data_from_ui()
        if data[0] is None: return
        c, A, b, ct, obj_mode = data
        if A.shape[0] == 0 and self.var_count > 0 : 
             self.info_label.config(text="Нет ограничений. Задача не ограничена (если не все c_i=0).")
             return
        try:
            result = self.simplex_core.solve(c, A, b, ct, objective_type=obj_mode)
            if result["status"] == "optimal":
                solution_str = "Оптимальное решение:\n"
                for i, val in enumerate(result["x"]): solution_str += f"x{i+1} = {val:.4f}\n"
                solution_str += f"\nЗначение целевой функции = {result['objective_value']:.4f}"
                self.info_label.config(text=solution_str)
            else:
                self.info_label.config(text=f"Результат: {result['status']}")
        except Exception as e:
            self.info_label.config(text=f"Ошибка при решении задачи:\n{str(e)}\n{traceback.format_exc()}")

    def solve_and_visualize(self): 
        data = self._get_data_from_ui()
        if data[0] is None: return
        c_all_vars, A_all_vars, b_all_vars, ct_all_vars, obj_mode_all_vars = data
        if A_all_vars.shape[0] == 0 and self.var_count > 0:
            self.info_label.config(text="Нет ограничений для решения и визуализации.")
            if hasattr(self, 'ax') and self.ax.figure is not None:
                self.ax.clear()
                self.ax.set_xlabel("x1"); self.ax.set_ylabel("x2")
                self.ax.grid(True); self.ax.axhline(0,c='k'); self.ax.axvline(0,c='k')
                self.canvas.draw()
            return
        try:
            full_result = self.simplex_core.solve(c_all_vars, A_all_vars, b_all_vars, ct_all_vars, objective_type=obj_mode_all_vars)
            if full_result["status"] == "optimal":
                solution_str = "Полное оптимальное решение:\n"
                for i, val in enumerate(full_result["x"]): solution_str += f"x{i+1} = {val:.3f}; "
                solution_str += f"\nF_opt = {full_result['objective_value']:.3f}"
                self.info_label.config(text=solution_str)
                if self.var_count >= 2 and self.visualization_mode:
                    self.plot_2d_projection(c_all_vars, A_all_vars, b_all_vars, ct_all_vars, 
                                            full_result["x"], full_result["objective_value"])
            else:
                self.info_label.config(text=f"Полное решение: {full_result['status']}")
                if hasattr(self, 'ax') and self.ax.figure is not None:
                    self.ax.clear()
                    self.ax.set_xlabel("x1"); self.ax.set_ylabel("x2")
                    self.ax.grid(True); self.ax.axhline(0,c='k'); self.ax.axvline(0,c='k')
                    self.canvas.draw()
        except Exception as e:
            self.info_label.config(text=f"Ошибка при решении/визуализации:\n{str(e)}\n{traceback.format_exc()}")

    def plot_2d_projection(self, c_orig_full, A_orig_full, b_orig_full, ct_orig_full, optimal_solution_full, optimal_value_full):
        if not (self.visualization_mode and self.var_count >=2 and hasattr(self, 'ax') and self.ax.figure is not None):
            # print("Условия для plot_2d_projection не выполнены")
            return 

        self.ax.clear()
        idx_x_plot, idx_y_plot = 0, 1 
        self.ax.set_xlabel(f"x{idx_x_plot+1}")
        self.ax.set_ylabel(f"x{idx_y_plot+1}")

        fixed_vars_values_for_plot = {} 
        fixed_vars_sum_constraints = np.zeros(A_orig_full.shape[0]) 
        fixed_vars_sum_objective = 0 

        if self.var_count > 2:
            for i in range(len(self.fixed_values_vars)): 
                actual_var_index = i + 2 
                fixed_val = self.fixed_values_vars[i].get()
                fixed_vars_values_for_plot[actual_var_index] = fixed_val
                if A_orig_full.shape[1] > actual_var_index:
                    fixed_vars_sum_constraints += A_orig_full[:, actual_var_index] * fixed_val
                if len(c_orig_full) > actual_var_index:
                    fixed_vars_sum_objective += c_orig_full[actual_var_index] * fixed_val
        
        b_2d_eff = b_orig_full - fixed_vars_sum_constraints 

        opt_x1_proj = optimal_solution_full[idx_x_plot]
        opt_x2_proj = optimal_solution_full[idx_y_plot]
        delta = max(2, abs(opt_x1_proj)*0.8 + abs(opt_x2_proj)*0.8 + 2) # Адаптивный дельта
        
        x_min_plot, x_max_plot = min(0, opt_x1_proj) - delta, max(0, opt_x1_proj) + delta
        y_min_plot, y_max_plot = min(0, opt_x2_proj) - delta, max(0, opt_x2_proj) + delta
        
        x_vals_for_lines = np.linspace(x_min_plot, x_max_plot, 200)

        for i in range(A_orig_full.shape[0]):
            a_plot_x = A_orig_full[i, idx_x_plot]
            a_plot_y = A_orig_full[i, idx_y_plot]
            b_eff_constr = b_2d_eff[i]
            
            constr_label_parts = []
            if abs(a_plot_x) > self.epsilon: constr_label_parts.append(f"{a_plot_x:.1f}x{idx_x_plot+1}")
            if abs(a_plot_y) > self.epsilon: constr_label_parts.append(f"{a_plot_y:+.1f}x{idx_y_plot+1}")
            
            fixed_contrib_str = ""
            if self.var_count > 2:
                current_fixed_contrib = np.sum(A_orig_full[i, k] * fixed_vars_values_for_plot.get(k,0.0) for k in range(2, self.var_count))
                if abs(current_fixed_contrib) > self.epsilon:
                    fixed_contrib_str = f" ({current_fixed_contrib:+.1f} от фикс.)"

            if not constr_label_parts and abs(b_orig_full[i] - original_fixed_effect_for_label_if_needed) > self.epsilon: # Ограничение только на фикс. переменные
                # print(f"Ограничение {i+1} не зависит от x{idx_x_plot+1}, x{idx_y_plot+1}, но может быть активным.")
                pass # Пропускаем рисование таких линий, но они влияют на ОДР
            
            constr_label = f"Огр{i+1}: " + " + ".join(constr_label_parts) + fixed_contrib_str + f" {ct_orig_full[i]} {b_orig_full[i]}"
            line_style = '-' if ct_orig_full[i] == '=' else '--'

            if abs(a_plot_y) > self.epsilon:
                y_vals_constr = (b_eff_constr - a_plot_x * x_vals_for_lines) / a_plot_y
                self.ax.plot(x_vals_for_lines, y_vals_constr, linestyle=line_style, label=constr_label if len(constr_label)<100 else f"Огр{i+1}", alpha=0.7)
            elif abs(a_plot_x) > self.epsilon:
                x_val_constr = b_eff_constr / a_plot_x
                self.ax.axvline(x_val_constr, linestyle=line_style, label=constr_label if len(constr_label)<100 else f"Огр{i+1}", alpha=0.7)
        
        c_plot_x = c_orig_full[idx_x_plot]
        c_plot_y = c_orig_full[idx_y_plot]

        if abs(c_plot_x) > self.epsilon or abs(c_plot_y) > self.epsilon : 
            x_grid_contour, y_grid_contour = np.meshgrid(np.linspace(x_min_plot, x_max_plot, 50), np.linspace(y_min_plot, y_max_plot, 50))
            F_grid_vals_contour = c_plot_x * x_grid_contour + c_plot_y * y_grid_contour
            opt_F_2d_part_contour = c_plot_x * opt_x1_proj + c_plot_y * opt_x2_proj
            
            num_levels_contour = 7
            delta_level = max(0.5, abs(opt_F_2d_part_contour / num_levels_contour)) if opt_F_2d_part_contour != 0 else 0.5
            levels_contour = np.linspace(opt_F_2d_part_contour - 3*delta_level, 
                                         opt_F_2d_part_contour + 3*delta_level, 
                                         num_levels_contour)
            levels_contour = np.sort(np.unique(np.round(np.append(levels_contour, opt_F_2d_part_contour), 2))) 

            CS = self.ax.contour(x_grid_contour, y_grid_contour, F_grid_vals_contour, levels=levels_contour, colors='dimgrey', linestyles=':', alpha=0.8)
            self.ax.clabel(CS, inline=True, fontsize=7, fmt=lambda val: f'{val:.1f}') 
    
        self.ax.plot(opt_x1_proj, opt_x2_proj, 'ro', markersize=8, 
                     label=f'Опт. проекция\nx{idx_x_plot+1}={opt_x1_proj:.2f}, x{idx_y_plot+1}={opt_x2_proj:.2f}\n(Общее F={optimal_value_full:.2f})')

        self.ax.set_xlim(x_min_plot, x_max_plot)
        self.ax.set_ylim(y_min_plot, y_max_plot)
        self.ax.grid(True, linestyle='--', linewidth=0.5)
        self.ax.axhline(0, color='black', linewidth=0.7)
        self.ax.axvline(0, color='black', linewidth=0.7)
        
        fixed_vars_str_title = ", ".join([f"x{k+1}={v:.1f}" for k,v in fixed_vars_values_for_plot.items()])
        plot_title_text = f"Проекция на (x{idx_x_plot+1}, x{idx_y_plot+1})"
        if fixed_vars_str_title:
            plot_title_text += f"\nФикс: {fixed_vars_str_title}"
        self.ax.set_title(plot_title_text, fontsize=10)
        
        if self.ax.has_data(): # Показываем легенду, только если есть что показывать
            self.ax.legend(loc='best', fontsize='xx-small') # Уменьшил размер шрифта легенды
        self.canvas.draw()
        
    def start_manual_mode_2d(self): 
        if not (self.visualization_mode and self.var_count == 2):
            self.info_label.config(text="Ручной режим доступен только для 2х переменных с визуализацией.")
            return
        self.manual_mode_2d = True
        self.current_point_2d = (0.0, 0.0) 
        self.edge_path_2d = [] 
        self.info_label.config(text="Ручной режим (2D) активирован. Используйте стрелки. (Функционал не реализован)")
        print("Ручной режим активирован. Логика перемещения по ребрам ОДР требует реализации.")

    def move_along_edge_2d(self, direction): 
        if not self.manual_mode_2d or self.current_point_2d is None or not self.edge_path_2d:
            return
        print(f"Команда на перемещение в ручном режиме (2D): направление {direction}. (Функционал не реализован)")
        pass 

# --- Основной блок для запуска ---
if __name__ == "__main__":
    root = tk.Tk()
    app = LPVisualizer(root)
    root.mainloop()