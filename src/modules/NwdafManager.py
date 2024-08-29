import logging
from pymongo import MongoClient, errors

def get_anomaly_ratio():
    """
    Retrieves the latest anomaly ratio from the 'nwdaf_anomaly_notification' collection.
    
    Returns:
        float: The latest anomaly ratio.
    
    Raises:
        ConnectionError: If there is a failure connecting to MongoDB.
        ValueError: If the required collection or data fields are not found.
        Exception: For other unexpected issues.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logging.getLogger('pymongo').setLevel(logging.WARNING)

    try:
        client = MongoClient('mongodb://localhost:27017/')
        assert client is not None, "Failed to create MongoDB client"

        db = client['notification_db']
        if 'nwdaf_anomaly_notification' not in db.list_collection_names():
            raise ValueError("Collection 'nwdaf_anomaly_notification' not found in the database")

        nwdaf_anomaly_collection = db['nwdaf_anomaly_notification']

        latest_document_cursor = nwdaf_anomaly_collection.find().sort('_id', -1).limit(1)
        latest_document = list(latest_document_cursor) 

        if not latest_document:  # Check if the list is empty
            raise ValueError("No documents found in the 'nwdaf_anomaly_notification' collection")

        latest_document = latest_document[0]  # Access the document

        if 'abnorBehavrs' not in latest_document or not latest_document['abnorBehavrs']:
            raise ValueError("'abnorBehavrs' field is missing or empty in the latest document")

        latest_ratio = latest_document['abnorBehavrs'][0].get('ratio')
        if latest_ratio is None:
            raise ValueError("'ratio' field is missing in the latest 'abnorBehavrs' entry")

        return latest_ratio

    except errors.ServerSelectionTimeoutError as e:
        logger.error("Failed to connect to MongoDB: %s", e)
        raise ConnectionError("Could not connect to MongoDB server")

    except (AssertionError, ValueError, Exception) as e:
        logger.error("An error occurred: %s", e)
        raise e


