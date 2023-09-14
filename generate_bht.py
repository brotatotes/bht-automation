# IMPORTS

import openai
import os
import tiktoken
import time
from bibleref import BibleRange
from timeout_decorator import timeout

# GLOBALS

WORKING_DIRECTORY = '.'
COMMENTARY_FOLDER = "commentary"
PROMPTS_FOLDER = "gpt prompts"
OUTPUT_FOLDER = "gpt output"
CHOICEST_FOLDER_NAME = "choicest"
BHT_FOLDER_NAME = "bht"
OPENAI_API_KEY = open('openai-api-key.txt', 'r').read().strip()

# HELPER FUNCTIONS

def get_book_chapter_verse(verse_ref):
    verse_ref = str(verse_ref)
    if any([b in verse_ref for b in ["Philemon", "2 John", "3 John", "Jude", "Obadiah"]]):
        parts = verse_ref.rsplit(' ', 1)
        verse_ref = parts[0] + " 1:" + parts[1]
    book, chapverse = verse_ref.rsplit(' ', 1)
    chapter, verse = chapverse.split(':')
    return book, chapter, verse

def get_commentary(commentator, verse_ref):
    book, chapter, verse = get_book_chapter_verse(verse_ref)
    file_path = f'{WORKING_DIRECTORY}/{COMMENTARY_FOLDER}/{commentator}/{book}/Chapter {chapter}/Verse {verse}.txt'
    
    if not os.path.exists(file_path):
        raise Exception(f'No commentary found for {verse_ref} for {commentator}.')
    
    file_contents = ""
    with open(file_path, 'r') as file:
        file_contents = file.read()

    if not file_contents:
        raise Exception(f'Commentary entry was blank for {verse_ref} for {commentator}.')

    return file_contents

def get_prompt(prompt_folder, prompt_name):
    file_path = f'{WORKING_DIRECTORY}/{PROMPTS_FOLDER}/{prompt_folder}/{prompt_name}.txt'

    if not os.path.exists(file_path):
        raise Exception(f'No prompt found called {prompt_name}.')
    
    file_contents = ""
    with open(file_path, 'r') as file:
        file_contents = file.read()

    if not file_contents:
        raise Exception(f'Prompt entry was blank for {prompt_name}.')

    return file_contents


def get_commentary_choicests(verse_ref, choicest_prompt, commentators):
    book, chapter, verse = get_book_chapter_verse(verse_ref)

    commentator_choicests = {}

    # Load commentator choicest pieces from files
    for commentator in commentators:
        commentator_choicest_file = f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{CHOICEST_FOLDER_NAME}/{choicest_prompt}/{book}/Chapter {chapter}/Verse {verse}/{commentator}.txt'

        if not os.path.exists(commentator_choicest_file):
            raise Exception(f"No choicest file found for {commentator} for {choicest_prompt} for {verse_ref}, file path: {commentator_choicest_file}")
        
        file_contents = ""
        with open(commentator_choicest_file, 'r') as file:
            file_contents = file.read()

        if not file_contents:
            # print(f'No choicest quotes found for {commentator}.')
            continue
        
        commentator_choicests[commentator] = file_contents

    return commentator_choicests
    

# SETUP

openai.api_key = OPENAI_API_KEY
ENCODING = tiktoken.encoding_for_model("gpt-3.5-turbo")

# Generate Choicest Piece
@timeout(10)
def ask_gpt_choicest_timeout(commentator, verse_ref, choicest_prompt):
    try:
        commentary_text = get_commentary(commentator, verse_ref)
    except:
        print(f"No commentary found for {commentator} for {verse_ref}.")
        return ""
    
    prompt_text = get_prompt(CHOICEST_FOLDER_NAME, choicest_prompt)
    messages = []

    messages.append({
        "role": "system",
        "content": prompt_text
    })

    messages.append({
        "role": "user",
        "content": "I'll give you the commentary in the following message."
    })

    messages.append({
        "role": "user",
        "content": commentary_text
    })

    model = "gpt-3.5-turbo"
    token_count = sum(len(ENCODING.encode(message["content"])) for message in messages)
    if token_count > 4097:
        print("*Too many tokens. Using 16k Context instead.*")
        model += "-16k"

    try:
        chat_completion = openai.ChatCompletion.create(
            model=model, 
            messages=messages,
            temperature=0.3
        )
    except openai.error.InvalidRequestError:
        print("*4k didn't work. Trying 16k Context.*")
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k", 
            messages=messages
        )

    return chat_completion.choices[0].message["content"]

def ask_gpt_choicest(commentator, verse_ref, choicest_prompt, tries=0, try_limit=10):
    if tries >= try_limit:
        raise Exception(f"***Failed {try_limit} times to get choicest. Quitting.***")
    
    try:
        return ask_gpt_choicest_timeout(commentator, verse_ref, choicest_prompt)
    except TimeoutError:
        print(f"Attempt {tries} timed out. Trying again.")
        return ask_gpt_choicest(commentator, verse_ref, choicest_prompt, tries + 1)


def record_gpt_choicest(verse_ref, choicest_prompts, commentators):
    for commentator in commentators:        
            for choicest_prompt in choicest_prompts:

                print(f"🟧 {commentator} {choicest_prompt}", end="", flush=True)
                
                book, chapter, verse = get_book_chapter_verse(verse_ref)

                out_path = f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{CHOICEST_FOLDER_NAME}/{choicest_prompt}/{book}/Chapter {chapter}/Verse {verse}/{commentator}.txt'

                if os.path.exists(out_path):
                    print(f"\r✅ {commentator} {choicest_prompt} File already exists.", flush=True)
                    continue

                choicest = ask_gpt_choicest(commentator, verse_ref, choicest_prompt)

                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                with open(out_path, 'w') as out_file:
                    out_file.write(choicest)

                if choicest:
                    print(f"\r✅ {commentator} {choicest_prompt} Done!", flush=True)

                # time.sleep(0.017) # follow rate limits


# Generate BHT! 
@timeout(10)
def ask_gpt_bht_timeout(verse_ref, choicest_prompts, bht_prompts, commentators):
    commentator_choicests = get_commentary_choicests(verse_ref, choicest_prompts, commentators)

    if not commentator_choicests:
        print("No commentary choicests found for {verse_ref}")
        return ""

    prompt_text = get_prompt(BHT_FOLDER_NAME, bht_prompts)

    messages = []
    messages.append({
        "role": "system",
        "content": prompt_text
    })

    messages.append({
        "role": "user",
        "content": f"I'll give you {len(commentator_choicests)} messages. Each will contain quotes from a specific commentator. The first line will be the name of the commentator."
    })

    for commentator, choicest in commentator_choicests.items():
        messages.append({
            "role": "user",
            "content": f"{commentator}\n{choicest}"
        })

    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=messages,
    )

    return chat_completion.choices[0].message["content"]


def ask_gpt_bht(verse_ref, choicest_prompts, bht_prompts, commentators, tries=0, try_limit=10):
    if tries >= try_limit:
        raise Exception(f"***Failed {try_limit} times to get bht. Quitting.***")
    
    try:
        return ask_gpt_bht_timeout(verse_ref, choicest_prompts, bht_prompts, commentators)
    except TimeoutError:
        print(f"Attempt {tries} timed out. Trying again.")
        return ask_gpt_bht(verse_ref, choicest_prompts, bht_prompts, commentators, tries + 1)


def record_gpt_bht(verse_ref, choicest_prompts, bht_prompts, commentators):
    for choicest_prompt in choicest_prompts:
        for bht_prompt in bht_prompts:
            book, chapter, verse = get_book_chapter_verse(verse_ref)

            out_path = f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{BHT_FOLDER_NAME}/{choicest_prompt} X {bht_prompt}/{book}/Chapter {chapter}/{book} {chapter} {verse} bht.md'

            print(f"🟧 {bht_prompt}", end="", flush=True)

            if os.path.exists(out_path):
                print(f"\r✅ {bht_prompt} File already exists.", flush=True)
                continue

            bht = ask_gpt_bht(verse_ref, choicest_prompt, bht_prompt, commentators)
            while len(bht.split()) > 100:
                print(f"***BHT WAS OVER 100 WORDS! Regenerating {verse_ref}***")
                bht = ask_gpt_bht(verse_ref, choicest_prompt, bht_prompt, commentators)

            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            with open(out_path, 'w') as out_file:
                out_file.write(f"# {verse_ref} Commentary Help Text\n\n")
                out_file.write(f"## BHT:\n{bht}\n\n")

                out_file.write(f"## Choicest Commentary Quotes:\n")
                for commentator, choicest in get_commentary_choicests(verse_ref, choicest_prompt, commentators).items():
                    out_file.write(f"### {commentator}:\n{choicest}\n\n")

                out_file.write("\n")

                out_file.write(f"## Generation Details\n")
                out_file.write(f"- Choicest Prompt: \"{choicest_prompt}\"\n")
                out_file.write(f"- BHT Prompt: \"{bht_prompt}\"\n")
                out_file.write(f"- Commentators: \"{', '.join(commentators)}\"\n")
            
            print(f"\r✅ {bht_prompt} Done!", flush=True)

            # time.sleep(0.017) # follow rate limits


# Get all choicests and generate the bht from scratch.

def generate_bht(verse_refs, choicest_prompts, bht_prompts, commentators, tries=0, try_limit=10):
    if tries >= try_limit:
        print(f"***Failed {try_limit} times. Quitting.***")
        return
    
    try:
        for verse_ref in verse_refs:
            print(f"Generating BHT for {verse_ref}:")
            record_gpt_choicest(verse_ref, choicest_prompts, commentators)
            record_gpt_bht(verse_ref, choicest_prompts, bht_prompts, commentators)
            print(f"✅ *{verse_ref} BHT Done!*")
            print()
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Retrying in {5 * tries} seconds...")
        time.sleep(5 * tries)
        generate_bht(verse_refs, choicest_prompts, bht_prompts, commentators, tries + 1)

# MAIN

if __name__ == '__main__':
    COMMENTATORS = [
        "Henry Alford",
        "Jamieson Fausset Brown",
        "Albert Barnes",
        "Marvin Vincent",
        "John Calvin",
        "Philip Schaff",
        "Archibald T Robertson",
        "John Gill",
        "John Wesley"
        ]
    
    # books = [
    #     BibleRange("Romans 8:1-11")
    # ]

    books = [BibleRange(b) for b in [
        # "Matthew",
        # "Mark",
        # "Luke",
        "John",
        # "Acts",
        "Romans",
        # "1 Corinthians",
        # "2 Corinthians",
        # "Galatians",
        "Ephesians",
        # "Philippians",
        # "Colossians",
        # "1 Thessalonians",
        # "2 Thessalonians",
        # "1 Timothy",
        # "2 Timothy",
        # "Titus",
        # "Philemon",
        # "Hebrews",
        # "James",
        # "1 Peter",
        # "2 Peter",
        # "1 John",
        "2 John",
        "3 John",
        "Jude",
        # "Revelation",
        ]]

    for book in books:
        generate_bht(book, ["choicest prompt v1"], ["bht prompt v3"], COMMENTATORS)