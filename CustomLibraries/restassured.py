import requests, os
from tenacity import retry, stop_after_attempt, wait_exponential
from .circuitbreaker import CircuitBreaker
from features.helper.logger import logger

class RestAssured:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = ""
        self.headers = {}
        self.body = None
        self.query_params = {}
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

    def given(self):
        return self

    def headers(self, headers):
        self.headers.update(headers)
        return self

    def body(self, body):
        self.body = body
        return self

    def query_params(self, params):
        self.query_params.update(params)
        return self

    def when(self):
        return self

    @retry(stop=stop_after_attempt(int(os.getenv('RETRY_ATTEMPTS', 3))), wait=wait_exponential(multiplier=float(os.getenv('RETRY_MULTIPLIER', 1)), min=int(os.getenv('RETRY_MIN', 4)), max=int(os.getenv('RETRY_MAX', 10))))
    def post(self, endpoint, request_type="json"):
        url = f"{self.base_url}{endpoint}"
        with self.circuit_breaker:
            if request_type.lower() == "xml":
                response = self.session.post(url, headers=self.headers, data=self.body, params=self.query_params)
            elif request_type.lower() == "graphql":
                self.headers["Content-Type"] = "application/json"
                response = self.session.post(url, headers=self.headers, json={"query": self.body}, params=self.query_params)
            else:
                response = self.session.post(url, headers=self.headers, json=self.body, params=self.query_params)

            logger.info(f"Request: POST {url} | Headers: {self.headers} | Body: {self.body}")
            logger.info(f"Response: {response.status_code} | {response.text}")
            response.raise_for_status()
            return response

    @retry(stop=stop_after_attempt(int(os.getenv('RETRY_ATTEMPTS', 3))), wait=wait_exponential(multiplier=float(os.getenv('RETRY_MULTIPLIER', 1)), min=int(os.getenv('RETRY_MIN', 4)), max=int(os.getenv('RETRY_MAX', 10))))
    def get(self, endpoint):
        url = f"{self.base_url}{endpoint}"
        with self.circuit_breaker:
            response = self.session.get(url, headers=self.headers, params=self.query_params)
            logger.info(f"Request: GET {url} | Headers: {self.headers}")
            logger.info(f"Response: {response.status_code} | {response.text}")
            response.raise_for_status()
            return response

    @retry(stop=stop_after_attempt(int(os.getenv('RETRY_ATTEMPTS', 3))), wait=wait_exponential(multiplier=float(os.getenv('RETRY_MULTIPLIER', 1)), min=int(os.getenv('RETRY_MIN', 4)), max=int(os.getenv('RETRY_MAX', 10))))
    def put(self, endpoint, request_type="json"):
        url = f"{self.base_url}{endpoint}"
        with self.circuit_breaker:
            if request_type.lower() == "xml":
                response = self.session.put(url, headers=self.headers, data=self.body, params=self.query_params)
            else:
                response = self.session.put(url, headers=self.headers, json=self.body, params=self.query_params)

            logger.info(f"Request: PUT {url} | Headers: {self.headers} | Body: {self.body}")
            logger.info(f"Response: {response.status_code} | {response.text}")
            response.raise_for_status()
            return response

    @retry(stop=stop_after_attempt(int(os.getenv('RETRY_ATTEMPTS', 3))), wait=wait_exponential(multiplier=float(os.getenv('RETRY_MULTIPLIER', 1)), min=int(os.getenv('RETRY_MIN', 4)), max=int(os.getenv('RETRY_MAX', 10))))
    def delete(self, endpoint):
        url = f"{self.base_url}{endpoint}"
        with self.circuit_breaker:
            response = self.session.delete(url, headers=self.headers, params=self.query_params)
            logger.info(f"Request: DELETE {url} | Headers: {self.headers}")
            logger.info(f"Response: {response.status_code} | {response.text}")
            response.raise_for_status()
            return response

# Example usage:
# response = RestAssured().given().headers({'Authorization': 'Bearer token'}).body({'key':'value'}).when().post('/api', request_type="graphql")