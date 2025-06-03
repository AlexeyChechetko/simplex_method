class Constraint:

    coefficients: list[float] # Коэффициенты при переменных
    b: float # Правая часть ограничения
    type_of_ineq: str # Тип неравенства

    def __init__(self, coefficients: list[float], b: float, type_of_ineq: str):
        """
        :param coefficients: коэффициенты при x_i
        :param b: правая часть ограничения
        :param type_of_ineq: ">=", "<=", "="
        """
        self.coefficients = coefficients
        self.b = b
        self.type_of_ineq = type_of_ineq

        # Преобразуем ограничение к виду <=
        self.transform()

    def transform(self):
        """
        Трансформирует неравенство в <= или остается просто =
        """
        if self.type_of_ineq == ">=":
            self.coefficients = [-coefficient for coefficient in self.coefficients]
            self.b = -self.b
            self.type_of_ineq = "<="

    def check_constraint(self) -> int:
        """
        Проверяет - имеет ли данное неравенство тип (-1)*x_i <= 0.
        """
        non_zero_indices = [i for i, x in enumerate(self.coefficients) if x != 0]
        if (len(non_zero_indices) == 1) and (self.coefficients[non_zero_indices[0]] < 0) and (self.b == 0):
            return non_zero_indices[0]
        else:
            return -1

    def __repr__(self):
        """
        Выводит преобразованное ограничение в формате (1)*x1 + (0)*x2 + (-3)*x3 <= 4
        :return: строка ограничения
        """
        str_constraint = ""

        for i, coefficient in enumerate(self.coefficients):
            str_constraint += ("(" + str(coefficient) + ")" + "*x" + str(i + 1) + " + ")
        str_constraint = str_constraint.removesuffix("+ ")

        str_constraint += (self.type_of_ineq + " " + str(self.b))

        return str_constraint

if __name__ == "__main__":
    # Пример 1
    coefficients_ex1 = [1, 0, -3]
    b_ex1 = 4
    type_of_ineq_ex1 = "<="

    Constraint_instance1 = Constraint(coefficients_ex1, b_ex1, type_of_ineq_ex1)
    print(Constraint_instance1)
    print(Constraint_instance1.check_constraint())

    # Пример 2
    coefficients_ex2 = [0, 0, -3]
    b_ex2 = 0
    type_of_ineq_ex2 = "=" # TODO: вот такие неравенства считает "хорошими" (0)*x1 + (0)*x2 + (-3)*x3 = 0, но они в целом смысла не несут. Можно считать, что они не вводятся

    Constraint_instance2 = Constraint(coefficients_ex2, b_ex2, type_of_ineq_ex2)
    print(Constraint_instance2)
    print(Constraint_instance2.check_constraint())


