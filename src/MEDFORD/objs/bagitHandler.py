import os
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import hashlib


class BagItHandler:
    def __init__(self, medford_data: Dict[str, Any],
                 base_dir: Optional[str] = ".", output_path: str = ".",
                 medford_file_path: Optional[str] = None):

        self.medford_data = medford_data
        self.base_dir = Path(base_dir) if base_dir else None
        self.output_path = Path(output_path)
        self.medford_file_path = (Path(medford_file_path)
                                  if medford_file_path else None)
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
                        return (self.base_dir / file_root_value
                                if self.base_dir else Path(file_root_value))
        else:
            print("Warning: File root not specified.") # TODO what to do?

        return self.base_dir

    def _validate(self):
        # check if we have a file root
        if self.no_files: #TODO
            return True
        else: 
            if not self.file_root:
                print("Error: FileRoot is required for BagIt validation.")
                return False

            # check if file root exists
            if not self.file_root.exists():
                print("Error: FileRoot directory "
                    f"{self.file_root} does not exist.")
                return False

            # check if referenced files exist
            referenced_files = self._get_file_references()
            missing_files = []

            for file_tag, file_path in referenced_files:
                full_path = self.file_root / file_path
                if not full_path.exists():
                    missing_files.append((file_tag, str(file_path)))

            if missing_files:
                print("Error: Referenced files are missing:")
                for tag, file in missing_files:
                    print(f"  - {tag}: {file}")
                return False

            # check all files in FileRoot must have corresponding tags
            untagged_files = self._find_untagged_files(referenced_files)
            if untagged_files:
                print("Error: Files in FileRoot without corresponding tags:")
                for file in untagged_files:
                    print(f"  - {file}")
                return False

            # check if all files are readable
            unreadable_files = []
            for tag_name, file_path in referenced_files:
                full_path = self.file_root / file_path
                if not os.access(full_path, os.R_OK):
                    unreadable_files.append(str(file_path))

            if unreadable_files:
                print("Error: Unreadable files:")
                for file in unreadable_files:
                    print(f"  - {file}")
                return False

        return True

    def _get_file_references(self):
        file_references = []
        seen_files = set() # to keep track of if there are 2 files with the same name

        for key in self.medford_data:
            if key.endswith("_Primary") or key.endswith("_Copy"):
                for entry in self.medford_data[key]:
                    if "value" in entry:
                        file_path = entry["value"]
                        filename = Path(file_path).name
               
                        if filename in seen_files:
                            raise ValueError(f"Duplicate file name detected: '{filename}' "
                                  f"in {key}. File names must be unique across all tags.")
                        
                        seen_files.add(filename)
                        file_references.append((key, file_path))
                    

        return file_references

    def _find_untagged_files(self, referenced_files: List[Tuple[str, str]]):
        # find files in FileRoot that don't have corresponding tags
        if not self.file_root or not self.file_root.exists():
            return []

        referenced_paths = {Path(file_path)
                            for _, file_path in referenced_files}

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
            self._create_bag_info()
            self._create_zip_bag()

            # clean up temporary directory
            shutil.rmtree(self.temp_dir)

            print(f"Successfully created BagIt package: {self.bag_path}")
            return self.bag_path

        except Exception as e:
            print(f"Error creating BagIt package: {e}")

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
        with open(metadata_json_path, 'w') as f:
            json.dump(self.medford_data, f, indent=2)

        # TODO translate? what does that mean?
        if self.medford_file_path and self.medford_file_path.exists():
            metadata_mfd_path = self.temp_dir / "metadata.mfd"
            shutil.copy2(self.medford_file_path, metadata_mfd_path)
        else:
            print("Warning: Original MEDFORD file not found")

    def _create_manifest(self):
        manifest_path = self.temp_dir / "manifest.txt"
        manifest_lines = []

        for file_path in self.temp_dir.rglob("*"):
            if file_path.is_file() and file_path.name != "manifest.txt":
                relative_path = file_path.relative_to(self.temp_dir)
                checksum = self._calculate_checksum(file_path)
                normalized_path = str(relative_path).replace(os.sep, '/')
                manifest_lines.append(f"{checksum}  {normalized_path}")

        manifest_lines.sort()

        with open(manifest_path, 'w') as f:
            f.write("\n".join(manifest_lines))

    # got this code from someone's github TODO need to say code copied from  
    def _calculate_checksum(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _create_bag_info(self):
        bag_info_path = self.temp_dir / "bag-info.txt"
        
        payload_stats = self._calculate_payload_stats()
        bagging_date = datetime.now().strftime("%Y-%m-%d")
        bag_info_lines = []
        
        bag_info_lines.append(f"Bagging-Date: {bagging_date}")
        bag_info_lines.append(f"Bag-Size: {payload_stats['bag_size']}")
        bag_info_lines.append(f"Payload-Oxum: {payload_stats['octet_count']}.{payload_stats['stream_count']}")
        
        if "MEDFORD" in self.medford_data:
            for entry in self.medford_data["MEDFORD"]:
                if "value" in entry:
                    bag_info_lines.append(f"External-Description: MEDFORD metadata package: {entry['value']}")
                    break
        
        if "Contributor" in self.medford_data:
            for entry in self.medford_data["Contributor"]:
                if "value" in entry:
                    bag_info_lines.append(f"Contact-Name: {entry['value']}")
                if "Email" in entry:
                    emails = entry["Email"] if isinstance(entry["Email"], list) else [entry["Email"]]
                    bag_info_lines.append(f"Contact-Email: {emails[0]}")
        
        if "Paper_Primary" in self.medford_data:
            for entry in self.medford_data["Paper_Primary"]:
                if "value" in entry:
                    bag_info_lines.append(f"Internal-Sender-Description: Research data for: {entry['value']}")
                    break
        
        if self.medford_file_path:
            external_id = Path(self.medford_file_path).stem
            bag_info_lines.append(f"External-Identifier: {external_id}")
        
        #TODO ask about this
        bag_info_lines.append("Source-Organization: idk")
        
        with open(bag_info_path, 'w', encoding='utf-8') as f:
            for line in bag_info_lines:
                f.write(line + '\n')
                

    def _calculate_payload_stats(self):
        total_bytes = 0
        file_count = 0
        
        if self.data_dir.exists():
            for file_path in self.data_dir.rglob("*"):
                if file_path.is_file():
                    total_bytes += file_path.stat().st_size
                    file_count += 1
        
        # got this code from someone else
        if total_bytes >= 1024**4:  # TB
            bag_size = f"{total_bytes / (1024**4):.1f} TB"
        elif total_bytes >= 1024**3:  # GB
            bag_size = f"{total_bytes / (1024**3):.1f} GB"
        elif total_bytes >= 1024**2:  # MB
            bag_size = f"{total_bytes / (1024**2):.1f} MB"
        elif total_bytes >= 1024:  # KB
            bag_size = f"{total_bytes / 1024:.1f} KB"
        else:
            bag_size = f"{total_bytes} bytes"
        
        return {
            'bag_size': bag_size,
            'octet_count': total_bytes,
            'stream_count': file_count
        }

    def _create_zip_bag(self):
        with zipfile.ZipFile(self.bag_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.temp_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.temp_dir)
                    zf.write(file_path,
                             arcname=str(arcname).replace(os.sep, '/'))
