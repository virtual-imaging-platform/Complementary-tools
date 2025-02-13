import os
import json
import requests
import subprocess
import configparser
import argparse
import tarfile
from subprocess import PIPE

verbose = None

class ZenodoAPI:
    def __init__(self, url: str, token: str):
        self.base_url = url
        self.token = token

    def create_deposition(self) -> str:
        return self.__request("deposit/depositions", mode="post")

    def update_deposition_metadata(self, deposition_id: str, metadata: dict) -> str:
        return self.__request(f"deposit/depositions/{deposition_id}", mode="put", data=json.dumps(metadata))

    def publish_deposition(self, deposition_id: str):
        return self.__request(f"deposit/depositions/{deposition_id}/actions/publish", mode="post")

    def upload_file_to_deposition(self, deposition_id: str, file_path: str) -> str:
        bucket_url = self.get_bucket_url(deposition_id).removeprefix(self.base_url)
        file_name = os.path.basename(file_path)

        with open(file_path, "rb") as file:
            return self.__request(f"{bucket_url}/{file_name}", mode="put", data=file)

    def get_bucket_url(self, deposition_id: str) -> str:
        data = self.__request(f"deposit/depositions/{deposition_id}", mode="get")
        return data["links"]["bucket"]

    def __request(self, endpoint: str, mode: str, **kwargs) -> str:
        params = {"access_token": self.token}
        methods = {"put": requests.put, "post": requests.post, "get": requests.get}
        
        response: requests.Response = methods[mode](f"{self.base_url}/{endpoint}", params=params, json={}, **kwargs)
        logger("requests", response.json(), True)
        response.raise_for_status()
        return response.json()

class ZenodoUploader:
    def __init__(self, grida_dir):
        self.grida_dir = grida_dir

    def __get_file_grida(self, src: str, dest: str):
        cmd = f"java -jar grida-standalone.jar getFile {src} {dest}"
        process = subprocess.run(["bash", "-c", cmd], cwd=self.grida_dir, stdout=PIPE, stderr=PIPE, check=False)

        logger("grida-out", process.stdout.decode())
        logger("grida-err", process.stderr.decode())

    def download(self, boutique_descriptor: str, invocation_outputs: str, target_directory: str):
        """Download files using grida"""
        self.__get_file_grida(boutique_descriptor, target_directory)

        for subdir, files in invocation_outputs.items():
            target_path = os.path.join(target_directory, subdir)

            for lfn_path in files:
                file_path = lfn_path.replace('lfn://', '')
                self.__get_file_grida(file_path, target_path)
        logger("global", "files downloaded using grida!")

    def compress(self, target_directory: str):
        """This will compress directories present in target_directory, the rest will not change"""
        compressed_files = []

        for item in os.listdir(target_directory):
            item_path = os.path.join(target_directory, item)

            if os.path.isdir(item_path):
                output_filename = f"{item_path}.tar.gz"
                with tarfile.open(output_filename, "w:gz") as tar:
                    tar.add(item_path, arcname=os.path.basename(item_path))

                logger("global", f"compressed folder : {output_filename}")
                compressed_files.append(output_filename)

            elif item.endswith('.json') and item != 'workflowMetadata.json':
                compressed_files.append(item_path)

        logger("global", "files compressed!")
        return compressed_files

    def upload(self, zenodo_api: str, token: str, files: list, metadata: dict):
        """Upload to zenodo"""
        api = ZenodoAPI(zenodo_api, token)

        deposition_id = api.create_deposition()["id"]
        logger("global", f"deposition created on zenodo with id: {deposition_id}")

        for file in files:
            api.upload_file_to_deposition(deposition_id, file)
            logger("global", f"file {file} uploaded to zenodo")

        api.update_deposition_metadata(deposition_id, metadata)
        logger("global", f"metadata of deposition {deposition_id} updated!")
        api.publish_deposition(deposition_id)
        logger("global", "deposition set as published on zenodo!")

def logger(std, msg, debug=False):
    if (debug and verbose) or not debug and len(msg) != 0:
        print(f"[zenodo-uploader][{std}]: {msg}")

def main():
    parser = argparse.ArgumentParser(description="Script to download from Grida and upload to Zenodo.")

    parser.add_argument('--config', required=True, help="Path to config.ini file.")
    parser.add_argument('--data', required=True, help="Path to data.json file.")
    parser.add_argument("--v", action="store_true", help="Add debug logs")
    args = parser.parse_args()

    # debug
    global verbose
    verbose = True if args.v else False

    # data.json
    with open(args.data, 'r') as f:
        data = json.load(f)

    boutique_descriptor = data['descriptor_boutique']
    metadata = data['metadata']
    invocation_outputs = data['invocation_outputs']
    path_workflow_directory = data['path_workflow_directory'].replace('file://', '').rstrip('/')

    # config.json
    config = configparser.ConfigParser()
    config.read(args.config)

    os.environ['X509_USER_PROXY'] = config['SETTINGS']['X509_USER_PROXY']

    # runner
    zenodo = ZenodoUploader(config['SETTINGS']['GRIDA_DIRECTORY'])

    zenodo.download(boutique_descriptor, invocation_outputs, path_workflow_directory)
    compressed_files = zenodo.compress(path_workflow_directory)
    zenodo.upload(config["SETTINGS"]["ZENODO_API"], config['SETTINGS']['ACCESS_TOKEN'], compressed_files, metadata)

if __name__ == "__main__":
    main()
