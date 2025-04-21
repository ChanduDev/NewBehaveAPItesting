import csv
import json

def load_test_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

def substitute_placeholders(data_dict, source_key, target_key, context):
    target_value = context.mongo_data.get(target_key) or context.__dict__.get(target_key)
    for section in data_dict:
        if isinstance(data_dict[section], dict):
            data_dict[section] = _replace_value_recursive(data_dict[section], source_key, target_value)

def _replace_value_recursive(obj, source_key, target_value):
    if isinstance(obj, dict):
        return {
            k: _replace_value_recursive(v, source_key, target_value)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [
            _replace_value_recursive(item, source_key, target_value) for item in obj
        ]
    elif isinstance(obj, str) and source_key in obj:
        return obj.replace(source_key, target_value)
    return obj