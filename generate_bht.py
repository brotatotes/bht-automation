# IMPORTS

import openai
import os
import tiktoken
import time
from bibleref import BibleRange, BibleVerse
from timeout_decorator import timeout
import traceback
import threading
import math
from gensim.utils import tokenize
import spacy
from bht import BHT
from multi_threaded_work_queue import MultiThreadedWorkQueue


# GLOBALS

WORKING_DIRECTORY = '.'
COMMENTARY_FOLDER = "commentary"
PROMPTS_FOLDER = "gpt prompts"
OUTPUT_FOLDER = "gpt output"
CHOICEST_FOLDER_NAME = "choicest"
BHT_FOLDER_NAME = "bht"
OPENAI_API_KEY = open('openai-api-key.txt', 'r').read().strip()

# SETUP

openai.api_key = OPENAI_API_KEY
ENCODING = tiktoken.encoding_for_model("gpt-3.5-turbo")
nlp = spacy.load("en_core_web_sm") # Load the spaCy English language model
STOP_WORDS_SET = spacy.lang.en.stop_words.STOP_WORDS # Get the list of English stopwords

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


def get_commentary_choicests(verse_ref, choicest_prompt, commentators):
    book, chapter, verse = get_book_chapter_verse(verse_ref)

    commentator_choicests = {}

    # Load commentator choicest pieces from files
    for commentator in commentators:
        commentator_choicest_file = f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{CHOICEST_FOLDER_NAME}/{choicest_prompt}/{book}/Chapter {chapter}/Verse {verse}/{commentator}.txt'

        if not os.path.exists(commentator_choicest_file):
            # raise Exception(f"No choicest file found for {commentator} for {choicest_prompt} for {verse_ref}, file path: {commentator_choicest_file}")
            continue
        
        file_contents = ""
        with open(commentator_choicest_file, 'r', encoding='utf-8') as file:
            file_contents = file.read()

        if not file_contents:
            # print(f'No choicest quotes found for {commentator}.')
            continue
        
        commentator_choicests[commentator] = file_contents

    return commentator_choicests


def get_bht_output_path(choicest_prompt, bht_prompt, book, chapter, verse):
    return f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{BHT_FOLDER_NAME}/{choicest_prompt} X {bht_prompt}/{book}/Chapter {chapter}/{book} {chapter} {verse} bht.md'

def get_choicest_output_path(choicest_prompt, book, chapter, verse, commentator):
    return f'{WORKING_DIRECTORY}/{OUTPUT_FOLDER}/{CHOICEST_FOLDER_NAME}/{choicest_prompt}/{book}/Chapter {chapter}/Verse {verse}/{commentator}.txt'



# Generate Choicest Piece

# @timeout(10)
def ask_gpt_choicest_timeout(commentator, commentary, verse_ref, choicest_prompt):
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
        "content": commentary
    })

    model = "gpt-3.5-turbo"
    token_count = sum(len(ENCODING.encode(message["content"])) for message in messages)
    if token_count > 4097:
        print(f"ℹ️ {verse_ref} {commentator} Too many tokens. Using 16k Context instead.")
        model += "-16k"

    try:
        chat_completion = openai.ChatCompletion.create(
            model=model, 
            messages=messages,
            request_timeout=15,
        )
    except openai.error.InvalidRequestError:
        print(f"ℹ️ {verse_ref} {commentator} Something went wrong. Trying 16k Context.")
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k", 
            messages=messages,
            request_timeout=15
        )

    return chat_completion.choices[0].message["content"]


def ask_gpt_choicest(commentator, commentary, verse_ref, choicest_prompt, tries=0, try_limit=10):
    if tries >= try_limit:
        raise Exception(f"❌ Failed {try_limit} times to get choicest. Quitting. ❌")
    
    try:
        return ask_gpt_choicest_timeout(commentator, commentary, verse_ref, choicest_prompt)
    except TimeoutError:
        print(f"Attempt {tries} timed out. Trying again.")
        return ask_gpt_choicest(commentator, commentary, verse_ref, choicest_prompt, tries + 1)


def record_gpt_choicest(verse_ref, choicest_prompts, commentators, force_redo=False):
    for commentator in commentators:        
            for choicest_prompt in choicest_prompts:

                # print(f"🟧 {verse_ref} {commentator} {choicest_prompt}")
                
                book, chapter, verse = get_book_chapter_verse(verse_ref)

                out_path = get_choicest_output_path(choicest_prompt, book, chapter, verse, commentator)

                choicest_not_empty = (os.path.exists(out_path) and not not open(out_path, 'r', encoding='utf-8').read().strip())
                commentary = get_commentary(commentator, verse_ref)
                no_commentary = not commentary

                if not force_redo and (no_commentary or choicest_not_empty):
                    msg = f"✅ {verse_ref} {commentator} {choicest_prompt}"
                    if no_commentary:
                        msg += f" No Commentary found. "
                    if choicest_not_empty:
                        msg += f" Choicest already exists. "

                    print(msg)
                    continue
                
                commentary_tokens_set = set(tokenize(commentary.lower()))

                commentary_length_limit = 15

                if len(commentary_tokens_set) < commentary_length_limit:
                    choicest = f"1. {commentary}"
                else:
                    while True:
                        choicest = ask_gpt_choicest(commentator, commentary, verse_ref, choicest_prompt)
                        choicest = choicest.replace('\n\n', '\n')
                        choicest_tokens = list(tokenize(choicest.lower()))
                        choicest_tokens_set = set(choicest_tokens)
                        word_count = len(choicest_tokens)

                        token_diff_limit = 2
                        word_count_limit = 150

                        diffs = len(choicest_tokens_set - commentary_tokens_set)
                        too_many_diffs = diffs > token_diff_limit
                        too_long = word_count > word_count_limit

                        if not too_many_diffs and not too_long:
                            break
                        else:
                            info_msg = [f"🔄 {verse_ref} {commentator}"]
                            info_msg.append(f"({diffs} injected words, {word_count} words)")

                            if too_many_diffs:
                                info_msg.append(f"MORE THAN {token_diff_limit} INJECTED WORDS!")

                            if too_long:
                                info_msg.append(f"MORE THAN {word_count_limit} WORDS!")

                            
                            print(' '.join(info_msg))


                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                with open(out_path, 'w', encoding='utf-8') as out_file:
                    out_file.write(choicest)

                if choicest:
                    print(f"✅ {verse_ref} {commentator} {choicest_prompt} Done!")

                # time.sleep(0.017) # follow rate limits


# Generate BHT! 
# @timeout(10)
def ask_gpt_bht_timeout(verse_ref, choicest_prompts, bht_prompts, commentator_choicests, extra_messages):
    if not commentator_choicests:
        print(f"No commentary choicests found for {verse_ref}")
        return ""

    prompt_text = get_prompt(BHT_FOLDER_NAME, bht_prompts)

    messages = []
    messages.append({
        "role": "system",
        "content": prompt_text
    })

    messages.append({
        "role": "user",
        "content": f"I'll give you {len(commentator_choicests)} messages. Each will contain quotes from a commentator."
    })

    for commentator, choicest in commentator_choicests.items():
        messages.append({
            "role": "user",
            "content": f"{choicest}"
        })

    messages.extend(extra_messages)

    model = "gpt-3.5-turbo"
    token_count = sum(len(ENCODING.encode(message["content"])) for message in messages)
    if token_count > 4097:
        print(f"ℹ️ {verse_ref} {commentator} Too many tokens. Using 16k Context instead.")
        model += "-16k"

    try:
        chat_completion = openai.ChatCompletion.create(
            model=model, 
            messages=messages,
            request_timeout=15
        )
    except openai.error.InvalidRequestError:
        print(f"ℹ️ {verse_ref} {commentator} Something went wrong. Trying 16k Context.")
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k", 
            messages=messages,
            request_timeout=15
        )

    return chat_completion.choices[0].message["content"]


def ask_gpt_bht(verse_ref, choicest_prompts, bht_prompts, commentator_choicests, extra_messages, tries=0, try_limit=10):
    if tries >= try_limit:
        raise Exception(f"❌ Failed {try_limit} times to get bht. Quitting. ❌")
    
    try:
        return ask_gpt_bht_timeout(verse_ref, choicest_prompts, bht_prompts, commentator_choicests, extra_messages)
    except TimeoutError:
        print(f"Attempt {tries} timed out. Trying again.")
        return ask_gpt_bht(verse_ref, choicest_prompts, bht_prompts, commentator_choicests, extra_messages, tries + 1)


def record_gpt_bht(verse_ref, choicest_prompts, bht_prompts, commentators, force_redo=False):
    for choicest_prompt in choicest_prompts:
        for bht_prompt in bht_prompts:
            debug_logs = []
            book, chapter, verse = get_book_chapter_verse(verse_ref)

            out_path = get_bht_output_path(choicest_prompt, bht_prompt, book, chapter, verse)

            # print(f"🟧 {verse_ref} {bht_prompt}")

            if not force_redo and os.path.exists(out_path) and not not open(out_path, 'r', encoding='utf-8').read().strip():
                msg = f"✅ {verse_ref} {bht_prompt} File already populated."
                debug_logs.append(msg)
                print(msg)
                continue

            commentator_choicests = get_commentary_choicests(verse_ref, choicest_prompt, commentators)
            choicests_tokens_set = set()
            for choicest in commentator_choicests.values():
                choicests_tokens_set |= set(tokenize(choicest.lower()))

            # these should probably be constants or something
            proportion_limits = (0.5, 0.9)
            strict_proportion_limits = (0.5, 0.9)
            target_proportion = 0.9
            word_limits = (25, 100)
            strict_word_limits = (25, 130)
            target_word_count = 80
            min_proportion_limit, max_proportion_limit = proportion_limits
            min_word_limit, max_word_limit = word_limits
            extra_messages = []
            attempts_limit = 5
            current_attempt = 0

            best_bht = None

            while current_attempt < attempts_limit:
                current_attempt += 1
                bht_text = ask_gpt_bht(verse_ref, choicest_prompt, bht_prompt, commentator_choicests, extra_messages)

                current_bht = BHT(bht_text)
                current_bht.init_checks(choicests_tokens_set, STOP_WORDS_SET, word_limits, proportion_limits, strict_word_limits, strict_proportion_limits, target_word_count, target_proportion)

                # Keep track of best BHT we've seen across all attempts.
                if current_bht > best_bht:
                    best_bht = current_bht

                if current_bht.passes_checks():
                    break

                else:
                    extra_messages.append({
                        "role": "assistant",
                        "content": bht_text
                    })

                    complaints = []

                    info_msg = [f"🔄 {verse_ref} (attempt {current_attempt}, {current_bht.word_count} words, {current_bht.proportion_percentage}% quotes, quality score: {current_bht.content_score})"]

                    if current_bht.too_many_words:
                        complaints.append(f"Please limit your response to {max_word_limit} words.")
                        info_msg.append(f"\n\t- BHT WAS OVER 100 WORDS!")
                    elif current_bht.not_enough_words:
                        complaints.append(f"Please make sure your response is at least {min_word_limit} words.")
                        info_msg.append(f"\n\t- BHT WAS UNDER {min_word_limit} WORDS!")
                    
                    if current_bht.not_enough_from_quotes:
                        complaints.append(f"Please make sure at least {min_proportion_limit * 100}% of the words in your response come from the quotes.")
                        info_msg.append(f"\n\t- LESS THAN {min_proportion_limit * 100}% OF BHT WAS FROM QUOTES!")
                    elif current_bht.too_much_from_quotes:
                        complaints.append(f"Please make sure you are not just copying the quotes.")
                        info_msg.append(f"\n\t- OVER {max_proportion_limit * 100}% OF BHT WAS FROM QUOTES!")

                    if current_bht.commentator_in_tokens:
                        complaints.append(f"Please do not use the word 'commentator' in your response.")
                        info_msg.append(f"\n\t- 'COMMENTATOR(S)' FOUND IN BHT!")

                    if current_bht.list_detected:
                        complaints.append(f"Please do not provide any kind of list. Please make sure your response is a short paragraph of sentences.")
                        info_msg.append(f"\n\t- LIST FORMAT DETECTED!")

                    extra_messages.append({
                        "role": "user",
                        "content": ' '.join(complaints)
                    })
                    
                    msg = ' '.join(info_msg)
                    debug_logs.append(msg)
                    print(msg)

            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            debug_logs.append(f"✅ {verse_ref} {bht_prompt} ({best_bht.word_count} words, {best_bht.proportion_percentage}% quotes)")

            with open(out_path, 'w', encoding='utf-8') as out_file:
                out_file.write(f"# {verse_ref} Commentary Help Text\n\n")
                out_file.write(f"## BHT:\n{best_bht.text}\n\n")

                out_file.write(f"## Choicest Commentary Quotes:\n")
                for commentator, choicest in get_commentary_choicests(verse_ref, choicest_prompt, commentators).items():
                    out_file.write(f"### {commentator}:\n{choicest}\n\n")

                out_file.write("\n")

                out_file.write(f"## Debug Info\n")
                out_file.write(f"### Generation Details\n")
                out_file.write(f"- Choicest Prompt: \"{choicest_prompt}\"\n")
                out_file.write(f"- BHT Prompt: \"{bht_prompt}\"\n")
                out_file.write(f"- Commentators: \"{', '.join(commentators)}\"\n")
                out_file.write(f"- BHT Word Count: {best_bht.word_count}\n")
                out_file.write(f"- BHT Commentary Usage: {best_bht.proportion_percentage}%\n")
                out_file.write(f"- BHT Quality Score: {best_bht.content_score}\n")
                out_file.write(f"- Generate Attempts: {current_attempt} / {attempts_limit}\n")
                out_file.write(f"- ChatGPT injected words ({len(best_bht.injected_words)}):\n\t{best_bht.injected_words}\n")
                out_file.write(f"- ChatGPT injected words (significant words only) ({len(best_bht.injected_significant_words)}):\n\t{best_bht.injected_significant_words}\n")
                out_file.write('\n')
                out_file.write(f"### Logs\n")
                out_file.write('- ' + '\n- '.join(debug_logs))
            
            print(f"✅ {verse_ref} {bht_prompt} ({best_bht.word_count} words, {best_bht.proportion_percentage}% quotes, quality score: {current_bht.content_score})")

            # time.sleep(0.017) # follow rate limits


# Get all choicests and generate the bht from scratch.

def generate_bht(verse_ref, choicest_prompts, bht_prompts, commentators, redo_choicest, redo_bht):
    record_gpt_choicest(verse_ref, choicest_prompts, commentators, redo_choicest)
    record_gpt_bht(verse_ref, choicest_prompts, bht_prompts, commentators, redo_bht)

def generate_bhts(verse_refs, choicest_prompts, bht_prompts, commentators, redo_choicest=False, redo_bht=False):
    work_queue = MultiThreadedWorkQueue()

    for verse_ref in verse_refs:
        print(verse_ref)
        work_queue.add_task(generate_bht, (verse_ref, choicest_prompts, bht_prompts, commentators, redo_choicest, redo_bht))

    input("Proceed? ")

    work_queue.start()
    work_queue.wait_for_completion()
    work_queue.stop()
        

# MAIN

if __name__ == '__main__':
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

    books = [BibleRange(b) for b in [
        # "Matthew",
        # "Mark",
        # "Luke",
        # "John",
        # "Acts",
        # "Romans",
        # "1 Corinthians",
        # "2 Corinthians",
        # "Galatians",
        # "Ephesians",
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
        # "2 John",
        # "3 John",
        # "Jude",
        # "Revelation",

        "Romans 8", 
        # "1 John 1", 
        # "John 3", 
        # "Ephesians 1",
        # "John 17:3"
        ]]
    
    verses = []
    for book in books:
        for verse in book:
            verses.append(verse)

    generate_bhts(verses, ["choicest prompt v2"], ["bht prompt v5"], COMMENTATORS)
    