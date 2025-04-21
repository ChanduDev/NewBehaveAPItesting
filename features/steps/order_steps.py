import json
from behave import given, when, then
from features.helper.data_utils import load_test_data, substitute_placeholders
from features.helper.mongo_utils import fetch_mongo_data
from features.helper.api_utils import execute_request, extract_json_path
from features.helper.logger import logger

@given('I use the "{api}" env config')
def step_use_env_config(context, api):
    context.api_config = context.config.userdata['env'].get(api)
    if not context.api_config:
        raise ValueError(f"No API config found for: {api}")
    context.api_name = api
    logger.info(f"Using API config: {api}")

@given('I load test data from "{csv_file}"')
def step_load_test_data(context, csv_file):
    context.test_data = load_test_data(f"features/data/{csv_file}")

@given('I fetch MongoDB data from query')
def step_fetch_mongo_data(context):
    context.mongo_data = fetch_mongo_data(context)

@when('I select row {row_index:d} to load the API contract details')
def step_select_row_data(context, row_index):
    context.current_data = context.test_data[row_index]
    for key in ['headers', 'query_parameters', 'body']:
        context.current_data[key] = json.loads(context.current_data.get(key, "{}"))

@when('I override values using mappings')
def step_override_mappings(context):
    for row in context.table:
        source = row['headers.Authorization'] if 'headers.Authorization' in row else row['body.order.cart_id']
        target = row['access_token'] if 'access_token' in row else row['cartId']
        substitute_placeholders(context.current_data, source, target, context)

@when('I send a {http_method} request to "{endpoint}" with API contract details')
def step_send_dynamic_request(context, http_method, endpoint):
    resolved_endpoint = endpoint.format(**context.__dict__)

    headers = context.current_data.get('headers') or {}
    params = context.current_data.get('query_parameters') or {}
    body = context.current_data.get('body') or {}

    response = execute_request(
        method=http_method,
        base_url=context.api_config['base_url'],
        endpoint=resolved_endpoint,
        headers=context.current_data['headers'],
        params=context.current_data['query_parameters'],
        body=context.current_data['body']
    )
    context.response = response

@then('the response status code should be {expected_code:d}')
def step_validate_status_code(context, expected_code):
    actual_code = context.response.status_code
    if actual_code != expected_code:
        logger.error(f"❌ Status code mismatch: Expected {expected_code}, got {actual_code}")
        logger.error(f"Response Body:\n{context.response.text}")
        logger.error(f"Response Headers:\n{context.response.headers}")
    else:
        logger.info(f"✅ Received expected status code: {actual_code}")
    assert actual_code == expected_code, f"Expected: {expected_code}, Got: {actual_code}"

@then('I save response values using mappings')
def step_save_response_values(context):
    json_response = context.response.json()
    for row in context.table:
        json_path = row["body.cart.id"] if "body.cart.id" in row else row["body.order.id"]
        var_name = row["cartId"] if "cartId" in row else row["orderId"]
        value = extract_json_path(json_response, json_path)
        context.__dict__[var_name] = value
        logger.info(f"✅ Saved variable '{var_name}' with value: {value}")

    filtered_vars = {k: v for k, v in context.__dict__.items() if k not in ['config', 'response']}
    logger.info(f"🔍 Current Context Variables: {filtered_vars}")

@then('I validate response values using mappings')
def step_validate_response_values(context):
    json_response = context.response.json()
    for row in context.table:
        expected = row['success']
        actual = extract_json_path(json_response, row['body.payment.status'])
        assert actual == expected, f"Expected {expected}, got {actual}"