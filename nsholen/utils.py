import requests
from typing import Any, Callable, Optional
import xmltodict

def build_shards_url(nation_name: Optional[str] = None,
                     region_name: Optional[str] = None,
                     shards: Optional[list[str]] = None,
                     params: Optional[dict[str, str]] = None):
    base: str = "https://www.nationstates.net/cgi-bin/api.cgi"
    new_url: str = base
    if nation_name and region_name:
        raise ValueError("You can only set one name.")

    query_string = ""
    if shards:                                                      query_string = f"&q={'+'.join([s for s in shards])}"
    if params:
        query_string += f";{";".join([f"{k}={v}" for k, v in params.items()])}"
    if nation_name:
        new_url += f"?nation={nation_name}"
    elif region_name:
        new_url += f"?region={region_name}"
    else:
        query_string = query_string.replace("&q", "q")
        new_url += "?"
    new_url += query_string
    return new_url

class ApiResponse():
    def __init__(self,
                 resp_object: requests.Response):
        self.status_code: int = resp_object.status_code
        self.text: str = resp_object.text

    def _xml_to_dict(self, xml_string: str):
        def post_processing(path, key, value):
            new_key = key.lower()
            return (new_key, value)
        return xmltodict.parse(xml_string,
                               attr_prefix="",
                               postprocessor=post_processing)

    def as_dict(self):
        return {
            "status_code": self.status_code,
            "text": self.text,
            "data": self._xml_to_dict(self.text)
        }

    def __str__(self):
        return f"ApiResponse[{self.status_code}]"

class NationAuth(requests.auth.AuthBase):
    def __init__(self,
                 nation_name: str,
                 password: Optional[str] = None,
                 autologin: Optional[str] = None):
        self.nation_name: str = nation_name
        self.password: Optional[str] = password
        self.autologin: Optional[str] = autologin

    def __call__(self, r: requests.models.PreparedRequest):
        if self.password:
            r.headers["x-password"] = self.password
        if self.autologin:
            r.headers["x-autologin"] = self.autologin
        return r

class Connection:
    def __init__(self) -> None:
        pass

    def make_request(self,
                     url: str,
                     headers: dict[str, str],
                     auth: NationAuth):
        response: ApiResponse = ApiResponse(
            requests.get(url,
                         headers=headers,
                         auth=auth
            )
        )
        if response.status_code != 200:
            raise ValueError(response.status_code)
        return response

if __name__ == "__main__":
    pass
