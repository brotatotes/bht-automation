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
import re
# from bht import BHT


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
STOP_WORDS = spacy.lang.en.stop_words.STOP_WORDS # Get the list of English stopwords

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
            # temperature=0.3
        )
    except openai.error.InvalidRequestError:
        print(f"ℹ️ {verse_ref} {commentator} Something went wrong. Trying 16k Context.")
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k", 
            messages=messages
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

                # print(f"🟧 {verse_ref} {commentator} {choicest_prompt}", flush=True)
                
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
                
                commentary_tokens = set(tokenize(commentary.lower()))

                commentary_length_limit = 15

                if len(commentary_tokens) < commentary_length_limit:
                    choicest = f"1. {commentary}"
                else:
                    while True:
                        choicest = ask_gpt_choicest(commentator, commentary, verse_ref, choicest_prompt)
                        choicest_tokens = set(tokenize(choicest.lower()))

                        token_diff_limit = 2

                        if len(choicest_tokens - commentary_tokens) > token_diff_limit:
                            print(f"🔄 {verse_ref} {commentator} MORE THAN {token_diff_limit} INJECTED WORDS! Regenerating.")
                        else:
                            break

                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                with open(out_path, 'w', encoding='utf-8') as out_file:
                    out_file.write(choicest)

                if choicest:
                    print(f"✅ {verse_ref} {commentator} {choicest_prompt} Done!", flush=True)

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
            # temperature=0.3
        )
    except openai.error.InvalidRequestError:
        print(f"ℹ️ {verse_ref} {commentator} Something went wrong. Trying 16k Context.")
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k", 
            messages=messages
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

            # print(f"🟧 {verse_ref} {bht_prompt}", flush=True)

            if not force_redo and os.path.exists(out_path):
                msg = f"✅ {verse_ref} {bht_prompt} File already exists."
                debug_logs.append(msg)
                print(msg)
                continue

            commentator_choicests = get_commentary_choicests(verse_ref, choicest_prompt, commentators)
            choicests_tokens = set()
            for choicest in commentator_choicests.values():
                choicests_tokens |= set(tokenize(choicest.lower()))

            proportion_min_limit = 0.7
            proportion_max_limit = 0.99
            max_word_limit = 100
            min_word_limit = 25
            extra_messages = []
            attempts_limit = 5
            current_attempt = 0

            best_bht_content = None
            best_bht_proportion_percentage = 0

            while current_attempt < attempts_limit:
                current_attempt += 1
                bht_content = ask_gpt_bht(verse_ref, choicest_prompt, bht_prompt, commentator_choicests, extra_messages)

                # Manually clean BHT.
                bht_content = bht_content.replace("\"", "") # Remove quotation marks.
                bht_content = re.sub(r'^[^a-zA-Z]*', '', bht_content) # Remove non-letter characters from beginning.

                bht_tokens = list(tokenize(bht_content.lower()))
                bht_tokens_set = set(bht_tokens)
                tokens_not_from_choicests = len(bht_tokens_set - choicests_tokens - STOP_WORDS)
                proportion_from_choicests = 1 - tokens_not_from_choicests / len(bht_tokens_set)
                proportion_from_choicests_rounded_percentage = round(proportion_from_choicests * 100, 2)

                # Manually check word count and quotes usage.
                too_many_words = len(bht_tokens) > max_word_limit
                not_enough_words = len(bht_tokens) < min_word_limit
                not_enough_from_quotes = proportion_from_choicests < proportion_min_limit
                too_much_from_quotes = proportion_from_choicests > proportion_max_limit
                commentator_in_tokens = "commentator" in bht_tokens_set or "commentators" in bht_tokens_set

                needs_another_attempt = too_many_words or not_enough_words or not_enough_from_quotes or too_much_from_quotes or commentator_in_tokens

                # Keep track of best BHT we've seen across all attempts.
                if (best_bht_content == None or 
                    (not too_much_from_quotes and not not_enough_words and len(bht_tokens) <= len(best_bht_tokens) and proportion_from_choicests_rounded_percentage >= best_bht_proportion_percentage) or
                    (not too_many_words and not not_enough_words and not too_much_from_quotes and proportion_from_choicests_rounded_percentage > best_bht_proportion_percentage)):
                    best_bht_content = bht_content
                    best_bht_proportion_percentage = proportion_from_choicests_rounded_percentage
                    best_bht_tokens = bht_tokens
                    best_bht_tokens_set = bht_tokens_set

                if needs_another_attempt:
                    extra_messages.append({
                        "role": "assistant",
                        "content": bht_content
                    })

                    complaints = []

                    info_msg = [f"🔄 {verse_ref}"]

                    if too_many_words:
                        complaints.append(f"Please limit your response to {max_word_limit} words.")
                        info_msg.append(f"BHT WAS OVER 100 WORDS! ({len(bht_tokens)}).")
                    elif not_enough_words:
                        complaints.append(f"Please make sure your response is at least {min_word_limit} words.")
                        info_msg.append(f"BHT WAS UNDER 20 WORDS! ({len(bht_tokens)}).")
                    
                    if not_enough_from_quotes:
                        complaints.append(f"Please make sure at least {proportion_min_limit * 100}% of the words in your response come from the quotes.")
                        info_msg.append(f"LESS THAN {proportion_min_limit * 100}% OF BHT WAS FROM QUOTES! ({proportion_from_choicests_rounded_percentage}%).")
                    elif too_much_from_quotes:
                        complaints.append(f"Please make sure you are not just copying the quotes.")
                        info_msg.append(f"MORE THAN {proportion_max_limit * 100}% OF BHT WAS FROM QUOTES! ({proportion_from_choicests_rounded_percentage}%).")

                    if commentator_in_tokens:
                        complaints.append(f"Please do not use the word 'commentator' in your response.")
                        info_msg.append(f"'COMMENTATOR' FOUND IN BHT!")

                    info_msg.append("Regenerating.")

                    extra_messages.append({
                        "role": "user",
                        "content": ' '.join(complaints)
                    })
                    
                    msg = ' '.join(info_msg)
                    debug_logs.append(msg)
                    print(msg)

                else:
                    break

            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            debug_logs.append(f"✅ {verse_ref} {bht_prompt} Done!")

            with open(out_path, 'w', encoding='utf-8') as out_file:
                out_file.write(f"# {verse_ref} Commentary Help Text\n\n")
                out_file.write(f"## BHT:\n{best_bht_content}\n\n")

                out_file.write(f"## Choicest Commentary Quotes:\n")
                for commentator, choicest in get_commentary_choicests(verse_ref, choicest_prompt, commentators).items():
                    out_file.write(f"### {commentator}:\n{choicest}\n\n")

                out_file.write("\n")

                out_file.write(f"## Debug Generation Details\n")
                out_file.write(f"- Choicest Prompt: \"{choicest_prompt}\"\n")
                out_file.write(f"- BHT Prompt: \"{bht_prompt}\"\n")
                out_file.write(f"- Commentators: \"{', '.join(commentators)}\"\n")
                out_file.write(f"- BHT Word Count: {len(best_bht_tokens)}\n")
                out_file.write(f"- BHT Commentary Usage: {best_bht_proportion_percentage}%\n")
                out_file.write(f"- Generate Attempts: {current_attempt} / {attempts_limit}\n")
                injected_words = sorted(list(best_bht_tokens_set - choicests_tokens))
                out_file.write(f"- ChatGPT injected words ({len(injected_words)}):\n\t{injected_words}\n")
                injected_significant_words = sorted(list(best_bht_tokens_set - choicests_tokens - STOP_WORDS))
                out_file.write(f"- ChatGPT injected words (significant words only) ({len(injected_significant_words)}):\n\t{injected_significant_words}\n")
                out_file.write(f"### Debug Logs\n")
                out_file.write('- ' + '\n- '.join(debug_logs))
            
            print(f"✅ {verse_ref} {bht_prompt} Done! ({len(best_bht_tokens)} words, {best_bht_proportion_percentage}% quotes)", flush=True)

            # time.sleep(0.017) # follow rate limits


# Get all choicests and generate the bht from scratch.


def generate_bht_concurrently(verse_refs, choicest_prompts, bht_prompts, commentators, tries=0, try_limit=1000, redo_choicest=False, redo_bht=False):
    verse_refs = [verse for verse in verse_refs]
    verses_done = 0
    verses_total = len(verse_refs)

    lock = threading.Lock()

    def generate_bht(verse_refs, choicest_prompts, bht_prompts, commentators, tries=0, try_limit=50, redo_choicest=False, redo_bht=False):
        nonlocal verses_done
        nonlocal verses_total
        nonlocal lock

        if tries >= try_limit:
            print(f"❌ Failed {try_limit} times. Quitting. ❌")
            return
        
        verse_i = 0
        
        try:
            for i, verse_ref in enumerate(verse_refs):
                verse_i = i
                # print(f"Generating BHT for {verse_ref}:")
                record_gpt_choicest(verse_ref, choicest_prompts, commentators, redo_choicest)
                record_gpt_bht(verse_ref, choicest_prompts, bht_prompts, commentators, redo_bht)
                # print(f"{verse_ref} BHT Done!")
                # print()
                with lock:
                    verses_done += 1
                print(f"🚧 COMPLETION: {verses_done} / {verses_total}")

        except Exception as e:
            print(f"❗An error occurred: {e}")
            # print(traceback.format_exc())
            wait_time = tries * 5
            print(f"Try # {tries} Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            generate_bht(verse_refs[verse_i:], choicest_prompts, bht_prompts, commentators, tries=tries + 1, try_limit=try_limit, redo_choicest=redo_choicest, redo_bht=redo_bht)


    verses_per_thread = math.ceil(len(verse_refs) / 100.0)
    num_threads = math.ceil(len(verse_refs) / verses_per_thread)
    threads = []
    verse_ref_i = 0
    for i in range(num_threads):
        verses = verse_refs[verse_ref_i : min(verse_ref_i + verses_per_thread, len(verse_refs))]
        verse_ref_i += verses_per_thread
        print(f"Creating thread {i} for: {verses}")
        thread = threading.Thread(target=generate_bht, args=(verses, choicest_prompts, bht_prompts, commentators, tries, try_limit, redo_choicest, redo_bht))
        threads.append(thread)
        # thread.start()
    
    input("Proceed? ")

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()




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
        "1 John 4"
        ]]
    
    verses = []
    for book in books:
        for verse in book:
            verses.append(verse)

    start_time = time.time()

    generate_bht_concurrently(verses, ["choicest prompt v2"], ["bht prompt v5"], COMMENTATORS)

    elapsed_time = time.time() - start_time
    print(f"That took {elapsed_time} seconds.")
    