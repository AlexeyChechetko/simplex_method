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
    number_of_non_equal_constraints = 0

    for i in range(len(task.system_of_constraints.constraints)):
        if task.system_of_constraints.constraints[i].type_of_ineq != "=":
            not_equal_add_variable(task, i)
            number_of_non_equal_constraints += 1

    check_right_parts(task)

    for n in range(number_of_non_equal_constraints):
        task.c.append(0)

def not_equal_add_variable(task: Task, i: int):
    for index_of_constraint in range(len(task.system_of_constraints.constraints)):
        task.system_of_constraints.A[index_of_constraint].append(0.0) # TODO изменить тип ограничения на "="
    task.system_of_constraints.constraints[i].type_of_ineq = "="
    task.system_of_constraints.A[i][-1]=1.0

def check_right_parts(task: Task):
    for index_of_constraint in range(len(task.system_of_constraints.constraints)):
        if task.system_of_constraints.constraints[index_of_constraint].b < 0:
            task.system_of_constraints.constraints[index_of_constraint].coefficients = list(np.array(task.system_of_constraints.constraints[index_of_constraint].coefficients) * (-1))
            task.system_of_constraints.A[index_of_constraint] = list(np.array(task.system_of_constraints.A[index_of_constraint]) * (-1))
            task.system_of_constraints.constraints[index_of_constraint].b *= -1
            task.system_of_constraints.b[index_of_constraint] *= (-1)

if __name__ == "__main__":
    # Первое ограничение
    coefficients_ex1 = [1, -4]
    b_ex1 = 4
    type_of_ineq_ex1 = "<="

    Constraint_instance1 = Constraint(coefficients_ex1, b_ex1, type_of_ineq_ex1)

    # Второе ограничение
    coefficients_ex2 = [3, -1]
    b_ex2 = 0
    type_of_ineq_ex2 = ">="

    Constraint_instance2 = Constraint(coefficients_ex2, b_ex2, type_of_ineq_ex2)

    # Третье ограничение
    coefficients_ex3 = [1, 1]
    b_ex3 = 4
    type_of_ineq_ex3 = ">="

    Constraint_instance3 = Constraint(coefficients_ex3, b_ex3, type_of_ineq_ex3)

    task_instance = Task(2, [-1, -1], [Constraint_instance1, Constraint_instance2, Constraint_instance3])

    make_task_canonical(task_instance)
    print(task_instance.system_of_constraints)
    print(task_instance.c)