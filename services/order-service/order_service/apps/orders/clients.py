import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from django.conf import settings


class ServiceUnavailableError(Exception):
    """Raised when downstream service is unavailable"""
    pass


class InsufficientStockError(Exception):
    """Raised when product service reports insufficient stock"""
    pass


def create_session_with_retries() -> requests.Session:
    """Create requests session with automatic retries"""
    session = requests.Session()

    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    )

    adapter = HTTPAdapter(max_retries=retry)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


class ProductServiceClient:
    """Client for communicating with Product Service"""

    def __init__(self):
        if not getattr(settings, "INTERNAL_SECRET", None):
            raise ValueError("INTERNAL_SECRET is not configured")

        if not getattr(settings, "PRODUCT_SERVICE_URL", None):
            raise ValueError("PRODUCT_SERVICE_URL is not configured")

        self.base_url = settings.PRODUCT_SERVICE_URL.rstrip("/")
        self.timeout = getattr(settings, "SERVICE_REQUEST_TIMEOUT", 10)

        self.session = create_session_with_retries()

        self.headers = {
            "X-Internal-Secret": settings.INTERNAL_SECRET,
            "Content-Type": "application/json",
        }

    def get_product(self, product_id: str) -> dict | None:
        """Fetch product details from product service"""
        try:
            resp = self.session.get(
                f"{self.base_url}/api/products/{product_id}/",
                headers=self.headers,
                timeout=self.timeout,
            )

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.ConnectionError:
            raise ServiceUnavailableError("Product service unavailable")

        except requests.exceptions.Timeout:
            raise ServiceUnavailableError("Product service timed out")

        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(str(e))

    def reserve_stock(self, product_id: str, quantity: int) -> dict:
        """Reserve stock in product service"""
        try:
            resp = self.session.post(
                f"{self.base_url}/api/products/{product_id}/reserve_stock/",
                json={"quantity": quantity},
                headers=self.headers,
                timeout=self.timeout,
            )

            if resp.status_code == 400:
                data = resp.json()
                raise InsufficientStockError(
                    data.get("error", "Insufficient stock")
                )

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.ConnectionError:
            raise ServiceUnavailableError("Product service unavailable")

        except requests.exceptions.Timeout:
            raise ServiceUnavailableError("Product service timed out")

        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(str(e))