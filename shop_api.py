from datetime import datetime
from urllib.parse import urljoin

import requests


SHOP_HOST = "https://api.moltin.com"

_token_desc = None
_client_id = None


def authenticate(client_id: str) -> None:
    global _client_id, _token_desc

    _client_id = client_id
    _token_desc = None
    get_token()


def get_token() -> str:
    global _token_desc
    if _client_id is None:
        raise ConnectionError("No authentication")
    if _token_desc is not None:
        timestamp = datetime.timestamp(datetime.now())
        expires_timestamp = _token_desc["expires"]
        if timestamp < expires_timestamp:
            return _token_desc["access_token"]

    token_url = urljoin(SHOP_HOST, "/oauth/access_token")
    data = {
        "client_id": _client_id,
        "grant_type": "implicit",
    }
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    _token_desc = response.json()
    return _token_desc["access_token"]


def get_products() -> list:
    products_url = urljoin(SHOP_HOST, "/v2/products")
    header = {
        "Authorization": f"Bearer {get_token()}",
    }
    response = requests.get(products_url, headers=header)
    response.raise_for_status()
    return response.json()["data"]


def get_product(product_id: str) -> dict:
    url = urljoin(SHOP_HOST, f"/v2/products/{product_id}")
    header = {
        "Authorization": f"Bearer {get_token()}",
    }
    response = requests.get(url, headers=header)
    response.raise_for_status()
    return response.json()["data"]


def get_product_image_url(product_id: str) -> str:
    product = get_product(product_id)
    image_id = product["relationships"]["main_image"]["data"]["id"]
    return get_file_url(image_id)


def get_cart(cart_reference: str) -> dict:
    cart_url = urljoin(SHOP_HOST, f"/v2/carts/{cart_reference}")
    header = {
        "Authorization": f"Bearer {get_token()}",
    }
    response = requests.get(cart_url, headers=header)
    response.raise_for_status()
    return response.json()


def get_cart_items(cart_reference: str) -> dict:
    header = {
        "Authorization": f"Bearer {get_token()}",
    }
    url = urljoin(SHOP_HOST, f"/v2/carts/{cart_reference}/items")
    response = requests.get(url, headers=header)
    response.raise_for_status()
    return response.json()


def get_file_url(file_id: str) -> str:
    header = {
        "Authorization": f"Bearer {get_token()}",
    }
    url = urljoin(SHOP_HOST, f"/v2/files/{file_id}")
    response = requests.get(url, headers=header)
    response.raise_for_status()
    link = response.json()["data"]["link"]["href"]
    return link


def add_product_to_cart(
    cart_reference: str,
    product_id: str,
    quantity: int,
) -> dict:
    header = {
        "Authorization": f"Bearer {get_token()}",
    }
    url = urljoin(SHOP_HOST, f"/v2/carts/{cart_reference}/items")
    data = {
        "data": {
            "id": product_id,
            "type": "cart_item",
            "quantity": quantity,
        },
    }
    response = requests.post(url, headers=header, json=data)
    response.raise_for_status()
    return response.json()


def remove_cart_item(cart_reference: str, item_id: str) -> None:
    header = {
        "Authorization": f"Bearer {get_token()}",
    }
    url = urljoin(SHOP_HOST, f"/v2/carts/{cart_reference}/items/{item_id}")
    response = requests.delete(url, headers=header)
    response.raise_for_status()


def create_customer(name: str, email: str) -> str:
    header = {
        "Authorization": f"Bearer {get_token()}",
    }
    url = urljoin(SHOP_HOST, "/v2/customers")
    data = {
        "data": {
            "type": "customer",
            "name": name,
            "email": email,
        },
    }
    response = requests.post(url, headers=header, json=data)
    response.raise_for_status()
    return response.json()


def get_customer(id: str) -> str:
    header = {
        "Authorization": f"Bearer {get_token()}",
    }
    url = urljoin(SHOP_HOST, f"/v2/customers/{id}")
    response = requests.get(url, headers=header)
    response.raise_for_status()
    return response.json()
