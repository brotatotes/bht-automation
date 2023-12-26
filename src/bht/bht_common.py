from bibleref import BibleRange, BibleVerse
import os
import re
import shutil

# GLOBALS

WORKING_DIRECTORY = '.'
COMMENTARY_FOLDER = "commentary"
PROMPTS_FOLDER = "gpt prompts"
OUTPUT_FOLDER = "gpt output"
CHOICEST_FOLDER_NAME = "choicest"
BHT_FOLDER_NAME = "bht"

COMMENTATORS = [
    "Henry Alford",
    "Jamieson-Fausset-Brown",
    "Albert Barnes",
    "Marvin Vincent",
    "John Calvin",
    "Philip Schaff",
    "Archibald T. Robertson",
    "John Gill",
    "John Wesley"
    ]

COMMENTATORS_SET = set(COMMENTATORS)

BOOKS = [BibleRange(b) for b in [
        "Matthew",
        "Mark",
        "Luke",
        "John",
        "Acts",
        "Romans",
        "1 Corinthians",
        "2 Corinthians",
        "Galatians",
        "Ephesians",
        "Philippians",
        "Colossians",
        "1 Thessalonians",
        "2 Thessalonians",
        "1 Timothy",
        "2 Timothy",
        "Titus",
        "Philemon",
        "Hebrews",
        "James",
        "1 Peter",
        "2 Peter",
        "1 John",
        "2 John",
        "3 John",
        "Jude",
        "Revelation",
        ]]

ALL_VERSES = []
for book in BOOKS:
    for verse_ref in book:
        ALL_VERSES.append(str(verse_ref))

BOOK_CHAPTERS = {
    'Matthew': 28,
    'Mark': 16,
    'Luke': 24,
    'John': 21,
    'Acts': 28,
    'Romans': 16,
    '1 Corinthians': 16,
    '2 Corinthians': 13,
    'Galatians': 6,
    'Ephesians': 6,
    'Philippians': 4,
    'Colossians': 4,
    '1 Thessalonians': 5,
    '2 Thessalonians': 3,
    '1 Timothy': 6,
    '2 Timothy': 4,
    'Titus': 3,
    'Philemon': 1,
    'Hebrews': 13,
    'James': 5,
    '1 Peter': 5,
    '2 Peter': 3,
    '1 John': 5,
    '2 John': 1,
    '3 John': 1,
    'Jude': 1,
    'Revelation': 22
}

# HELPER FUNCTIONS

def get_bht_json_path(choicest_prompt, bht_prompt, book, chapter, verse):
    return f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{BHT_FOLDER_NAME}/json/{choicest_prompt} X {bht_prompt}/{book}/Chapter {chapter}/{book} {chapter} {verse} bht.json'

def get_bht_md_path(choicest_prompt, bht_prompt, book, chapter, verse):
    return f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{BHT_FOLDER_NAME}/md/{choicest_prompt} X {bht_prompt}/{book}/Chapter {chapter}/{book} {chapter} {verse} bht.md'

def get_choicest_output_path(choicest_prompt, book, chapter, verse, commentator):
    return f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{CHOICEST_FOLDER_NAME}/{choicest_prompt}/{book}/Chapter {chapter}/Verse {verse}/{commentator}.txt'

def get_book_chapter_verse(verse_ref):
    verse_ref = str(verse_ref)
    if any([b in verse_ref for b in ["Philemon", "2 John", "3 John", "Jude", "Obadiah"]]) and ':' not in verse_ref:
        parts = verse_ref.rsplit(' ', 1)
        verse_ref = parts[0] + " 1:" + parts[1]
    book, chapverse = verse_ref.rsplit(' ', 1)
    chapter, verse = chapverse.split(':')
    return book, chapter, verse

def get_verse_ref(book, chapter, verse):
    return f"{book} {chapter}:{verse}"

def get_commentary(commentator, verse_ref):
    book, chapter, verse = get_book_chapter_verse(verse_ref)
    file_path = f'{WORKING_DIRECTORY}/{COMMENTARY_FOLDER}/{commentator}/{book}/Chapter {chapter}/Verse {verse}.txt'
    
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

def get_prompt(prompt_folder, prompt_name):
        file_path = f'{WORKING_DIRECTORY}/{PROMPTS_FOLDER}/{prompt_folder}/{prompt_name}.txt'

        if not os.path.exists(file_path):
            raise Exception(f'No prompt found called {prompt_name}.')
        
        file_contents = ""
        with open(file_path, 'r', encoding='utf-8') as file:
            file_contents = file.read()

        if not file_contents:
            raise Exception(f'Prompt entry was blank for {prompt_name}.')

        return file_contents


def get_verses_from_folder(folder_path):
    verses = []

    for book in os.listdir(folder_path):
        if book.startswith('.'):
            continue

        for chapter in os.listdir(f"{folder_path}/{book}"):
            if chapter.startswith('.'):
                continue

            for verse in os.listdir(f"{folder_path}/{book}/{chapter}"):
                chapter_number, verse_number = int(chapter.split()[1]), int(verse.split()[-2])
                verses.append(get_verse_ref(book, chapter_number, verse_number))

    return verses

def get_commentatory_shorthand_name(commentator):
    shorthand_names = {
        "Henry Alford": "alford",
        "Jamieson-Fausset-Brown": "jfb",
        "Albert Barnes": "barnes",
        "Marvin Vincent": "vws",
        "John Calvin": "calvin",
        "Philip Schaff": "schaff",
        "Archibald T. Robertson": "rwp",
        "John Gill": "gill",
        "John Wesley": "wesley"
    }

    return shorthand_names[commentator]

def find_all_in_string(substring, input_string):
    indices = [i for i in range(len(input_string)) if input_string.startswith(substring, i)]
    return indices

def find_all_in_list(item, item_list):
    indices = [i for i in range(len(item_list)) if item_list[i] == item]
    return indices

def remove_html_tags(html_text):
    if not html_text:
        return ''
    text = re.sub(r'<.*?>', '', html_text)
    text = re.sub(r' +', ' ', text)
    return text

def copy_file(source_path, destination_path):
    try:
        shutil.copy2(source_path, destination_path)
        print(f"File copied successfully from {source_path} to {destination_path}")
    except FileNotFoundError:
        print(f"Error: Source file {source_path} not found.")
    except PermissionError:
        print(f"Error: Permission denied to copy to {destination_path}")
    except Exception as e:
        print(f"An error occurred: {e}")