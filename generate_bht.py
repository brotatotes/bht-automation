# IMPORTS

import openai
import os
import tiktoken
import time
from bibleref import BibleRange

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
    if any([b in str(verse_ref) for b in ["Philemon", "2 John", "3 John", "Jude", "Obadiah"]]):
        verse_ref = str(verse_ref).replace(" ", " 1:")
    book, chapverse = str(verse_ref).rsplit(' ', 1)
    chapter, verse = chapverse.split(':')
    return book, chapter, verse

def get_commentary(commentator, verse_ref):
    book, chapter, verse = get_book_chapter_verse(verse_ref)
    file_path = f'{WORKING_DIRECTORY}/{COMMENTARY_FOLDER}/{commentator}/{book}/Chapter {chapter}/Verse {verse}.txt'
    
    if not os.path.exists(file_path):
        raise Exception(f'No commentary found for {verse_ref} for {commentator}. file_path: {file_path}')
    
    file_contents = ""
    with open(file_path, 'r') as file:
        file_contents = file.read()

    if not file_contents:
        raise Exception(f'Commentary entry was blank for {verse_ref} for {commentator}. file_path: {file_path}')

    return file_contents

def get_prompt(prompt_folder, prompt_name):
    file_path = f'{WORKING_DIRECTORY}/{PROMPTS_FOLDER}/{prompt_folder}/{prompt_name}.txt'

    if not os.path.exists(file_path):
        raise Exception(f'No prompt found called {prompt_name}. file_path: {file_path}')
    
    file_contents = ""
    with open(file_path, 'r') as file:
        file_contents = file.read()

    if not file_contents:
        raise Exception(f'Prompt entry was blank for {prompt_name}. file_path: {file_path}')

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
            print(f'Prompt entry was blank for {commentator} for {choicest_prompt} for {verse_ref}. file path: {commentator_choicest_file}')
            continue
        
        commentator_choicests[commentator] = file_contents

    return commentator_choicests
    

# SETUP

openai.api_key = OPENAI_API_KEY
ENCODING = tiktoken.encoding_for_model("gpt-3.5-turbo")

# Generate Choicest Piece

def ask_gpt_choicest(commentator, verse_ref, choicest_prompt):
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


def record_gpt_choicest(verse_refs, choicest_prompts, commentators):
    for verse_ref in verse_refs:    
        for commentator in commentators:        
            for choicest_prompt in choicest_prompts:
                print(f"Asking ChatGPT to get choicest for {commentator} for {verse_ref} for {choicest_prompt}...", end='')
                
                book, chapter, verse = get_book_chapter_verse(verse_ref)

                out_path = f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{CHOICEST_FOLDER_NAME}/{choicest_prompt}/{book}/Chapter {chapter}/Verse {verse}/{commentator}.txt'

                if os.path.exists(out_path):
                    print(f"File already exists. Skipping. {out_path}")
                    continue

                choicest = ask_gpt_choicest(commentator, verse_ref, choicest_prompt)

                print(f"Done! Writing to file: {out_path}\n")

                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                with open(out_path, 'w') as out_file:
                    out_file.write(choicest)

                time.sleep(0.017) # follow rate limits


# Generate BHT! 

def ask_gpt_bht(verse_ref, choicest_prompts, bht_prompts, commentators):
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
    

def record_gpt_bht(verse_refs, choicest_prompts, bht_prompts, commentators):
    for verse_ref in verse_refs:
        for choicest_prompt in choicest_prompts:
            for bht_prompt in bht_prompts:
                book, chapter, verse = get_book_chapter_verse(verse_ref)

                out_path = f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{BHT_FOLDER_NAME}/{choicest_prompt} X {bht_prompt}/{book}/Chapter {chapter}/{book} {chapter} {verse} bht.md'

                if os.path.exists(out_path):
                    print(f"File already exists. Skipping. {out_path}")
                    continue

                print(f"Asking ChatGPT to get bht for {verse_ref} via {choicest_prompt} X {bht_prompt} for {commentators}...", end='')

                bht = ask_gpt_bht(verse_ref, choicest_prompt, bht_prompt, commentators)
                while len(bht.split()) > 100:
                    print(f"\n***BHT WAS OVER 100 WORDS! Regenerating {verse_ref}***\n")
                    bht = ask_gpt_bht(verse_ref, choicest_prompt, bht_prompt, commentators)

                print(f"Done! Writing to file: {out_path}\n")

                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                with open(out_path, 'w') as out_file:
                    out_file.write(f"# {choicest_prompt} X {bht_prompt}; {commentators}\n\n")

                    for commentator, choicest in get_commentary_choicests(verse_ref, choicest_prompt, commentators).items():
                        out_file.write(f"## {commentator}:\n{choicest}\n\n")

                    out_file.write("\n")
                    out_file.write(f"# BHT:\n{bht}")

                time.sleep(0.017) # follow rate limits


# Get all choicests and generate the bht from scratch.

def generate_bht(verse_refs, choicest_prompts, bht_prompts, commentators, tries=0, try_limit=3):
    if tries >= try_limit:
        print(f"***Failed {try_limit} times. Quitting.***")
        return
    
    try:
        record_gpt_choicest(verse_refs, choicest_prompts, commentators)
        record_gpt_bht(verse_refs, choicest_prompts, bht_prompts, commentators)
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Retrying...")
        generate_bht(verse_refs, choicest_prompts, bht_prompts, commentators, tries + 1)

# MAIN

if __name__ == '__main__':
    COMMENTATORS = ["Henry Alford", "Jamieson Fausset Brown", "Albert Barnes", "Marvin Vincent", "John Calvin", "Philip Schaff", "Archibald T Robertson", "Adam Clarke",]

    # VERSES = ["2 Peter 1:19", "Ephesians 1:22"]
    # VERSES = BibleRange("Philemon")
    # VERSES = BibleRange("Romans")
    books = [BibleRange("Philemon"), BibleRange("1 Peter"), BibleRange("Romans")]
    for book in books:
        generate_bht(book, ["choicest prompt v1"], ["bht prompt v3"], COMMENTATORS)