import os
import shutil


class ScriptPath:
    TRAVELCARD_FRONTEND = "/Users/ariel/Documents/travel-card/frontend"
    BACKUP = "/Users/ariel/Desktop/tmp/backup"
    PERSONAL = "/Users/ariel/PycharmProjects/personal"

def copy_files(src, dest, exclude_dirs, exclude_files):
   """
   Copy files from src to dest, excluding specific file types, directories, and specific files.

   :param src: Source directory (path1)
   :param dest: Destination directory (path2)
   :param exclude_dirs: List of directories to exclude from src
   :param exclude_files: List of specific files to exclude
   """
   # Define excluded file types and directory names
   excluded_extensions = {'.ini', '.config', '.cfg'}
   excluded_directories = {'.idea', '__pycache__', 'node_modules', '.next', 'cache'}
   excluded_directories.update(exclude_dirs)

   # Get source folder name and create full destination path
   src_folder_name = os.path.basename(os.path.normpath(src))
   full_dest = os.path.join(dest, src_folder_name)

   # Remove the destination directory if it exists
   if os.path.exists(full_dest):
       print(f"Removing existing destination directory: {full_dest}")
       shutil.rmtree(full_dest)

   # Create the destination directory
   os.makedirs(full_dest, exist_ok=True)
   print(f"Created destination directory: {full_dest}")

   # Walk through the source directory
   for root, dirs, files in os.walk(src):
       # Exclude directories
       dirs[:] = [d for d in dirs if d not in excluded_directories]

       # Copy files
       for file in files:
           file_path = os.path.join(root, file)
           if not any(file.endswith(ext) for ext in excluded_extensions) and file not in exclude_files:
               shutil.copy2(file_path, os.path.join(full_dest, file))
               print(f"Copied: {file_path} -> {os.path.join(full_dest, file)}")

if __name__ == "__main__":
   # Define variables
   src_path = ScriptPath.PERSONAL
   dst_path = ScriptPath.BACKUP
   exclude_dirs = ["images", "migrations", ".git", "crossfit", "shifts", "bank-scraper"]  # Replace with your list of excluded directories
   exclude_files = ["package-lock.json", "yarn.lock", ".env.local", ".DS_Store", "variables.py", "tsconfig.tsbuildinfo"]  # Replace with your list of excluded files

   # Run the copy function
   copy_files(src_path, dst_path, set(exclude_dirs), exclude_files)