
import os
import shutil


source_folder = "gpt output/bht/choicest prompt v1 X bht prompt v3"

dest_folder = "bht gen 1"


for book in os.listdir(source_folder):
    if book.startswith('.'):
        continue

    for chapter in os.listdir(f"{source_folder}/{book}"):
        if chapter.startswith('.'):
            continue

        for verse in os.listdir(f"{source_folder}/{book}/{chapter}"):
            if verse.startswith('.'):
                continue

            source_file = f"{source_folder}/{book}/{chapter}/{verse}"
            destination = f"{dest_folder}/{book}/{chapter}"
            print(f"Copying {source_file} to {destination}")
            shutil.copy2(source_file, destination)