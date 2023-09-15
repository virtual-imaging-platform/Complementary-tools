import os
import json
import shutil
import tempfile
import requests
import subprocess
import configparser
import argparse

"""
Script: ZenodoUploader

Author: Alexandre Cornier
Date: 13/09/2023

Description:
This script automates the process of uploading files to Zenodo, a platform for sharing scientific data. 
It utilizes Zenodo's API to create a new deposition, upload files to it, 
update the metadata of the deposition, and finally publish it. Additionally, it first downloads 
the files via Grida before uploading them to Zenodo.

Required Parameters:
1. ACCESS_TOKEN: Your personal Zenodo access token. Never share this token publicly.
    - To be defined in the config.ini file under the [SETTINGS] section.
    
2. GRIDA_DIRECTORY: The path to your Grida directory.
    - To be defined in the config.ini file under the [SETTINGS] section.

3. files_to_download: A list of files to be downloaded via Grida for subsequent upload to Zenodo.
    - To be defined in the data.json file.

4. metadata: Metadata associated with the Zenodo deposition like title, upload type, description, etc.
    - To be defined in the data.json file.

Usage:
Once parameters are set, run the script to download files via Grida and auto-upload them to Zenodo.

Note:
Ensure the path to the Grida directory is accurate and that your Zenodo token is valid.
"""

class ZenodoUploader:

    # The constructor is used to initialize a new instance of the class.
    def __init__(self, access_token):
        # BASE_URL is the base URL of the Zenodo API.
        self.BASE_URL = "https://sandbox.zenodo.org/api/deposit/depositions"
        # Headers for HTTP requests.
        self.headers = {"Content-Type": "application/json"}
        # Parameters for HTTP requests. `access_token` is used to authenticate with the API.
        self.params = {'access_token': access_token}

    # This method creates a new deposition on Zenodo and returns its representation as JSON.
    def create_deposition(self):
        response = requests.post(self.BASE_URL, params=self.params, json={}, headers=self.headers)
        response.raise_for_status()
        return response.json()

    # This method uploads a file to a specified Zenodo repository.
    def upload_file_to_deposition(self, deposition_id, file_path, file_name):
        # We obtain the bucket's download URL using another method in this class.
        bucket_url = self.get_bucket_url(deposition_id)
        
        with open(file_path, "rb") as fp:
            response = requests.put(f"{bucket_url}/{file_name}", data=fp, params=self.params)
            response.raise_for_status()
            return response.json()

    # This method updates the metadata of a specified deposition on Zenodo.
    def update_deposition_metadata(self, deposition_id, metadata):
        response = requests.put(f"{self.BASE_URL}/{deposition_id}", params=self.params, data=json.dumps(metadata), headers=self.headers)
        response.raise_for_status()
        return response.json()

    # This method publishes a specified deposition on Zenodo.
    def publish_deposition(self, deposition_id):
        response = requests.post(f"{self.BASE_URL}/{deposition_id}/actions/publish", params=self.params)
        response.raise_for_status()
        return response.json()

    # This auxiliary method obtains the bucket URL (used for downloading files) for a specified deposition.
    def get_bucket_url(self, deposition_id):
        response = requests.get(f"{self.BASE_URL}/{deposition_id}", params=self.params)
        response.raise_for_status()
        return response.json()["links"]["bucket"]
    
    # This method downloads files via Grida
    def download_files(self, files_to_download, temp_directory, grida_directory):
        downloaded_files = []

        for file_path in files_to_download:
            bash_command = f"java -jar grida-standalone-2.3.0-20230905.072020-1-jar-with-dependencies.jar -r grida-server.conf getFile {file_path} {temp_directory}"
            result = subprocess.run(['bash', '-c', bash_command], cwd=grida_directory, capture_output=True, text=True)
            if result.returncode == 0:
                downloaded_files.append(result.stdout.strip())
                
        return downloaded_files

    def upload_files(self, files_to_download, metadata, grida_directory):
        temp_dir = tempfile.mkdtemp()

        try:
            downloaded_files = self.download_files(files_to_download, temp_dir, grida_directory)
            deposition = self.create_deposition()

            for path in downloaded_files:
                filename = os.path.basename(path)
                self.upload_file_to_deposition(deposition["id"], path, filename)

            self.update_deposition_metadata(deposition["id"], metadata)
            self.publish_deposition(deposition["id"])
            
            return deposition

        finally:
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    # Creating an argument parser
    parser = argparse.ArgumentParser(description="Script to download from Grida and upload to Zenodo.")

    # Add expected arguments for configuration files
    parser.add_argument('--config', required=True, help="Path to config.ini file.")
    parser.add_argument('--data', required=True, help="Path to data.json file.")

    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    ACCESS_TOKEN = config['SETTINGS']['ACCESS_TOKEN']
    GRIDA_DIRECTORY = config['SETTINGS']['GRIDA_DIRECTORY']

    with open(args.data, 'r') as f:
        data = json.load(f)

    files_to_download = data['files_to_download']
    metadata = data['metadata']

    uploader = ZenodoUploader(ACCESS_TOKEN)
    uploader.upload_files(files_to_download, metadata, GRIDA_DIRECTORY)

