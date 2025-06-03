import numpy as np
from constraint import Constraint
from system_of_constraints import SystemOfConstraints

class Task:

    number_of_variables: int # Количество переменных в задаче
    c: list[float] # Список коэффициентов целевой функции
    system_of_constraints: SystemOfConstraints # Система ограничений

    def __init__(self, number_of_variables: int, c: list[float], constraints: list[Constraint]):
        self.number_of_variables = number_of_variables
        self.c = c
        self.system_of_constraints = SystemOfConstraints(constraints)

def make_task_canonical(task: Task):
    """
    Переделывает задачу в каноническую путем добавления переменных
    """
    for i in task.system_of_constraints.indices_of_non_good_constraints:
        if task.system_of_constraints.constraints[i].type_of_ineq != "=":
            not_equal_add_variable(task, i)
    for j in task.system_of_constraints.indices_of_non_good_variables:
        non_good_variable_add_variable(task, j)

def not_equal_add_variable(task: Task, i: int):
    for index_of_non_good_constraint in range(len(task.system_of_constraints.indices_of_non_good_constraints)):
        task.system_of_constraints.A[index_of_non_good_constraint].append(0.0) # TODO изменить тип ограничения на "="
    task.system_of_constraints.A[i][-1]=-1.0

def non_good_variable_add_variable(task: Task, index_of_non_good_variable: int):
    for index_of_non_good_constraint in range(len(task.system_of_constraints.indices_of_non_good_constraints)):
        task.system_of_constraints.A[index_of_non_good_constraint].append(-task.system_of_constraints.A[index_of_non_good_constraint][index_of_non_good_variable])

if __name__ == "__main__":
    # Первое ограничение
    coefficients_ex1 = [1, 0, -3]
    b_ex1 = 4
    type_of_ineq_ex1 = ">="

    Constraint_instance1 = Constraint(coefficients_ex1, b_ex1, type_of_ineq_ex1)

    # Второе ограничение
    coefficients_ex2 = [0, 0, -3]
    b_ex2 = 1
    type_of_ineq_ex2 = "="

    Constraint_instance2 = Constraint(coefficients_ex2, b_ex2, type_of_ineq_ex2)

    # Третье ограничение
    coefficients_ex3 = [0, 0, -3]
    b_ex3 = 0
    type_of_ineq_ex3 = "<="

    Constraint_instance3 = Constraint(coefficients_ex3, b_ex3, type_of_ineq_ex3)

    task_instance = Task(3, [1, 2, 3], [Constraint_instance1, Constraint_instance2, Constraint_instance3])

    make_task_canonical(task_instance)
    print(task_instance.system_of_constraints)