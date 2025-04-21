from CustomLibraries.restassured import RestAssured
from features.helper.logger import logger

def execute_request(method, base_url, endpoint, headers, params, body):
    client = RestAssured()
    client.base_url = base_url
    client = client.given().headers(headers).query_params(params).body(body).when()

    logger.info(f"Executing {method.upper()} request to {endpoint}")
    if method.lower() == 'post':
        return client.post(endpoint)
    elif method.lower() == 'get':
        return client.get(endpoint)
    elif method.lower() == 'put':
        return client.put(endpoint)
    elif method.lower() == 'delete':
        return client.delete(endpoint)
    else:
        raise ValueError(f"Unsupported method: {method}")

def validate_response(response, expected_status):
    actual_status = response.status_code
    assert actual_status == expected_status, f"Expected status {expected_status}, got {actual_status}"

def extract_json_path(json_obj, path):
    try:
        keys = path.split('.')
        for key in keys:
            if isinstance(json_obj, list):
                json_obj = json_obj[int(key)]
            else:
                json_obj = json_obj[key]
        return json_obj
    except (KeyError, IndexError, ValueError, TypeError) as e:
        raise ValueError(f"Failed to extract path '{path}': {e}")