import json
from pymongo import MongoClient
from features.helper.logger import logger     

def fetch_mongo_data(context):
    mongo_cfg = context.config.userdata['env'].get('mongodb', {})
    if not mongo_cfg.get('mongo_uri'):
        logger.warning("MongoDB config not provided. Using fallback JSON.")
        return _load_fallback_json()

    try:
        client = MongoClient(mongo_cfg['mongo_uri'], serverSelectionTimeoutMS=20000)
        db = client[mongo_cfg['db_name']]
        collection = db[mongo_cfg['collection']]
        document = collection.find_one({})  # adjust query as needed
        logger.info("MongoDB document fetched successfully")
        return document or {}

    except Exception as e:
        logger.warning(f"Mongo fetch failed. Falling back to JSON. Reason: {str(e)}")
        return _load_fallback_json()

def _load_fallback_json():
    try:
        with open("features/data/default_mongo.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        from features.helper.logger import logger
        logger.error(f"Fallback to default_mongo.json failed: {str(e)}")
        return {}
