class Constraint:

    number_of_variables: int # Число переменных
    coefficients: list[float] # Коэффициенты при переменных
    b: float # Правая часть ограничения
    type_of_ineq: str # Тип неравенства

    def __init__(self, coefficients: list[float], b: float, type_of_ineq: str):
        """
        :param coefficients: коэффициенты при x_i
        :param b: правая часть ограничения
        :param type_of_ineq: ">=", "<=", "="
        """
        self.number_of_variables = len(coefficients)
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

    def __repr__(self):
        str_constraint = ""

        for i, coefficient in enumerate(self.coefficients):
            str_constraint += ("(" + str(coefficient) + ")" + "*x" + str(i + 1) + " + ")
        str_constraint = str_constraint.removesuffix("+ ")

        str_constraint += (self.type_of_ineq + " " + str(self.b))

        return str_constraint

if __name__ == "__main__":
    coefficients_ex = [1, 0, -3]
    b_ex = 4
    type_of_ineq_ex = "<="

    Constraint_instance = Constraint(coefficients_ex, b_ex, type_of_ineq_ex)
    print(Constraint_instance)



