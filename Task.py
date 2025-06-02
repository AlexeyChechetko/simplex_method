import numpy as np

from constraint import Constraint
from system_of_constraints import SystemOfConstraints

class Task:

    number_of_variables: int # Количество переменных в задаче
    c: list[float] # Список коэффициентов целевой функции
    system_of_constraints: SystemOfConstraints # Система ограничений

    def __init__(self):
        pass

    def make_task(self):
        """

        """
        pass

    def check_constraint(self, constraint: Constraint):
        """
        Проверяет, имеет ли ограничение вид типа (-1)*x_i <= 0
        """
        pass

def make_task_canonical(task: Task) -> Task:
    """
    Переделывает задачу в каноническую путем добавления переменных
    """
    pass

if __name__ == "__main__":
    list_ex = [
        [1, 2, 3],
        [4, 5 ,6],
        [7, 8, 9],
    ]

    print(list_ex[1:2][0])

    numpy_list_ex = np.array(list_ex)
    numpy_list_ex[:, -1] = np.array([1, 2, 3])
    print(numpy_list_ex)