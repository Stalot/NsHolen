from typing import Any

class UserAgentError(Exception):
    """
    Exception called for invalid
    user agents.
    """
    ...

class RequestFail(Exception):
    def __init__(self,
                 status_code: int | str,
                 e: Any = None):
        def status_context(code: str | int):
            contexts = {400: "Bad Request",
                        403: "Forbidden",
                        404: "Not Found",
                        429: "Too Many Requests",
                        503: "Service Unavailable"
                        }
            i: int = int(code)
            result = f"[{code}]"
            if i in contexts:
                result += " " + contexts[i]
            if e:
                result += f" – {e}"
            return result
        msg = status_context(status_code)
        super().__init__(msg)

if __name__ == "__main__":
    raise RequestFail(404, f"Unable to find 'Orlis'")