from pymongo import MongoClient
import os
import json
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv(override=True)

class MongoDBHandler:
    def __init__(self):
        # Initialize MongoDB client and connect to the specified database and collection
        self.client = MongoClient(os.getenv("MONGODB_ATLAS_CLUSTER_URI"))
        self.db = self.client[os.getenv("DB_NAME")]
        self.collection = self.db["Natural_diaster_events"]
        self.stats = str(self.retrieve_stats())
        
    def insert_record(self, record):
        # Insert a single document/record into the collection
        result = self.collection.insert_one(record)
        return result.inserted_id
    
    def insert_record(self, collection, record):
        # Insert a single document/record into the collection
        result = self.db[collection].insert_one(record)
        return result.inserted_id

    def insert_json(self, json_data=None, collection_name=None, file_path=None):
        """
        Inserts the 'features' list from a GeoJSON object into the specified MongoDB collection.
        If `file_path` is provided, the JSON data will be loaded from the file instead.

        Args:
            json_data (dict, optional): The GeoJSON data containing a 'features' list to be inserted. Ignored if `file_path` is provided.
            collection_name (str): The name of the collection where the data should be inserted.
            file_path (str, optional): Path to a file containing the GeoJSON data. If provided, the file's content will be used.

        Returns:
            list: A list of the inserted document IDs.

        Raises:
            ValueError: If neither `json_data` nor `file_path` is provided, or if 'features' is missing.
        """
        if not collection_name:
            raise ValueError("Collection name must be provided.")
        
        # Load JSON data from file if file_path is provided
        if file_path:
            print(f"Attempting to read file from path: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
            except Exception as e:
                raise ValueError(f"Error loading JSON data from file: {e}")
        
        if not json_data:
            raise ValueError("No valid JSON data provided.")
        
        # Ensure the collection exists or use the provided collection name
        collection = self.db[collection_name]
        
        # Check if 'features' exists in the json_data and insert it
        if 'features' in json_data:
            # Insert the list of features into the collection
            result = collection.insert_many(json_data['features'])
            return [str(doc_id) for doc_id in result.inserted_ids]
        else:
            raise ValueError("No 'features' found in the provided GeoJSON data.")


    def retrieve_stats(self):
        # Connect to the 'Statistics' collection within the 'Dragngue' database
        statistics_collection = self.db["Statistics"]
        
        # Retrieve the first record (assuming only one record is present)
        record = statistics_collection.find_one()
        events = self.retrieve_all_records(
          filter_condition=None, collection_name="Natural_diaster_events"
         )
        record["total_number_natural_disasters"] = len(events)
        return record
    def retrieve_all_records(self, filter_condition=None, collection_name=None):
        # Use the provided collection name or default to self.collection
        collection = self.db[collection_name] if collection_name else self.collection
        
        # Retrieve all documents, optionally filtering with a condition
        if filter_condition is None:
            documents = collection.find()
        else:
            documents = collection.find(filter_condition)
        
        all_documents = []
        for doc in documents:
            doc.pop('_id', None)
            doc.pop("embedded_description", None)
            all_documents.append(doc)
        
        return all_documents
    def delete_record(self, filter_condition: dict, collection_name: str):
        """
        Deletes a specific record from the specified collection.

        Args:
            collection_name (str): The name of the collection from which to delete the record.
            filter_condition (dict): The filter condition to identify the record to delete.

        Returns:
            dict: A result summary including the number of documents deleted.
        """
        # Access the specified collection
        collection = self.db[collection_name]
        
        # Delete the document(s) matching the filter condition
        result = collection.delete_one(filter_condition)
        
        if result.deleted_count > 0:
            print(f"Deleted {result.deleted_count} record(s) from the '{collection_name}' collection.")
        else:
            print(f"No matching records found in the '{collection_name}' collection.")
        
        return {
            "deleted_count": result.deleted_count,
            "filter_used": filter_condition,
        }

    
    def delete_all_records(self, collection_name: str):
        """
        Deletes all records within the specified MongoDB collection.

        Args:
            collection_name (str): The name of the collection from which to delete all records.
        
        Returns:
            int: The count of documents deleted.
        """
        collection = self.db[collection_name]
        result = collection.delete_many({})
        print(f"Deleted {result.deleted_count} records from the '{collection_name}' collection.")
        return result.deleted_count

    def google_insert_geojson_features(self, geojson_data):
        # Ensure the data is in a FeatureCollection format
        if geojson_data["type"] != "FeatureCollection":
            raise ValueError("Invalid GeoJSON format: Expected FeatureCollection")

        # Insert each feature in the collection
        inserted_ids = []
        for feature in geojson_data["features"]:
            if feature["type"] == "Feature":
                # Extract properties and geometry
                properties = feature.get("properties", {})
                location = properties.get("location", "")
                coordinates = feature.get("geometry", {}).get("coordinates", [])

                # Create embedding content with severity details
                embedding_content = ", ".join(f"{key}: {value}" for key, value in properties.items())
                
                # Append location, coordinates, severity text, and level
                if location:
                    embedding_content += f", location: {location}"

                severity_text = properties.get("severity_text", "N/A")
                severity_level = properties.get("severity", "N/A")
                embedding_content += f", severity_text: {severity_text}, severity_level: {severity_level}"

                # Generate embedding (assuming the existence of a generate_embedding function)
                
                if coordinates:
                    embedding_content += f", coordinates: {coordinates}"
                feature["description_text"] = embedding_content
                feature["properties"]["category"] = "event"

                # Insert feature as document in MongoDB
                inserted_id = self.collection.insert_one(feature).inserted_id
                inserted_ids.append(inserted_id)
        return inserted_ids