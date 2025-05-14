import json
import os
import sys
from argparse import ArgumentParser
from vip_client import VipSession
from copy import deepcopy
from vip_client.classes import VipGirder
from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import urlparse
from uuid import uuid4
from girder_client import GirderClient

@dataclass
class Config:
    # vip
    vip_url: str
    vip_key: str
    # provider
    provider_url: str
    provider_key: str
    provider_id: str
    # filemanagement
    use_vip_storage: bool

class FileLoader():
    def load_json(file_path: str) -> dict:
        with open(file_path, "r") as file:
            return json.load(file)

class AbstractReplayer(ABC):
    @abstractmethod
    def __init__(self, config: Config):
        self.config = config
        pass

    @abstractmethod
    def replay(self, pipeline: str, data: dict, output_dir: str):
        pass

    def warning(cls, inputs: dict):
        print("Are you sure to rerun this execution (y/n)?")

        if input() != "y":
            print("aborted!")
            exit(1)

    @abstractmethod
    def finish(self):
        pass

    def random_session(self) -> str:
        return f"relaunch-{str(uuid4())[:6]}"


class GirderReplayer(AbstractReplayer):
    def __init__(self, config: Config):
        super().__init__(config)
        VipGirder.init(
            vip_key=config.vip_key, 
            girder_key=config.provider_key, 
            girder_api_url=f"{config.provider_url}/api/v1", 
            girder_id_prefix=config.provider_id, 
            vip_portal_url=config.vip_url)

    def replay(self, pipeline, data, output_dir):
        urls = self.extract_girder_links(data["inputs"], data["provider"]["storage_id"])
        inputs = self.transform_inputs(data["inputs"], urls)
        self.local_output = output_dir

        if self.config.use_vip_storage:
            self.launcher = VipGirder(output_location="vip", session_name=self.random_session())
        else:
            self.launcher = VipGirder(output_location="local", output_dir=self.local_output,
                session_name=self.random_session())

        self.launcher.launch_pipeline(pipeline, inputs)
        self.launcher.monitor_workflows(5)

    def finish(self):
        if not self.config.use_vip_storage:
            self.launcher.download_outputs()
            self.launcher.finish()
            print("Outputs are on your local storage!")
        else:
            self.launcher.finish(keep_output=True)
            print("Outputs are on the VIP platform!")

    @classmethod
    def warning(cls, inputs):
        print("The inputs that you are about to replay are detected to be located on a girder server.\n\
Please, check that have you access to it and pass the credentials to the script (--provider-key)!")
        super().warning(cls, inputs)

    def transform_inputs(self, inputs: dict, urls: dict):
        for v in inputs.values():
            for index, item in enumerate(v):
                if (item in urls.keys()):
                    v[index] = self.transform_to_girder_collection(urls[item])
        return inputs

    def transform_to_girder_collection(self, file_id: str):
        client = GirderClient(apiUrl=VipGirder._GIRDER_PORTAL)
        client.authenticate(apiKey=self.config.provider_key)

        file = client.getFile(file_id)
        item = client.getItem(file["itemId"])
        current_folder = client.getFolder(item["folderId"])
        path_parts = [item["name"]]

        while current_folder['parentId']:
            path_parts.append(current_folder['name'])

            if current_folder['parentCollection'] == "collection":
                collection_info = client.get(f"collection/{current_folder['parentId']}")
                path_parts.append(collection_info['name'])
                prefix = f"/collection/"
                break

            elif current_folder['parentCollection'] == "user":
                prefix = f"/user/{client.getUser(current_folder['creatorId'])['login']}/"
                break  

            current_folder = client.get(f"folder/{current_folder['parentId']}")

        return prefix + "/".join(reversed(path_parts))

    def extract_girder_links(self, inputs: dict, girder_id: str) -> dict:
        urls = {}
        
        for v in inputs.values():
            for url in v:
                if url.startswith(girder_id):
                    id = urlparse(url).netloc.lstrip("/")
                    urls[url] = id

        return urls

class LocalReplayer(AbstractReplayer):
    _TREE_FILE = "inputs_tree.txt"
    _INPUT_FOLDER = "inputs"

    def __init__(self, config):
        super().__init__(config)
        VipSession.init(config.vip_key, vip_portal_url=config.vip_url)

    def replay(self, pipeline, data, output_dir):
        session_name = self.random_session()
        inputs, _ = self.__transform_inputs_to_local(data["inputs"], self.__input_vip(session_name))

        self.launcher = VipSession(session_name, output_dir=output_dir)
        self.launcher.upload_inputs(self._INPUT_FOLDER, True)
        self.launcher.launch_pipeline(pipeline, inputs)
        self.launcher.monitor_workflows(5)

    def finish(self):
        if not self.config.use_vip_storage:
            self.launcher.download_outputs()
            self.launcher.finish()
            print("Outputs are on your local storage!")
        else:
            self.launcher.finish(keep_output=True)
            print("Outputs are on the VIP platform!")

    def __input_vip(self, session) -> str:
        return f"/vip/Home/API/" + session + "/INPUTS/"

    @classmethod
    def warning(cls, inputs):
        LocalReplayer.__generate_tree_files(deepcopy(inputs))
        print(f"The inputs that you are about to replay are detected to be located locally on your machine.\n\
Please, download and organize them like it is specified inside the {cls._TREE_FILE} file!")
        super().warning(cls, inputs)

    @classmethod
    def __is_path(cls, value) -> bool:
        if isinstance(value, list):
            return any("/" in str(item) for item in value)
        else:
            return "/" in value

    @classmethod
    def __get_inputs_paths(cls, values: list[list]) -> list:
        result = list()

        for value in values:
            for item in value:
                if (cls.__is_path(item)):
                    result.append(item)
        return result

    @classmethod
    def __simplify_inputs_paths(cls, paths: list[str], new_prefix: str) -> dict:
        new_paths = dict()
        # if multiples paths commonpath or just keeping the basename for single path
        common_path = os.path.commonpath(paths) if len(paths) > 1 else os.path.dirname(paths[0])

        for path in paths:
            new_paths[path] = new_prefix + path.removeprefix(common_path + "/")
        return new_paths

    @classmethod
    def __transform_inputs_to_local(cls, inputs: dict, new_prefix = "") -> tuple[dict, dict]:
        inputs_paths = cls.__get_inputs_paths(inputs.values())
        simplified_paths = cls.__simplify_inputs_paths(inputs_paths, new_prefix)

        for values in inputs.values():
            for i, item in enumerate(values):
                if item in simplified_paths:
                    values[i] = simplified_paths[item]
        return inputs, simplified_paths

    @classmethod
    def __display_tree(cls, tree: dict, indent="├──", file=sys.stdout):
        files = []
        directories = []

        for k, v in tree.items():
            if v:
                directories.append((k, v))
            else:
                files.append(k)

        for f in files:
            print(f"{indent} {f}", file=file)

        for directory, sub_tree in directories:
            print(f"{indent} {directory}/", file=file)
            cls.__display_tree(sub_tree, " " * len(indent) + " ├──", file)

    @classmethod
    def __generate_tree_files(cls, inputs: dict, root_folder="inputs/"):
        _, paths = cls.__transform_inputs_to_local(inputs)
        paths = paths.values()

        tree = {}
        for path in paths:
            parts: list[str] = path.strip("/").split("/")
            current = tree
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
        with open(cls._TREE_FILE, "w") as file:
            print(root_folder, file=file)
            cls.__display_tree(tree, file=file)

class Runner:
    def __init__(self, conf: Config, descriptor: dict, data: dict, output_folder: str):
        self.replayer_cls = self.detect_replayer(data["provider"])
        self.config = conf
        self.descriptor = descriptor
        self.data = data
        self.output_folder = output_folder

    def run(self):
        self.replayer = self.replayer_cls(self.config)
        self.replayer.warning(self.data["inputs"])
        self.replayer.replay(self.__get_pipeline(self.descriptor), self.data, self.output_folder)
        self.replayer.finish()

    def __get_pipeline(self, descriptor: str) -> str:
        return f"{descriptor['name']}/{descriptor['tool-version']}"

    @classmethod
    def create_config(cls, provider_info: dict, **kwargs) -> Config:
        return Config(
            vip_url = provider_info.get("vip_url", "https://vip.creatis.insa-lyon.fr/"),
            vip_key = kwargs.get("vip_key", ""),
            provider_url = provider_info.get("storage_url"),
            provider_key = kwargs.get("provider_key", ""),
            provider_id = provider_info.get("storage_id", ""),
            use_vip_storage = kwargs.get("vip_storage", False)
        )
        
    @classmethod
    def detect_replayer(cls, data: dict) :
        provider = data["storage_type"]

        if (provider == "GIRDER"):
            return GirderReplayer
        else:
            return LocalReplayer

def main():
    parser = ArgumentParser(description="Script used to replay a specific execution on VIP!")

    group = parser.add_mutually_exclusive_group()
    parser.add_argument("descriptor", help="the application boutiques.json file")
    parser.add_argument("inputs", help="the workflow-xxxxx.json file")
    parser.add_argument("--vip-key", required=True, help="your vip api key")
    parser.add_argument("--provider-key", help="the api key related to your input provider (ex: girder)")
    group.add_argument("--output-folder", help="define where you want your outputs to be (if vip-storage, then it won't works)", default=f"outputs/")
    group.add_argument("--vip-storage", action="store_true", help="store the output on vip output-folder specified instead of local folder")

    args = parser.parse_args()
    descriptor_file = FileLoader.load_json(args.descriptor)
    inputs_file = FileLoader.load_json(args.inputs)

    conf = Runner.create_config(inputs_file["provider"], **vars(args))
    Runner(conf, descriptor_file, inputs_file, args.output_folder).run()

if __name__ == "__main__":
    main()
