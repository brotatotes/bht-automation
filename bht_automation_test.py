# IMPORTS

import openai
import os

# GLOBALS

WORKING_DIRECTORY = '.'
COMMENTARY_FOLDER = "commentary"
PROMPTS_FOLDER = "gpt prompts"
OUTPUT_FOLDER = "gpt output"
COMMENTATORS = ["Albert Barnes", "Jamieson Fausset Brown", "John Calvin", "Vincent's Word Studies"]
VERSES = ["2 Peter 1:19", "Ephesians 1:22"]
CHOICEST_FOLDER_NAME = "choicest"
BHT_FOLDER_NAME = "bht"
CHOICEST_PROMPTS = ["choicest prompt"]
BHT_PROMPTS = ["bht prompt"]
OPENAI_API_KEY = "PASTE API KEY HERE"

# HELPER FUNCTIONS

def get_book_chapter_verse(verse_ref):
    book, chapverse = verse_ref.rsplit(' ', 1)
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
            raise Exception(f'Prompt entry was blank for {commentator} for {choicest_prompt} for {verse_ref}. file path: {commentator_choicest_file}')
        
        commentator_choicests[commentator] = file_contents

    return commentator_choicests
    

# SETUP

openai.api_key = OPENAI_API_KEY

# Generate Choicest Piece

def ask_gpt_choicest(commentator, verse_ref, choicest_prompt):
    commentary_text = get_commentary(commentator, verse_ref)
    
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

    chat_completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=messages
    )

    return chat_completion.choices[0].message["content"]


def record_gpt_choicest(verse_refs, choicest_prompts, commentators):
    for verse_ref in verse_refs:    
        for commentator in commentators:        
            for choicest_prompt in choicest_prompts:
                print(f"Asking ChatGPT to get choicest for {commentator} for {verse_ref} for {choicest_prompt}...", end='')

                choicest = ask_gpt_choicest(commentator, verse_ref, choicest_prompt)
                
                book, chapter, verse = get_book_chapter_verse(verse_ref)

                out_path = f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{CHOICEST_FOLDER_NAME}/{choicest_prompt}/{book}/Chapter {chapter}/Verse {verse}/{commentator}.txt'

                print(f"Done! Writing to file: {out_path}")

                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                with open(out_path, 'w') as out_file:
                    out_file.write(choicest)


# Generate BHT! 

def ask_gpt_bht(verse_ref, choicest_prompts, bht_prompts, commentators):
    commentator_choicests = get_commentary_choicests(verse_ref, choicest_prompts, commentators)

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
        messages=messages
    )

    return chat_completion.choices[0].message["content"]
    

def record_gpt_bht(verse_refs, choicest_prompts, bht_prompts, commentators):
    for verse_ref in verse_refs:
        for choicest_prompt in choicest_prompts:
            for bht_prompt in bht_prompts:
                print(f"Asking ChatGPT to get bht for {verse_ref} via {choicest_prompt} X {bht_prompt} for {commentators}...", end='')

                bht = ask_gpt_bht(verse_ref, choicest_prompt, bht_prompt, commentators)

                book, chapter, verse = get_book_chapter_verse(verse_ref)

                out_path = f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{BHT_FOLDER_NAME}/{book}/Chapter {chapter}/Verse {verse}/{choicest_prompt} X {bht_prompt}.md'

                print(f"Done! Writing to file: {out_path}")

                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                with open(out_path, 'w') as out_file:
                    out_file.write(f"# {choicest_prompt} X {bht_prompt}; {commentators}\n\n")

                    for commentator, choicest in get_commentary_choicests(verse_ref, choicest_prompt, commentators).items():
                        out_file.write(f"## {commentator}:\n{choicest}\n\n")

                    out_file.write("\n")
                    out_file.write(f"# BHT:\n{bht}")


# Get all choicests and generate the bht from scratch.

def generate_bht(verse_refs, choicest_prompts, bht_prompts, commentators):
    record_gpt_choicest(verse_refs, choicest_prompts, commentators)
    record_gpt_bht(verse_refs, choicest_prompts, bht_prompts, commentators)


# MAIN

if __name__ == '__main__':
    record_gpt_choicest(VERSES, CHOICEST_PROMPTS, COMMENTATORS) 
    record_gpt_bht(VERSES, CHOICEST_PROMPTS, BHT_PROMPTS, COMMENTATORS)