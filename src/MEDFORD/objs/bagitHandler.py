import os
import json
import datetime
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

class BagItHandler:
        def __init__(self, medford_data: Dict[str, Any], base_dir: Optional[str] = None, output_path: str = "."):
                self.medford_data = medford_data
                self.base_dir = Path(base_dir) if base_dir else None
                self.output_path = Path(output_path)
                # self.bag_name = #TODO what to name: given by user, command line, or tag; .mfd file -> directory where medford file is and where it should be (relative address)
                # self.bag_path = self.output_path / f"{self.bag_name}.zip"
                
                # # Temporary directory for building the bag structure
                # self.temp_dir = self.output_path / f"temp_{self.bag_name}"
                # self.data_dir = self.temp_dir / "data"
        
        def validate(self): #TODO more validation needed? should i combine this validation with parser validation?
                #should still validate; is separate from parser validation
                # 
                # check if base directory is given
                if not self.base_dir:
                        print("Error: Base directory (--dir) is required for BagIt validation.") #TODO or would this info be given in @FileRoot?
                        return False

                # check if base directory exists 
                if not self.base_dir.exists():
                        print(f"Error: Base directory {self.base_dir} does not exist.")
                        return False

                # check if referenced files exist
                referenced_files = self._get_files()
                missing_files = []
        
                for file_path in referenced_files:
                        full_path = self.base_dir / file_path
                        if not full_path.exists():
                                missing_files.append(str(file_path))
                
                if missing_files:
                        print("Error: Referenced files are missing:")
                        for file in missing_files:
                                print(f"  - {file}")
                        return False
                
                return True
        
        def _get_files(self):
                filePaths = [] #TODO check syntax/logic
        
                file_root = None
                if "fileroot" in self.medford_data:
                        for entry in self.medford_data["fileroot"]:
                                if "value" in entry:
                                        file_root = entry["value"]
                                        break
                
                if "fileroot_file" in self.medford_data:
                        for entry in self.medford_data["fileroot_file"]:
                                if "value" in entry:
                                        # If we have a file_root_path, combine it with the filename
                                        if file_root:
                                                full_path = Path(file_root) / entry["value"]
                                                filePaths.append(str(full_path))
                                else:
                                        # If no file_root_path, just use the filename 
                                        filePaths.append(entry["value"])
                return filePaths
        
        # def _compile(self): #returns path to zip file
        # def _copy_data_files(self):
        # def _get_dataset_references(self):
        # def _create_manifest(self):
        # def _create_zip_bag(self):

