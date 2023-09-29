import os
import re
import string
from gensim.utils import tokenize
from bht_generation import generate_bhts
from generate import COMMENTATORS
from bht_generation import get_commentary, get_verse_ref

COMMENTATORS_SET = set(COMMENTATORS)
CHOICEST_PROMPT = "choicest prompt v2"
BHT_PROMPT = "bht prompt v5"

def get_verses_to_check(folder_to_check):
    verses = []

    for book in os.listdir(folder_to_check):
        if book.startswith('.'):
            continue

        for chapter in os.listdir(f"{folder_to_check}/{book}"):
            if chapter.startswith('.'):
                continue

            for verse in os.listdir(f"{folder_to_check}/{book}/{chapter}"):
                chapter_number, verse_number = int(chapter.split()[1]), int(verse.split()[-2])
                verses.append((book, chapter_number, verse_number))
    
    return verses


def get_bht_content(folder_to_check, book, chapter, verse):
    return open(f"{folder_to_check}/{book}/Chapter {chapter}/{book} {chapter} {verse} bht.md", 'r', encoding="utf-8").read()

def get_commentators_used(bht_content):
    pattern = r'^### .+:$'
    commentators = set([c[4:-1] for c in re.findall(pattern, bht_content, re.MULTILINE)])
    return commentators

def get_commentators_with_commentary(book, chapter, verse, all_commentators):
    commentators_with_commentary = set([])
    for commentator in all_commentators:
        commentary = get_commentary(commentator, get_verse_ref(book, chapter, verse))
        if commentary:
            commentators_with_commentary.add(commentary)

    return commentators_with_commentary


def check_commentators(folder_to_check, book, chapter, verse, all_commentators):
    bht_content = get_bht_content(folder_to_check, book, chapter, verse)
    commentators_used = get_commentators_used(bht_content)
    commentators_with_commentary = get_commentators_with_commentary(book, chapter, verse, all_commentators)

    missing_commentators = commentators_with_commentary - commentators_used
    phantom_commentators = commentators_used - commentators_with_commentary

    return missing_commentators, phantom_commentators


def parse_choicest_quotes(bht_content):
    current_commentator = None
    commentator_quotes = {}
    for line in bht_content.splitlines():
        if line.startswith("### "):
            current_commentator = line[4:-1]
            continue
        elif line.startswith("# "):
            current_commentator = None

        if not current_commentator:
            continue

        if not current_commentator in commentator_quotes:
            commentator_quotes[current_commentator] = []

        commentator_quotes[current_commentator].append(line)

    return commentator_quotes


def get_corrupted_commentator_quotes(bht_content, book, chapter, verse):
    choicest_quotes = parse_choicest_quotes(bht_content)
    commentators = get_commentators_used(bht_content)

    corrupted_quotes = {}

    for commentator in commentators:
        commentary = get_commentary(commentator, get_verse_ref(book, chapter, verse))
        commentary_tokens = set(tokenize(commentary.lower()))

        for quote in choicest_quotes[commentator]:
            quote_tokens = set(tokenize(quote.lower()))

            tokens_added_by_gpt = quote_tokens - commentary_tokens
            if len(tokens_added_by_gpt) > 2:
                if commentator not in corrupted_quotes:
                    corrupted_quotes[commentator] = []

                corrupted_quotes[commentator].append((quote, tokens_added_by_gpt))
                break
        
    return corrupted_quotes
        

def check_all_bht_contents(folder_to_check, output_filename):
    check_bht_contents(get_verses_to_check(folder_to_check), output_filename)


def check_bht_contents(verses, output_filename):
    output_file = open(output_filename, 'w', encoding="utf-8")
    output_file.write("# Issues Found:\n\n")

    corrupted_verses = []
    missing_commentator_count = 0
    phantom_commentator_count = 0
    misquoted_commentator_count = 0
    verse_i = 0

    for book, chapter, verse in verses:
        verse_i += 1
        print(f"\r{verse_i} / {len(verses)} {get_verse_ref(book, chapter, verse)}", end="")
        bht_content = get_bht_content(folder_to_check, book, chapter, verse)
        missing_commentators, phantom_commentators = check_commentators(folder_to_check, book, chapter, verse, COMMENTATORS_SET)

        for missing_commentator in missing_commentators:
            output_file.write(f"## {missing_commentator} for {book} {chapter}:{verse} has commentary but is missing!\n\n")
            missing_commentator_count += 1

        for phantom_commentator in phantom_commentators:
            output_file.write(f"## {phantom_commentator} for {book} {chapter}:{verse} has no commentary but was quoted!\n\n")
            phantom_commentator_count += 1

        corrupted_quotes = get_corrupted_commentator_quotes(bht_content, book, chapter, verse)
        for commentator in corrupted_quotes:
            commentary = get_commentary(commentator, get_verse_ref(book, chapter, verse))

            output_file.write(f"## {book} {chapter} {verse} {commentator} corrupted.\n") 
            output_file.write(f"Original Commentary:\n[{commentary}]\n")
            for quote, tokens_added_by_gpt in corrupted_quotes[commentator]:
                output_file.write(f"- Quote:\n[{quote}]\n")
                output_file.write(f"- Added words:\n[{tokens_added_by_gpt}]\n")

            misquoted_commentator_count += 1

        if corrupted_quotes:
            corrupted_verses.append(get_verse_ref(book, chapter, verse))

    result_text = f"""
# Summary:
{len(verses)} verses checked.
Missing Commentator Count: {missing_commentator_count} (How many commentaries should have quotes but they're missing?)
Phantom Commentator Count: {phantom_commentator_count} (How many commentaries have quotes but there's no commentary?)
Corrupted Verses Count: {len(corrupted_verses)} (How many verses have quotes with chatGPT injected opinions?)
Misquoted Commentator Count: {misquoted_commentator_count} (How many commentaries have quotes with chatGPT injected opinions?)
"""
    
    output_file.write(result_text)
    output_file.close()

    print(result_text)

    return corrupted_verses


if __name__ == '__main__':
    # folder_to_check = "bht gen 2"
    folder_to_check = f"gpt output/bht/{CHOICEST_PROMPT} X {BHT_PROMPT}"
    output_filename = 'check_choicests.md'

    verses_to_check = get_verses_to_check(folder_to_check)

    while verses_to_check:
        corrupted_verses = check_bht_contents(verses_to_check, output_filename)

        if corrupted_verses:
            input(f"Retry {len(corrupted_verses)} corrupted verses? ")
            generate_bhts(corrupted_verses, [CHOICEST_PROMPT], [BHT_PROMPT], COMMENTATORS, redo_choicest=True, redo_bht=True)

        verses_to_check = corrupted_verses
    