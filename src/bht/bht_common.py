from bibleref import BibleRange, BibleVerse
import os

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

# HELPER FUNCTIONS

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

