
import os
import re

COMMENTATORS = set([
    "Henry Alford",
    "Jamieson Fausset Brown",
    "Albert Barnes",
    "Marvin Vincent",
    "John Calvin",
    "Philip Schaff",
    "Archibald T Robertson",
    "John Gill",
    "John Wesley"
    ])

def get_commentary(commentator, book, chapter, verse):
    file_path = f'commentary/{commentator}/{book}/Chapter {chapter}/Verse {verse}.txt'
    
    if not os.path.exists(file_path):
        # raise Exception(f'No commentary found for {verse_ref} for {commentator}.')
        return None
    
    file_contents = ""
    with open(file_path, 'r', encoding='utf-8') as file:
        file_contents = file.read()

    if not file_contents:
        # raise Exception(f'Commentary entry was blank for {verse_ref} for {commentator}.')
        return None

    return file_contents


folder = "bht gen 1"

count = 0

output_file = open('check_choicests.txt', 'w')

for book in os.listdir(folder):
    if book.startswith('.'):
        continue

    for chapter in os.listdir(f"{folder}/{book}"):
        if chapter.startswith('.'):
            continue

        for verse in os.listdir(f"{folder}/{book}/{chapter}"):
            if verse.startswith('.'):
                continue

            bht_content = open(f"{folder}/{book}/{chapter}/{verse}", 'r').read()
            pattern = r'^### .+:$'
            commentators = set([c[4:-1] for c in re.findall(pattern, bht_content, re.MULTILINE)])
            missing_commentators = COMMENTATORS - commentators

            chapter_number, verse_number = int(chapter.split()[1]), int(verse.split()[-2])

            # print(book, chapter_number, verse_number)

            # verify that missing commentators really have no commentary...
            for missing_commentator in missing_commentators:
                commentary_content = get_commentary(missing_commentator, book, chapter_number, verse_number)

                no_commentary = not commentary_content

                if not no_commentary:
                    output_file.write(f"{missing_commentator} for {book} {chapter_number}:{verse_number} actually has commentary!\n")
                    count += 1

output_file.write(str(count))
output_file.close()