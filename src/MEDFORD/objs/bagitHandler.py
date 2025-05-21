import os
import json
import datetime
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional

class BagItHandler:
        def __init__(self, medford_data: Dict[str, Any], base_dir: Optional[str] = None, output_path: str = ".", medford_file_path: Optional[str] = None):
                self.medford_data = medford_data
                self.base_dir = Path(base_dir) if base_dir else None # command line specified
                self.output_path = Path(output_path)
                self.medford_file_path = Path(medford_file_path) if medford_file_path else None


                self.bag_name = "default_bag_name" # need to implement command line option
                if "Bag_Name" in self.medford_data:
                        for entry in self.medford_data["Bag_Name"]:
                                if "value" in entry:
                                        self.bag_name = entry["value"]
                
                self.bag_path = self.output_path / f"{self.bag_name}.zip"
                #TODO what to name: given by user, command line, or tag; .mfd file -> directory where medford file is and where it should be (relative address)

                # make temporary directory
                self.temp_dir = self.output_path / f"temp_{self.bag_name}"
                self.data_dir = self.temp_dir / "data"

                # get FileRoot if specified
                self.file_root = self._get_file_root()
        

        def _get_file_root(self):
                if "FileRoot" in self.medford_data:
                        for entry in self.medford_data["FileRoot"]:
                                if "value" in entry:
                                        file_root_value = entry["value"]
                                        if file_root_value == ".": # relative path TODO need to think about "." again
                                                return self.base_dir
                                        elif os.path.isabs(file_root_value): # absolute path
                                                return Path(file_root_value)
                                        else:
                                                # relative path from base directory
                                                return self.base_dir / file_root_value if self.base_dir else Path(file_root_value)
                return self.base_dir
        
        def validate(self): 
                
                # check if we have a file root
                if not self.file_root:
                        print("Error: FileRoot is required for BagIt validation.")
                        return False
                
                # check if file root exists
                if not self.file_root.exists():
                        print(f"Error: FileRoot directory {self.file_root} does not exist.")
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
                
                # check: TODO think about if all files in fileroot have corresponding tags?
                
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
        
        def _get_file_references(self): # from @ *-File tags.
                file_references = []
        
                # look for all tags ending with "_file" or "file"
                for key in self.medford_data:
                        if key.endswith("_file") or key == "file":
                                for entry in self.medford_data[key]:
                                        if "value" in entry:
                                                file_references.append((key, entry["value"]))
                
                return file_references
        
        def _compile(self): #returns path to zip file
                try:
                        # clean up any existing temp directory
                        if self.temp_dir.exists():
                                shutil.rmtree(self.temp_dir)
                        
                        # create temporary directory structure
                        self.temp_dir.mkdir(parents=True, exist_ok=True)
                        self.data_dir.mkdir(parents=True, exist_ok=True)
                        
                        self._copy_data_files()
                        self._create_metadata_files()
                        self._create_manifest()
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
                        
                        # convert Windows paths to forward slashes for the bag
                        compatible_path = file_path.replace("\\", "/")
                        dest_path = self.data_dir / compatible_path
                        
                        # # create parent directories if needed TODO think about
                        # dest_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        shutil.copy2(source_path, dest_path)
                        # print(f"  Copied: {file_path}")

        def _create_metadata_files(self):
                metadata_json_path = self.temp_dir / "metadata.json"
                with open(metadata_json_path, 'w') as f:
                        json.dump(self.medford_data, f, indent=2)
                
                #TODO translate? what does that mean?
                if self.medford_file_path and self.medford_file_path.exists():
                        metadata_mfd_path = self.temp_dir / "metadata.mfd"
                        shutil.copy2(self.medford_file_path, metadata_mfd_path)
                else:
                        print("Warning: Original MEDFORD file not found")

        def _create_manifest(self):
                manifest_path = self.temp_dir / "manifest.txt"
                
                #TODO. how to create manifest file? what is manifest file? 
                #TODO need to create license? 
        
        def _create_zip_bag(self):
                with zipfile.ZipFile(self.bag_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for file_path in self.temp_dir.rglob("*"):
                                if file_path.is_file():
                                        arcname = file_path.relative_to(self.temp_dir)
                                        zf.write(file_path, arcname=str(arcname).replace(os.sep, '/'))
                        
        # def _get_dataset_references(self):


