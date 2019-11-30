import os
import zipfile
from typing import List


def find_files_of_type(folder_path: str, target_type: str = "txt") -> List[str]:
  """Finds all files of a specific type in the given directory.

    Args:
      folder_path: The directory path to search for files.
      target_type: The type of files to find (eg. txt, pkl, csv, etc.)

    Returns:
      The full path of all files with the required type
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
  folder_path, filetype = zipfile_path.split(".")
  if filetype != "zip":
    raise NameError("Failed to read file of type {}. Make sure that the "
                    "directory does not contain dots.".format(filetype))

  if not os.path.isdir(folder_path):
    with zipfile.ZipFile(zipfile_path, "r") as zip_ref:
      zip_ref.extractall(folder_path)

  return folder_path