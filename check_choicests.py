
import os
import re
import string
from gensim.utils import tokenize

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


# folder_to_check = "bht gen 1"
folder_to_check = "gpt output/bht/choicest prompt v2 X bht prompt v3"

verse_count = 0
missing_commentary_quotes_count = 0
corrupted_commentary_quotes_count = 0
corrupted_verses_count = 0

output_file = open('check_choicests.md', 'w')
output_file.write("# Issues Found:\n\n")

for book in os.listdir(folder_to_check):
    if book.startswith('.'):
        continue

    for chapter in os.listdir(f"{folder_to_check}/{book}"):
        if chapter.startswith('.'):
            continue

        for verse in os.listdir(f"{folder_to_check}/{book}/{chapter}"):
            verse_count += 1
            print(f"\r{verse_count} / 7957", end="", flush=True)
            if verse.startswith('.'):
                continue

            bht_content = open(f"{folder_to_check}/{book}/{chapter}/{verse}", 'r').read()
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
                    output_file.write(f"## {missing_commentator} for {book} {chapter_number}:{verse_number} actually has commentary!\n\n")
                    missing_commentary_quotes_count += 1

            # parse bht_content into commentator quotes.
            current_commentator = None
            commentator_quotes = {}
            for line in bht_content.splitlines():
                if line.startswith("###"):
                    current_commentator = line[4:-1]
                    continue
                elif line.startswith("#"):
                    current_commentator = None

                if not current_commentator:
                    continue

                if not current_commentator in commentator_quotes:
                    commentator_quotes[current_commentator] = []

                commentator_quotes[current_commentator].append(line)

            # print(commentator_quotes)

            corrupted_verse = False

            # verify that all commentary quotes really come from commentary.
            for commentator in commentators:
                commentary = get_commentary(commentator, book, chapter_number, verse_number)
                commentary_tokens = set(tokenize(commentary.lower()))
                # print(f"Commentator:\n{commentator}")
                # print()
                # print(f"Commentary Tokens:\n{commentary_tokens}")
                # print()

                for quote in commentator_quotes[commentator]:
                    quote_tokens = set(tokenize(quote.lower()))

                    # print(f"Quote Tokens:\n{quote_tokens}")
                    # print()
                    # print(f"all quote words found in commentary: {len(quote_tokens - commentary_tokens) == 0}")
                    # print(f"{quote_tokens - commentary_tokens}")
                    # input()

                    tokens_added_by_gpt = quote_tokens - commentary_tokens
                    if len(tokens_added_by_gpt) > 2:
                        output_file.write(f"## {book} {chapter_number} {verse_number} {commentator} corrupted.\n") 
                        output_file.write(f"### Original Commentary:\n[{commentary}]\n")
                        output_file.write(f"### Quote:\n[{quote}]\n")
                        output_file.write(f"### Added words:\n[{tokens_added_by_gpt}]\n\n")
                        corrupted_commentary_quotes_count += 1
                        corrupted_verse = True
                        break

            if corrupted_verse:
                corrupted_verses_count += 1




output_file.write("\n# Summary:\n")
output_file.write(f"Missing Commentary Quotes Count: {missing_commentary_quotes_count} (How many commentaries should have quotes but they're missing?)\n")
output_file.write(f"Corrupted Verses Count: {corrupted_verses_count} (How many verses have quotes with chatGPT injected opinions?)\n")
output_file.write(f"Corrupted Commentary Quotes Count: {corrupted_commentary_quotes_count} (How many commentaries have quotes with chatGPT injected opinions?)\n")
output_file.close()