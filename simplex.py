from Task import Task
from constraint import Constraint
from Task import make_task_canonical
import math
import numpy as np

def simplex(task: Task):

    c = task.c
    A = task.system_of_constraints.A
    b = task.system_of_constraints.b

    tableau = to_tableau(c, A, b)

    i = 0
    while can_be_improved(tableau) and i < 10:
        i += 1
        print(i)
        pivot_position = get_pivot_position(tableau)
        tableau = pivot_step(tableau, pivot_position)

    return get_solution(tableau)

def to_tableau(c, A, b):
    xb = [eq + [x] for eq, x in zip(A, b)]
    z = c + [0]
    return xb + [z]

def can_be_improved(tableau):
    z = tableau[-1]
    return any(x > 0 for x in z[:-1])

def get_pivot_position(tableau):
    z = tableau[-1]
    column = next(i for i, x in enumerate(z[:-1]) if x > 0)
    # column = max(((i, x) for i, x in enumerate(z[:-1]) if x > 0), key=lambda t: t[1])[0]

    restrictions = []
    for eq in tableau[:-1]:
        el = eq[column]
        restrictions.append(math.inf if el <= 0 else eq[-1] / el)

    row = restrictions.index(min(restrictions))
    return row, column

def pivot_step(tableau, pivot_position):
    new_tableau = [[] for eq in tableau]

    i, j = pivot_position
    pivot_value = tableau[i][j]
    new_tableau[i] = np.array(tableau[i]) / pivot_value

    for eq_i, eq in enumerate(tableau):
        if eq_i != i:
            multiplier = np.array(new_tableau[i]) * tableau[eq_i][j]
            new_tableau[eq_i] = np.array(tableau[eq_i]) - multiplier

    return new_tableau

def is_basic(column):
    return sum(column) == 1 and len([c for c in column if c == 0]) == len(column) - 1

def get_solution(tableau):
    columns = np.array(tableau).T
    solutions = []
    for column in columns[:-1]:
        solution = 0
        if is_basic(column):
            one_index = column.tolist().index(1)
            solution = columns[-1][one_index]
        solutions.append(solution)

    return solutions
if __name__ == "__main__":
    # Первое ограничение
    coefficients_ex1 = [1, -1]
    b_ex1 = -2
    type_of_ineq_ex1 = ">="

    Constraint_instance1 = Constraint(coefficients_ex1, b_ex1, type_of_ineq_ex1)

    # Второе ограничение
    coefficients_ex2 = [-1, -1]
    b_ex2 = -4
    type_of_ineq_ex2 = ">="

    Constraint_instance2 = Constraint(coefficients_ex2, b_ex2, type_of_ineq_ex2)

    # Третье ограничение
    # coefficients_ex3 = [1, 1]
    # b_ex3 = 4
    # type_of_ineq_ex3 = ">="

    # Constraint_instance3 = Constraint(coefficients_ex3, b_ex3, type_of_ineq_ex3)

    task_instance = Task(2, [1, -4], [Constraint_instance1, Constraint_instance2])

    make_task_canonical(task_instance)
    print(task_instance.system_of_constraints)

    ans = simplex(task_instance)
    print(ans)