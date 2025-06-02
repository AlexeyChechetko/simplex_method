from constraint import Constraint

class SystemOfConstraints:

    constraints: list[Constraint] # Список ограничений
    number_of_constraints: int # Количество ограничений
    A: list[list[float]] # Матрица коэффициентов при переменных в системе ограничений
    b: list[float] # Вектор значений правых частей ограничений
    indices_of_non_good_variables: list[int] # Массив индексов переменных, для которых нет неравенства (-1)*x_i <= 0
    indices_of_non_good_constraints: list[int] # Массив индексов ограничений типа (-1)*x_i <= 0, которые не войду в матрицу A и вектор b

    def __init__(self, constraints: list[Constraint]):
        self.constraints = constraints
        self.number_of_constraints = len(constraints)

        self.indices_of_non_good_variables = list(range(len(self.constraints[0].coefficients)))
        self.indices_of_non_good_constraints = list(range(len(self.constraints)))
        self.check_variables_and_constraints()

        self.A = [] * len(self.indices_of_non_good_constraints)
        self.b = []
        self.obtain_matrix_a()
        self.obtain_vector_b()

    def obtain_matrix_a(self):
        """
        Получаем из системы ограничений матрицу коэффициентов A
        """
        for i in self.indices_of_non_good_constraints:
            self.A.append(self.constraints[i].coefficients)

    def obtain_vector_b(self):
        """
        Получаем из системы ограничений вектор правых частей b
        """
        for i in self.indices_of_non_good_constraints:
            self.b.append(self.constraints[i].b)

    def check_variables_and_constraints(self):
        """
        Проверяет каждое неравенство в системе.
        Если встретили неравенство типа (-1)*x_i <= 0, то удаляем из массива self.indices_of_non_good_variables индекс i
        """
        for i, constraint in enumerate(self.constraints):
            variable_index = constraint.check_constraint()
            if variable_index != -1: # Если ограничение типа (-1)*x_i <= 0
                self.indices_of_non_good_variables.pop(variable_index)
                self.indices_of_non_good_constraints.pop(i)

    def __repr__(self):
        str_system_of_constraints = "##########   Constraints   ##########\n"

        for constraint in self.constraints:
            str_system_of_constraints += str(constraint) + "\n"

        str_system_of_constraints += "##########   A   ##########\n"
        str_system_of_constraints += str(self.A) + "\n"

        str_system_of_constraints += "##########   b   ##########\n"
        str_system_of_constraints += str(self.b) + "\n"

        str_system_of_constraints += "##########   indices_of_non_good_variables   ##########\n"
        str_system_of_constraints += str(self.indices_of_non_good_variables) + "\n"

        return str_system_of_constraints


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

    # Система ограничений
    SystemOfConstraints_instance = SystemOfConstraints([Constraint_instance1, Constraint_instance2, Constraint_instance3])
    print(SystemOfConstraints_instance)