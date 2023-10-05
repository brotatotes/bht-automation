import os
import re
import string
from gensim.utils import tokenize
from bht_generation import generate_bhts, get_commentary, get_verse_ref, get_book_chapter_verse
from generate import COMMENTATORS
from bht_semantics import calculate_similarity_bert, calculate_similarity_sklearn, STOP_WORDS_SET, nlp

COMMENTATORS_SET = set(COMMENTATORS)

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
                verses.append(get_verse_ref(book, chapter_number, verse_number))
    
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
            commentators_with_commentary.add(commentator)

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
        elif line.startswith("# ") or line.startswith("## "):
            current_commentator = None

        if not current_commentator or not current_commentator in COMMENTATORS_SET:
            continue

        if not current_commentator in commentator_quotes:
            commentator_quotes[current_commentator] = []

        commentator_quotes[current_commentator].append(line)

    return commentator_quotes


def parse_bht(bht_content):
    bht_lines = []
    found = False
    for line in bht_content.splitlines():
        if line.startswith("## BHT:"):
            found = True
            continue
        elif line.startswith("## Choicest Commentary Quotes:"):
            break
        elif found:
            bht_lines.append(line)

    return '\n'.join(bht_lines)


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


def get_bht_tokens_proportion(bht_content):
    choicest_quotes = parse_choicest_quotes(bht_content)
    bht = parse_bht(bht_content)

    bht_tokens_set = set(tokenize(bht.lower()))
    quotes_tokens_set = set()
    for quotes in choicest_quotes.values():
        for quote in quotes:
            quotes_tokens_set |= set(tokenize(quote.lower()))

    tokens_not_from_quotes = bht_tokens_set - quotes_tokens_set - STOP_WORDS_SET
    proportion = 1 - len(tokens_not_from_quotes) / len(bht_tokens_set)

    return proportion

def get_overall_semantic_similarity(bht_content):
    choicest_quotes = parse_choicest_quotes(bht_content)
    bht = parse_bht(bht_content)

    return calculate_similarity_sklearn(bht, '\n\n'.join('\n'.join(l) for l in choicest_quotes.values()))


def get_footnotes(bht_content):
    choicest_quotes = parse_choicest_quotes(bht_content)
    bht = parse_bht(bht_content)

    bht_nlp = nlp(bht)
    comparisons = {} # (bht_sent_i, commentator, i) -> score

    for commentator in choicest_quotes:
        for i, quote in enumerate(choicest_quotes[commentator]):

            for j, sentence in enumerate(bht_nlp.sents):
                key = (j, commentator, i)
                if quote:
                    comparisons[key] = calculate_similarity_sklearn(str(sentence), quote)
    
    for i, s in enumerate(bht_nlp.sents):
        print(i, s)

    for k in sorted(comparisons.keys(), key=lambda k: -comparisons[k]):
        print(k, comparisons[k])
        print(list(bht_nlp.sents)[k[0]])
        print(choicest_quotes[k[1]][k[2]])
        print()

    input()




def check_bht_contents(folder_to_check, verses, output_filename):
    output_file = open(output_filename, 'w', encoding="utf-8")
    output_file.write("# Issues Found:\n\n")

    corrupted_verses = set()
    missing_commentator_count = 0
    phantom_commentator_count = 0
    misquoted_commentator_count = 0
    low_proportion_bht_count = 0
    verse_i = 0
    overall_similarity = {}

    for verse_ref in verses:
        book, chapter, verse = get_book_chapter_verse(verse_ref)
        verse_i += 1
        print(f"\r{verse_i} / {len(verses)} {get_verse_ref(book, chapter, verse)} {' ' * 10}", end="")
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
            corrupted_verses.add(get_verse_ref(book, chapter, verse))

        proportion = get_bht_tokens_proportion(bht_content)
        if proportion < 0.5:
            output_file.write(f"## {verse_ref} BHT uses only {proportion} of words from quotes.\n")
            output_file.write(f"BHT:\n{parse_bht(bht_content)}\n")
            corrupted_verses.add(get_verse_ref(book, chapter, verse))
            low_proportion_bht_count += 1

        overall_similarity[verse_ref] = get_overall_semantic_similarity(bht_content)

        # get_footnotes(bht_content)

    similarity_string = '\n'.join(str(a) for a in sorted(overall_similarity.items(), key=lambda x: x[1]))
    result_text = f"""
# Summary:
{len(verses)} verses checked.
Missing Commentator Count: {missing_commentator_count} (How many commentaries should have quotes but they're missing?)
Phantom Commentator Count: {phantom_commentator_count} (How many commentaries have quotes but there's no commentary?)
Misquoted Commentator Count: {misquoted_commentator_count} (How many commentaries have quotes with chatGPT injected opinions?)
Low Proportion BHT Count: {low_proportion_bht_count} (How many BHTs use <50% words from quotes?)
Corrupted Verses Count: {len(corrupted_verses)} (All verses with any of the issues above.)
Similarity:
{similarity_string}
"""
    
    output_file.write(result_text)
    output_file.close()

    print(result_text)

    return corrupted_verses