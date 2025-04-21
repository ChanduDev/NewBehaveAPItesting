import os
import json
import yaml
import datetime
from behave import fixture, use_fixture
from helper.logger import logger
from helper.core_utils import should_skip_scenario

@fixture
def load_env_config(context):
    logger.info(">>> Load Env Config")
    env = context.config.userdata.get('TEST_ENV', os.getenv('ENV', 'dev'))
    with open('config/env_config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    context.config.userdata['env'] = config[env]
    retry_config = config.get('retry_settings', {})
    os.environ['RETRY_ATTEMPTS'] = str(retry_config.get('retry_attempts', 3))
    os.environ['RETRY_MULTIPLIER'] = str(retry_config.get('retry_multiplier', 1))
    os.environ['RETRY_MIN'] = str(retry_config.get('retry_min', 4))
    os.environ['RETRY_MAX'] = str(retry_config.get('retry_max', 10))

def before_all(context):
    use_fixture(load_env_config, context)
    logger.info(">>> BeforeAll")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    allure_dir = f"reports/allure-results/{timestamp}"
    if not os.path.exists(allure_dir):
        os.makedirs(allure_dir)
    context.config.userdata['allure_dir'] = allure_dir
    logger.info(f"Allure reports will be generated at {allure_dir}")

def before_scenario(context, scenario):

    # Handle test_filter.json inclusion
    logger.info(f"Evaluating scenario: {scenario.name}")

    # Handle @skip tag to explicitly skip scenarios
    for tag in scenario.tags:
        if tag.strip().lower().startswith("skip"):
            logger.info(f"Scenario '{scenario.name}' skipped due to @skip tag")
            scenario.skip("Skipped explicitly by @skip tag")
            return

    # Handle test_filter.json inclusion
    filter_path = 'test_filter.json'
    if os.path.exists(filter_path):
        with open(filter_path, 'r') as f:
            filters = json.load(f)
        included = filters.get('include', [])
        logger.info(f"Scenario filter active: include = {included}")
        if included and scenario.name not in included:
            logger.info(f"Scenario '{scenario.name}' not listed in test_filter.json. Skipping.")
            scenario.skip("Skipped due to test_filter.json")
            return

    # Handle @if: expression tag skipping
    if should_skip_scenario(context):
        logger.info(f"Scenario '{scenario.name}' skipped due to unmet @if: tag condition")
        scenario.skip("Skipped due to unmet @if: tag condition")
        return

    logger.info(f"Scenario '{scenario.name}' passed all skip checks and will execute.")

def after_scenario(context, scenario):
    if scenario.status == "failed":
        logger.error(f"Scenario '{scenario.name}' failed.")
    else:
        logger.info(f"Scenario '{scenario.name}' completed successfully.")