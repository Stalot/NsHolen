from .utils import QueryString, ApiResponse, UrlManager, Headers, Connection
from decimal import Decimal, localcontext, InvalidOperation, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN, ROUND_UP, ROUND_DOWN

class HandfulTools:
    def __init__(self):
        pass
    def is_real_number(self,
                       string: str):
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

class NsHolen:
    """
    NsHolen is a python libraby dedicated to simplify the repetitive steps of developing wrappers for the NationStates API, such as query management, while giving you liberty
    """
    def __init__(self) -> None:
        self._urlManager = UrlManager()
        self._connection = Connection()
    def url_manager(self) -> UrlManager:
        return self._urlManager
    def querystring(self,
                    args: list[str] | None = None,
                    kwargs: dict[str, str] | None = None) -> QueryString:
        return QueryString(args, kwargs)
    def connection(self):
        return self._connection