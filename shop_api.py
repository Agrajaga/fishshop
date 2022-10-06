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


def get_product_image_url(host: str, token: str, product_id: str) -> str:
    product = get_product(host, token, product_id)
    image_id = product["relationships"]["main_image"]["data"]["id"]
    return get_file_url(host, token, image_id)


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


def get_file_url(host: str, token: str, file_id: str) -> str:
    header = {
        "Authorization": f"Bearer {token}",
    }
    url = urljoin(host, f"/v2/files/{file_id}")
    response = requests.get(url, headers=header)
    response.raise_for_status()
    link = response.json()["data"]["link"]["href"]
    return link


def add_product_to_cart(
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


def remove_cart_item(
    host: str,
    token: str,
    cart_reference: str,
    item_id: str,
) -> None:
    header = {
        "Authorization": f"Bearer {token}",
    }
    url = urljoin(host, f"/v2/carts/{cart_reference}/items/{item_id}")
    response = requests.delete(url, headers=header)
    response.raise_for_status()


def create_customer(
    host: str,
    token: str,
    name: str,
    email: str,
) -> str:
    header = {
        "Authorization": f"Bearer {token}",
    }
    url = urljoin(host, "/v2/customers")
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


def get_customer(
    host: str,
    token: str,
    id: str,
) -> str:
    header = {
        "Authorization": f"Bearer {token}",
    }
    url = urljoin(host, f"/v2/customers/{id}")
    response = requests.get(url, headers=header)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    from pprint import pprint
    load_dotenv()
    host = os.getenv("SHOP_HOST")
    client_id = os.getenv("SHOP_CLIENT_ID")
    implicit_token = authenticate(host, client_id)
    #pprint(get_products(host, implicit_token))
    #print(get_cart_items(host, implicit_token, "my_cart"))
    pprint(get_product(host, implicit_token,
           "dda5bd6a-7216-457c-8a5f-da03b09421ab"))
