import os
import json
import zipfile
import pandas as pd
from typing import Any, Dict, List


def find_files_of_type(folder_path: str, target_type: str = "txt") -> List[str]:
  """Finds all files of a specific type in the given directory.

    Args:
      folder_path: The directory path to search for files.
      target_type: The type of files to find (eg. txt, pkl, csv, etc.).

    Returns:
      List with the full paths of all found files with the required type.
  """
  all_files = os.listdir(folder_path)
  found_files = []
  for file in all_files:
    if len(file.split(".")) > 2:
      raise NameError("Cannot identify type of {}.".format(file))
    if file.split(".")[-1] == target_type:
      found_files.append(os.path.join(folder_path, file))

  return found_files


def unzip(zipfile_path: str) -> str:
  """Unzips a zip file by creating a folder in the same directory.

  The created folder has the same name as the zip file.

  Args:
    zipfile_path: Directory of the zip file to unzip.

  Returns:
    folder_path: Directory of the folder that contains the zip contents.
  """
  folder_path, filetype = zipfile_path.split(".")
  if filetype != "zip":
    raise NameError("Failed to read file of type {}. Make sure that the "
                    "directory does not contain dots.".format(filetype))

  if not os.path.isdir(folder_path):
    with zipfile.ZipFile(zipfile_path, "r") as zip_ref:
      zip_ref.extractall(folder_path)
  return folder_path


def zipdir(folder_name: str, folder_dir: str):
  """Zips the contents of folder in a zip file.

  The zip file has the same name as the folder and is stored in the same
  directory.

  Args:
    folder_name: Name of the folder to zip.
    folder_dir: Directory where the folder is located.

  Returns:
    zip_path: Absolute directory of the created zip file.
  """
  folder_path = os.path.join(folder_dir, folder_name)
  zip_path = os.path.join(folder_dir, ".".join([folder_name, "zip"]))

  zipf = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)
  for file in os.listdir(folder_path):
    file_path = os.path.join(folder_path, file)
    zipf.write(file_path, os.path.basename(file_path))
  zipf.close()
  return zip_path


def read_metadata(folder: str) -> Dict[str, Any]:
  if not os.path.isdir(folder):
    raise FileNotFoundError("Unable to find directory {}.".format(folder))

  # Load hotel metadata (star ratings, etc.)
  metafile_dir = find_files_of_type(folder, target_type="txt")
  if len(metafile_dir) > 1:
    raise FileExistsError("Multiple txt files found in {}.".format(folder))
  elif not metafile_dir:
    raise FileNotFoundError("Unable to find txt file in {}.".format(folder))

  with open(metafile_dir[0], "r") as file:
    metadata = json.load(file)
  os.remove(metafile_dir[0])

  return metadata


def read_reviews(folder: str) -> pd.DataFrame:
  # Load DataFrame from csv/pkl
  pkl_files = find_files_of_type(folder, target_type="pkl")
  if len(pkl_files) > 1:
    raise FileExistsError("Multiple data files found in {}.".format(folder))
  elif not pkl_files:
    raise FileNotFoundError("Unable to data file in {}.".format(folder))

  data = pd.read_pickle(pkl_files[0])
  os.remove(pkl_files[0])
  return data
