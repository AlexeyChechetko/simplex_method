from constraint import Constraint

class SystemOfConstraints:

    constraints: list[Constraint] # Список ограничений
    number_of_constraints: int # Количество ограничений
    A: list[list[float]] # Матрица коэффициентов при переменных в системе ограничений
    b: list[float] # Вектор значений правых частей ограничений

    def __init__(self, constraints: list[Constraint]):
        self.constraints = constraints
        self.number_of_constraints = len(constraints)

        self.A = []
        self.b = []
        self.obtain_matrix_a()
        self.obtain_vector_b()

    def obtain_matrix_a(self):
        """
        Получаем из системы ограничений матрицу коэффициентов A
        """
        for constraint in self.constraints:
            self.A.append(constraint.coefficients)

    def obtain_vector_b(self):
        """
        Получаем из системы ограничений вектор правых частей b
        """
        for constraint in self.constraints:
            self.b.append(constraint.b)

    def __repr__(self):
        str_system_of_constraints = "##########   Constraints   ##########\n"

        for constraint in self.constraints:
            str_system_of_constraints += str(constraint) + "\n"

        str_system_of_constraints += "##########   A   ##########\n"
        str_system_of_constraints += str(self.A) + "\n"

        str_system_of_constraints += "##########   b   ##########\n"
        str_system_of_constraints += str(self.b) + "\n"

        return str_system_of_constraints


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

    # Система ограничений
    SystemOfConstraints_instance = SystemOfConstraints([Constraint_instance1, Constraint_instance2, Constraint_instance3])
    print(SystemOfConstraints_instance)