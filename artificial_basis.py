from Task import Task
from constraint import Constraint
from simplex import simplex
from Task import make_task_canonical

def find_pivot_position(task: Task):
    add_variables(task)
    point = simplex(task)
    return point

def add_variables(task: Task):
    for index_of_constraint in range(len(task.system_of_constraints.constraints)):
        for j in range(0, index_of_constraint):
            task.system_of_constraints.A[index_of_constraint].append(0.0)
        task.system_of_constraints.A[index_of_constraint].append(1.0)
        for k in range(task.system_of_constraints.number_of_constraints - 1 - index_of_constraint):
            task.system_of_constraints.A[index_of_constraint].append(0.0)
    for i in range(len(task.system_of_constraints.constraints)):
        task.c.append(0.0)

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

    task_instance = Task(2, [-1, 4], [Constraint_instance1, Constraint_instance2])
    make_task_canonical(task_instance)

    #add_variables(task_instance)
    #print(task_instance.system_of_constraints.A)
    print(find_pivot_position(task_instance))
