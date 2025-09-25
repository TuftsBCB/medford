import os
import json
import shutil
import zipfile
import warnings
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import hashlib


class BagItHandler:
    def __init__(
        self,
        medford_data: Dict[str, Any],
        base_dir: Optional[str] = ".",
        output_path: str = ".",
        medford_file_path: Optional[str] = None,
    ):
        self.medford_data = medford_data
        self.base_dir = Path(base_dir) if base_dir else None
        self.output_path = Path(output_path)
        self.medford_file_path = Path(medford_file_path) if medford_file_path else None
        self.bag_name = "default_bag_name"

        if "Bag_Name" in self.medford_data:
            for entry in self.medford_data["Bag_Name"]:
                if "value" in entry:
                    self.bag_name = entry["value"]

        self.bag_path = self.output_path / f"{self.bag_name}.zip"

        # make temporary directory
        self.temp_dir = self.output_path / f"temp_{self.bag_name}"
        self.data_dir = self.temp_dir / "data"

        # get FileRoot if specified
        self.file_root = self._get_file_root()
        if self.file_root == None:
            self.no_files = True
        else:
            self.no_files = False

    def _get_file_root(self):
        if "FileRoot" in self.medford_data:
            for entry in self.medford_data["FileRoot"]:
                if "value" in entry:
                    file_root_value = entry["value"]
                    if file_root_value == ".":
                        # print(self.base_dir)
                        return self.base_dir
                    elif os.path.isabs(file_root_value):  # absolute path
                        return Path(file_root_value)
                    else:
                        # relative path from base directory
                        return (
                            self.base_dir / file_root_value
                            if self.base_dir
                            else Path(file_root_value)
                        )
        else:
            warnings.warn("File root not specified.", UserWarning)

        return self.base_dir

    def _validate(self):
        # check if we have a file root
        if self.no_files:  # TODO
            return True
        else:
            if not self.file_root:
                warnings.warn("FileRoot is required for BagIt validation.", UserWarning)
                return False

            # check if file root exists
            if not self.file_root.exists():
                warnings.warn(f"FileRoot directory {self.file_root} does not exist.", UserWarning)
                return False

            # check if referenced files exist
            referenced_files = self._get_file_references()
            missing_files = []

            for file_tag, file_path in referenced_files:
                full_path = self.file_root / file_path
                if not full_path.exists():
                    missing_files.append((file_tag, str(file_path)))

            if missing_files:
                warning_msg = "Referenced files are missing:\n"
                for tag, file in missing_files:
                    warning_msg += f"  - {tag}: {file}\n"
                warnings.warn(warning_msg.rstrip(), UserWarning)
                return False

            # check all files in FileRoot must have corresponding tags
            untagged_files = self._find_untagged_files(referenced_files)
            if untagged_files:
                warning_msg = "Files in FileRoot without corresponding tags:\n"
                for file in untagged_files:
                    warning_msg += f"  - {file}\n"
                warnings.warn(warning_msg.rstrip(), UserWarning)
                return False

            # check if all files are readable
            unreadable_files = []
            for tag_name, file_path in referenced_files:
                full_path = self.file_root / file_path
                if not os.access(full_path, os.R_OK):
                    unreadable_files.append(str(file_path))

            if unreadable_files:
                warning_msg = "Unreadable files:\n"
                for file in unreadable_files:
                    warning_msg += f"  - {file}\n"
                warnings.warn(warning_msg.rstrip(), UserWarning)
                return False

        return True

    def _get_file_references(self):
        file_references = []
        seen_files = set()  # to keep track of if there are 2 files with the same name

        for key in self.medford_data:
            if key.endswith("_Primary") or key.endswith("_Copy"):
                for entry in self.medford_data[key]:
                    if "value" in entry:
                        file_path = entry["value"]
                        filename = Path(file_path).name

                        if filename in seen_files:
                            raise ValueError(
                                f"Duplicate file name detected: '{filename}' "
                                f"in {key}. File names must be unique across all tags."
                            )

                        seen_files.add(filename)
                        file_references.append((key, file_path))

        return file_references

    def _find_untagged_files(self, referenced_files: List[Tuple[str, str]]):
        # find files in FileRoot that don't have corresponding tags
        if not self.file_root or not self.file_root.exists():
            return []

        referenced_paths = {Path(file_path) for _, file_path in referenced_files}

        untagged = []
        for path in self.file_root.rglob("*"):
            if path.is_file():
                relative_path = path.relative_to(self.file_root)
                if relative_path not in referenced_paths:
                    untagged.append(str(relative_path))

        return untagged

    def _compile(self):  # returns path to zip file
        try:
            validated = self._validate()
            if not validated:
                raise ValueError("Could not create Bag because of failed validation")
            # clean up any existing temp directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

            # create temporary directory structure
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            self.data_dir.mkdir(parents=True, exist_ok=True)

            if not self.no_files:
                self._copy_data_files()

            self._create_metadata_files()
            self._create_manifest()
            self._create_zip_bag()

            # clean up temporary directory
            shutil.rmtree(self.temp_dir)

            print(f"Successfully created BagIt package: {self.bag_path}")
            return self.bag_path

        except Exception as e:
            warnings.warn(f"Error creating BagIt package: {e}", UserWarning)

            # clean up
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            return None

    def _copy_data_files(self):
        referenced_files = self._get_file_references()
        for file_tag, file_path in referenced_files:
            source_path = self.file_root / file_path
            if not source_path.exists():
                raise ValueError(f"File {file_path} does not exist.")

            # convert Windows paths to forward slashes for the bag
            compatible_path = file_path.replace("\\", "/")
            dest_path = self.data_dir / compatible_path

            # # create parent directories if needed TODO think about
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source_path, dest_path)

    def _create_metadata_files(self):
        metadata_json_path = self.temp_dir / "metadata.json"
        with open(metadata_json_path, "w") as f:
            json.dump(self.medford_data, f, indent=2)

        # TODO translate? what does that mean?
        if self.medford_file_path and self.medford_file_path.exists():
            metadata_mfd_path = self.temp_dir / "metadata.mfd"
            shutil.copy2(self.medford_file_path, metadata_mfd_path)
        else:
            warnings.warn("Original MEDFORD file not found", UserWarning)

    def _create_manifest(self):
        manifest_path = self.temp_dir / "manifest.txt"
        manifest_lines = []

        for file_path in self.temp_dir.rglob("*"):
            if file_path.is_file() and file_path.name != "manifest.txt":
                relative_path = file_path.relative_to(self.temp_dir)
                checksum = self._calculate_checksum(file_path)
                normalized_path = str(relative_path).replace(os.sep, "/")
                manifest_lines.append(f"{checksum}  {normalized_path}")

        manifest_lines.sort()

        with open(manifest_path, "w") as f:
            f.write("\n".join(manifest_lines))

    # got this code from someone's github TODO need to say code copied from
    def _calculate_checksum(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _create_baginfo(self):
        pass
    
    def _create_zip_bag(self):
        with zipfile.ZipFile(self.bag_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.temp_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.temp_dir)
                    zf.write(file_path, arcname=str(arcname).replace(os.sep, "/"))
