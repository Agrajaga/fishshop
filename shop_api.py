import os

import requests
from dotenv import load_dotenv
from urllib.parse import urljoin

def authenticate(host: str, client_id: str) -> str:
    token_url = urljoin(host, "/oauth/access_token")
    data = {
        "client_id": client_id,
        "grant_type": "implicit",
    }
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def get_products(host: str, token: str) -> list:
    products_url = urljoin(host, "/v2/products")
    header = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(products_url, headers=header)
    response.raise_for_status()
    return response.json()["data"]


def get_product(host: str, token: str, product_id: str) -> dict:
    url = urljoin(host, f"/v2/products/{product_id}")
    header = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(url, headers=header)
    response.raise_for_status()
    return response.json()["data"]


def get_cart(host: str, token: str, cart_reference: str) -> dict:
    cart_url = urljoin(host, f"/v2/carts/{cart_reference}")
    header = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(cart_url, headers=header)
    response.raise_for_status()
    return response.json()


def get_cart_items(host: str, token: str, cart_reference: str) -> dict:
    header = {
        "Authorization": f"Bearer {token}",
    }
    url = urljoin(host, f"/v2/carts/{cart_reference}/items")
    response = requests.get(url, headers=header)
    response.raise_for_status()
    return response.json()


def add_product(
    host: str,
    token: str,
    cart_reference: str,
    product_id: str,
    quantity: int,
) -> dict:
    header = {
        "Authorization": f"Bearer {token}",
    }
    url = urljoin(host, f"/v2/carts/{cart_reference}/items")
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


if __name__ == "__main__":
    load_dotenv()
    host = os.getenv("SHOP_HOST")
    client_id = os.getenv("SHOP_CLIENT_ID")
    implicit_token = authenticate(host, client_id)
    print(get_products(host, implicit_token))
    #print(get_cart_items(host, implicit_token, "my_cart"))
