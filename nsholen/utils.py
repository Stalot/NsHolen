import requests
from urllib.parse import quote_plus, urljoin, urlunparse
from typing import Any, Callable, Optional
import urllib

def build_shards_url(nation_name: Optional[str] = None,
                     region_name: Optional[str] = None,
                     shards: Optional[list[str]] = None,
                     params = None):
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

def make_request(url: str,
                 headers: dict[str, str]):
    req: bytes = urllib.request.Request(url,
                                        headers=headers)
    response: str = urllib.request.urlopen(req).read().decode("UTF-8", "LATIN-1")
    return response

if __name__ == "__main__":
    pass
