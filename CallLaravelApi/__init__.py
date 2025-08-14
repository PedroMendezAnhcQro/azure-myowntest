import logging
import os
import requests

def main(event_uid: str) -> bool:
    logging.info(f"Llamando al endpoint Laravel con UID: {event_uid}")

    admin_domain = os.environ.get("ADMIN_DOMAIN")
    if not admin_domain:
        logging.error("ADMIN_DOMAIN no está definido")
        return False

    try:
        laravel_url = f"{admin_domain}/api/async-task"
        response = requests.post(laravel_url, json={"eventUID": event_uid}, timeout=10)
        response.raise_for_status()

        data = response.json()
        logging.info(f"Respuesta Laravel: {data}")
        return data.get("should_continue", False)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error al llamar Laravel API: {e}")
        return False
