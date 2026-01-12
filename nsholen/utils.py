import requests
from typing import Any
import time
from .exceptions import UserAgentError

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
    
    def __call__(self, key: str | None = None, default: Any | None = None):
        if key:
            return self.headers.get(key, default)
        return self.headers

    def update_headers(self, headers: dict[str, str]) -> None:
        self.headers.update(headers)
    def remove_header(self, key: str) -> None:
        del self.headers[key]
    def clear_all(self) -> None:
        self.headers = {}

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
                    elif isinstance(args, str):
                        return args
                    elif isinstance(args, dict):
                        items = separator.join([f"{k}={parse_arguments("+", v)}" for k, v in args.items()])
                        return items
        params = self.arguments
        key_params = self.key_arguments
        
        final_query = "q="
        final_query += f"{parse_arguments("+", params)}"
        if key_params:
            final_query += f";{parse_arguments(";", key_params)}"
        return final_query

class UrlManager:
    def __init__(self):
        pass
    
    def build_url(self,
            base: str,
            path: list[str] = None,
            unique_slug: tuple[str, str] | None = None,
            querystring: QueryString | None = None,
            api_version: int = 12) -> str:
                final_url = base
                query = querystring
                sep = "?"
                if path:
                    parsed_path = "/".join(path)
                    final_url += f"/{parsed_path}"
                if unique_slug:
                    sep = "&"
                    key: str = unique_slug[0]
                    value: str = unique_slug[1]
                    final_url += f"?{key}={value}"
                if query:
                    final_url += f"{sep}{query.build()}"
                final_url += f"&v={api_version}"
                return final_url

class AuthManager:
    def __init__(self):
        self.authentication = {}
    
    def update(self, auth: Auth):
        self.authentication.update(auth.get())
    def current(self) -> dict[str, Any]:
        return self.authentication

class ApiResponse:
    def __init__(self, response):
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
        return f"[Ratelimit-Policy: {max_requests};{sleep}]"
    
    def check_limit(self,
                    resp_headers: dict[str, str]):
        requests_left: int = int(resp_headers["Ratelimit-Remaining"])
        print(self)
        print(f"{requests_left=}")
        sleep_span: int = self.policy[1]
        if requests_left <= 1:
            time.sleep(sleep_span)

class Connection:
    def __init__(self):
        self.headers: Headers = Headers()
        self.authManager = AuthManager()
        self.ratelimit = RateLimit()
    
    def make_request(self,
                     url: str) -> ApiResponse:
        def validate():
            user_agent: str | None = self.headers("User-Agent")
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
            return ApiResponse(response)
        validate()
        apiResponse: ApiResponse = do_request()
        process_response_headers(apiResponse)
        return apiResponse
    
    def set_request_headers(self,
                            new_headers: Headers) -> None:
        self.headers = new_headers

if __name__ == "__main__":
    wrapper = Connection()
    headers = Headers({"User-Agent": "NsHolen 0.0.0.dev0 (By: Orlys)"})
    wrapper.set_request_headers(headers)
    url = "https://www.nationstates.net/cgi-bin/api.cgi?nation=testlandia&q=census"
    bruh = wrapper.make_request(url)
    print(bruh.to_dict()["text"])