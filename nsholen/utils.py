import requests
from requests import Session
from typing import Any, Callable
import time
from .exceptions import UserAgentError, RequestFail
import re
from urllib.parse import urlparse
from pprint import pprint

class Headers:
    def __init__(self, headers: dict[str, Any] | None = None):
        self.headers = {}  
        if headers:
            self.update(headers)
    def __call__(self):
        return self.headers
    def __getitem__(self,
                    key: str):
        key: str = str(key).lower()
        return self.headers[key]
    def __setitem__(self,
                    key: str,
                    value: str):
        key: str = str(key).lower()
        self.headers[key] = value   
    def __delitem__(self, key: str):
        key: str = str(key).lower()
        del self.headers[key]
    def __len__(self):
        return len(self.headers.keys())

    def update(self, new_headers: dict[str, str]) -> None:
        if not isinstance(new_headers, dict):
            raise TypeError(f"new_headers must be of type dict, not {type(new_headers).__name__}")
        new_headers = {str(k).lower(): str(v) for k, v in new_headers.items()}
        self.headers.update(new_headers)
    def clear_all(self) -> None:
        self.headers = {}
    def get_all(self) -> dict[str, str]:
        return self.headers
    def get(self,
            key: str,
            default = None):
        try:
            key: str = str(key).lower()
            return self.headers[key]
        except KeyError:
            return default

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
    def __str__(self):
        return "Url()"
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
    
    def update(self, auth: dict[str, str]):
        self.authentication.update(auth)
    def auth_headers(self,
                     headers: Headers):
        password: str | None = headers.get("x-password")
        autologin: str | None = headers.get("X-Autologin")
        pin: str | None = headers.get("x-pin")
        
        auth: dict[str, str] = {}
        if password:
            auth["x-password"] = password
        if autologin:
            auth["x-autologin"] = autologin
        if pin:
            auth["x-pin"] = pin
        
        self.update(auth)
    def current(self) -> Headers:
        return Headers(self.authentication)

class ApiResponse:
    def __init__(self,
                 response):
        self.status_code: int = response.status_code
        self.text: str = response.text
        self.content: bytes = response.content
        self.headers: Headers = Headers(dict(response.headers))
       
    def status(self) -> int:
        return self.status_code

    def sucessfull(self):
        return self.status_code == 200

    def to_dict(self) -> dict[str, Any]:
        return {"status_code": self.status_code,
                "content": self.content,
                "text": self.text,
                "headers": self.headers
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
                    resp_headers: Headers):
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
    def __init__(self,
                 use_session: bool = False):
        self.use_session: bool = use_session
        self.default_headers: Headers = Headers()
        self.authManager = AuthManager()
        self.ratelimit = RateLimit()
        self._session = Session()
    
    
    def make_request(self,
                     url: str,
                     raise_exception: bool = False) -> ApiResponse:
        def validate():
            user_agent: str | None = self.default_headers["User-Agent"]
            if not user_agent:
                raise UserAgentError("No user agent provided!")
            if not len(user_agent) > 16:
                raise UserAgentError("The user agent provided is too short")
        def process_response_headers(apiResponse) -> None:
            resp_data: dict[str, Any] = apiResponse.to_dict()
            headers: Headers = resp_data["headers"]
            
            # RateLimiting Logic
            self.ratelimit.check_limit(headers)
            
            # Updates authentication
            self.authManager.auth_headers(headers)
            self.set_request_headers(self.authManager.current())
        def do_request():
            if not self.use_session:
                response = requests.get(url, headers=self.default_headers())
            else:
                response = self._session.get(url)
            if raise_exception and not response.status_code == 200:
                raise RequestFail(response.status_code)
            return ApiResponse(response)
        validate()
        apiResponse: ApiResponse = do_request()
        process_response_headers(apiResponse)
        return apiResponse
    
    def update_auth(self,
                    password: str):
        auth: dict[str, str] = {"X-Password": password}
        self.set_request_headers(Headers(auth))
    
    def set_request_headers(self,
                            new_headers: Headers) -> None:
        if not isinstance(new_headers, Headers):
            raise TypeError(f"new_headers must be a Headers() object, not {type(new_headers).__name__}")
        self.default_headers.update(new_headers())
        self._session.headers.update(new_headers())

if __name__ == "__main__":
    pass