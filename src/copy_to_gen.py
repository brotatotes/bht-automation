import shutil, os

CHOICEST_PROMPT = "choicest prompt v0.4"
BHT_PROMPT = "bht prompt v0.7"
source_folder = f"gpt output/bht/md/{CHOICEST_PROMPT} X {BHT_PROMPT}"
dest_folder = f"bht gen 2.5"

for root, dirs, files in os.walk(source_folder):
    for file_name in files:
        source_file = os.path.join(root, file_name)
        # Calculate the corresponding destination path
        relative_path = os.path.relpath(source_file, source_folder)
        destination_file = os.path.join(dest_folder, relative_path)

        # Ensure the destination directory exists, create it if necessary
        os.makedirs(os.path.dirname(destination_file), exist_ok=True)

        print(file_name)

        # Copy the file to the destination
        shutil.copy(source_file, destination_file)

print("Files copied successfully.")