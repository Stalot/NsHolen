from decimal import Decimal, localcontext, ROUND_HALF_EVEN

class HandfulTools:
    def __init__(self):
        pass
    def is_real_number(self,
                       string: str):
        """
        Checks if the provided string
        is a real number or not.
        """
        try:
            string = string.replace(",", ".")
            float(string)
            return True
        except ValueError:
            return False
    def scientific_notation_to_decimal(self,
                                       string: str,
                                       prec: int = 16) -> str:
        with localcontext() as lc:
            lc.prec = prec
            return format(Decimal(string), "f")
    def decimal_into_scientific_notation(self,
                                         string: str) -> str:
        return format(Decimal(string), "e")

    def decimal_rounding(self,
                         x: str, 
                         template: str = "0.01",
                         rounding = ROUND_HALF_EVEN):
        with localcontext() as lc:
            try:
                lc.rounding = rounding
                d = Decimal(x)
                return d.quantize(Decimal(template))
            except TypeError:
                raise ValueError(f"'{rounding}' is not a valid rounding")

if __name__ == "__main__":
    handy = HandfulTools()
    print(f"{handy.is_real_number("12.7E4")=}")
    print(f"{handy.scientific_notation_to_decimal("12.7E4")=}")
    print(f"{handy.decimal_into_scientific_notation("127000")=}")
    print(f"{handy.decimal_into_scientific_notation("12.7E4")=}")
    print(f"{handy.decimal_rounding("4.8279")=}")
    