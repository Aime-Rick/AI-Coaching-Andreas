import os
from dotenv import load_dotenv
import tempfile
from openai import OpenAI
load_dotenv()
from backend.files.utils import get_file_list, download_file

client = OpenAI()


def create_vector_store(bucket_folder: str, bucket="documents"):

    vector_store = client.vector_stores.create(
        name="temporary_vector_store",
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        list_of_files = get_file_list(bucket, bucket_folder)
        for file in list_of_files:
            # Extract filename from URL or set manually
            filename = os.path.join(temp_dir, file["name"])
            
            # Download the file to the temporary directory
            bucket_file_path = os.path.join(bucket_folder, file["name"])
            download_file(filename, bucket_file_path)
            

            print(f"File downloaded to: {filename}")
            # Upload the file to the vector store

            client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store.id,
                file=open(filename, "rb")
            )

    return vector_store.id

def delete_vector_store(store_id: str):
    """Deletes a vector store by its ID."""
    client.vector_stores.delete(
        vector_store_id=store_id
    )