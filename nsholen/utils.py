import requests
from typing import Any, Callable
import time
from .exceptions import UserAgentError, RequestFail
import re
from urllib.parse import urlparse

class Auth:
    def __init__(self, **kwargs):
        self.data = {}
        self.data.update(kwargs)

    def __call__(self, **kwargs):
        self.data.update(kwargs)
    
    def get(self, key: str | None = None):
        try:
            return self.data if not key else self.data[key]
        except KeyError:
            raise ValueError(f"'{key}' not found")

    def update(self, data: dict[str, Any]):
        self.data.update(data)

class Headers:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers if headers else {}  
    def __call__(self):
        return self.headers
    def __getitem__(self,
                    key: str,
                    default: Any = None):
        try:
            return self.headers[key]
        except:
            return default
    def __setitem__(self,
                    key: str,
                    value: str):
         self.headers[key] = value   
    def __delitem__(self, key: str):
        del self.headers[key]
    def __len__(self):
        return len(self.headers.keys())

    def update(self, headers: dict[str, str]) -> None:
        if not isinstance(headers, dict):
            raise TypeError(f"headers must be of type dict, not {type(headers).__name__}")
        self.headers.update(headers)
    def remove(self, key: str) -> None:
        del self.headers[key]
    def clear_all(self) -> None:
        self.headers = {}
    def get_all(self) -> dict[str, str]:
        return self.headers

class QueryString:
    def __init__(self,
                 args: list[str] | None = None,
                 kwargs: dict[str, str] | None = None):
        self.arguments = args if args else []
        self.key_arguments = kwargs if kwargs else {}
    
    def __str__(self):
        return "QueryString()"

    def set_arguments(self, args: list[str], kwargs: dict[str | list[str]] | None = None) -> None:
        if args:
            self.arguments = args
        if kwargs:
            for k, v in kwargs.items():
                self.key_arguments.update({k: v})
        
    def build(self):
        def parse_arguments(separator: str, args: list[str] | dict[str, str]) -> str:
                    if isinstance(args, list):
                        return separator.join(args)
                    if isinstance(args, str):
                        return args
                    if isinstance(args, dict):
                        items = separator.join([f"{k}={parse_arguments("+", v)}" for k, v in args.items()])
                        return items
                    raise TypeError(f"args cannot be of type {type(args).__name__}")
        if not self.arguments:
            raise ValueError("Couldn't build querystring! QueryString() needs valid values, which must be of type str or list[str]")
        if not isinstance(self.arguments, (list, str)):
            raise TypeError("Couldn't build querystring! QueryString() values must be of type str or list[str]")
        if self.key_arguments and not isinstance(self.key_arguments, dict):
            raise TypeError("Couldn't build querystring! QueryString() key values must be of type dict[str, str | list[str]]")
        params = self.arguments
        key_params = self.key_arguments
        
        final_query = "q="
        final_query += f"{parse_arguments("+", params)}"
        if key_params:
            final_query += f";{parse_arguments(";", key_params)}"
        return final_query

class Url:
    def __init__(self,
                 path: str | list[str] = "cgi-bin/api.cgi",
                 slugs: dict[str, str] | None = None,
                 querystring: QueryString | None = None,
                 api_version: int = 12):
        self.path: str | list[str] = path
        self.slugs: dict[str, str] | None = slugs
        self.querystring: QueryString | None = querystring
        self.api_version: int = api_version
        
        if not isinstance(self.api_version, int):
            raise TypeError("api_version must be a integer, not {type(self.api_version).__name__}")
        if not isinstance(self.path, (str, list)):
            raise TypeError(f"path must be of type str or list[str], not {type(self.path).__name__}")
        if not isinstance(self.slugs, dict):
            raise TypeError(f"slugs must be of type dict, not {type(self.slugs).__name__}")
        if not isinstance(self.querystring, QueryString):
            raise TypeError(f"querystring must be a QueryString() object, not {type(self.querystring).__name__}")
    
    def __call__(self):
        return self.build()
    
    def build(self,
              base: str = "https://www.nationstates.net"):
        def parse_path(path: str | list[str]):
            parsed_path: str | list[str] = path
            if isinstance(parsed_path, list):
               parsed_path = "/".join(path)
            parsed_path = f"/{parsed_path}"
            return parsed_path
        def validate(url: str):
            result = urlparse(url)
            if result.scheme != "https":
                raise ValueError(f"Scheme must be https, not '{result.scheme}'") 
            if result.netloc != "www.nationstates.net":
                raise ValueError(f"Only 'www.nationstates.net' is allowed. '{result.netloc}' is untrusted")
            if re.findall(r"//+?", result.path):
                raise ValueError(f"'{result.path}'is not a valid path")
        final_url = base
        query = self.querystring
        sep = "?"
        final_url += parse_path(self.path)
        if self.slugs:
           sep = "&"
           slugs: str = sep.join([f"{k}={v}" for k, v in self.slugs.items()])
           slugs = slugs.replace(" ", "%20")
           final_url += f"?{slugs}"
        if query:
           final_url += f"{sep}{query.build()}"
        final_url += f"&v={self.api_version}"
        validate(final_url)
        return final_url

class AuthManager:
    def __init__(self):
        self.authentication = {}
    
    def update(self, auth: Auth):
        self.authentication.update(auth.get())
    def current(self) -> dict[str, Any]:
        return self.authentication

class ApiResponse:
    def __init__(self,
                 response):
        self.status_code: int = response.status_code
        self.text: str = response.text
        self.content: bytes = response.content
        self.headers: Headers = Headers(response.headers)

    def status(self) -> int:
        return self.status_code

    def sucessfull(self):
        return self.status_code == 200

    def to_dict(self) -> dict[str, Any]:
        return {"status_code": self.status_code,
                "content": self.content,
                "text": self.text,
                "headers": self.headers()
                }
    
    def __str__(self):
        return f"[{self.status()}]"


class RateLimit:
    def __init__(self,
                 policy: tuple[int, int] = (50, 30)):
        self.policy: tuple[int, int] = policy
    
    def __str__(self):
        max_requests: int = self.policy[0]
        sleep: int = self.policy[1]
        return f"[RateLimit: {max_requests};{sleep}]"
    
    def check_limit(self,
                    resp_headers: dict[str, str]):
        def sleep_conditions():
            retry_after: str | None = resp_headers.get('Retry-After') 
            retry_after: int | None = int(retry_after) if retry_after else None
            requests_left: int = int(resp_headers["Ratelimit-Remaining"])
            sleep_span: int = self.policy[1]
            if retry_after:
                time.sleep(retry_after)
            if requests_left <= 1:
                time.sleep(sleep_span)
        sleep_conditions()

class Connection:
    def __init__(self):
        self.headers: Headers = Headers()
        self.authManager = AuthManager()
        self.ratelimit = RateLimit()
    
    def make_request(self,
                     url: str,
                     raise_exception: bool = False) -> ApiResponse:
        def validate():
            user_agent: str | None = self.headers["User-Agent"]
            if not user_agent:
                raise UserAgentError("No user agent provided!")
            if not len(user_agent) > 16:
                raise UserAgentError("The user agent provided is too short")
        def process_response_headers(apiResponse) -> None:
            resp_data = apiResponse.to_dict()
            headers = resp_data["headers"]
            self.ratelimit.check_limit(headers)
        def do_request():
            response = requests.get(url, headers=self.headers())
            if raise_exception and not response.status_code == 200:
                raise RequestFail(response.status_code)
            return ApiResponse(response)
        validate()
        apiResponse: ApiResponse = do_request()
        process_response_headers(apiResponse)
        return apiResponse
    
    def set_request_headers(self,
                            new_headers: Headers) -> None:
        self.headers = new_headers

if __name__ == "__main__":
    q = QueryString("numnations")
    url = Url("cgi-bin/api.cgi/",
              {"nation": "The Ultimate Hero"},
              querystring=q)
    print(url())