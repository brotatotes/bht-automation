import os
import re
import string
from gensim.utils import tokenize
from bht.bht_generation import generate_bhts, get_commentary, get_verse_ref, get_book_chapter_verse
from bht.bht_semantics import calculate_similarity_bert, calculate_similarity_sklearn, calculate_similarity_tensorflow, STOP_WORDS_SET, nlp

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize


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


def check_commentators(bht_content, book, chapter, verse, all_commentators):
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


def get_corrupted_commentator_quotes(bht_content, book, chapter, verse, choicest_quotes):
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


def get_bht_tokens_proportion(bht, choicest_quotes):
    bht_tokens_set = set(tokenize(bht.lower()))
    quotes_tokens_set = set()
    for quotes in choicest_quotes.values():
        for quote in quotes:
            quotes_tokens_set |= set(tokenize(quote.lower()))

    tokens_not_from_quotes = bht_tokens_set - quotes_tokens_set - STOP_WORDS_SET
    proportion = 1 - len(tokens_not_from_quotes) / len(bht_tokens_set)

    return proportion

# def get_overall_semantic_similarity(bht, choicest_quotes):
#     return calculate_similarity_sklearn(bht, '\n\n'.join('\n'.join(l) for l in choicest_quotes.values()))


def get_stop_words():
    return set([line.strip() for line in open('src/stopwords.txt', 'r')])

def tokenize_using_lemmatization(text):
    lemmatizer = WordNetLemmatizer()
    translator = str.maketrans('', '', string.punctuation)
    words = word_tokenize(text.lower().translate(translator))
    return set([lemmatizer.lemmatize(word) for word in words])

def compute_token_similarity(text1, text2):
    stop_words = get_stop_words()
    tokens1 = tokenize_using_lemmatization(text1) - stop_words
    tokens2 = tokenize_using_lemmatization(text2) - stop_words

    similarity = len(tokens1 & tokens2) / len(tokens1 | tokens2)
    
    return similarity

def compute_semantic_similarity(text1, text2):
    return calculate_similarity_tensorflow(text1, text2)

def compute_combined_similarity(text1, text2):
    text1, text2 = str(text1), str(text2)
    token_similarity = compute_token_similarity(text1, text2)
    semantic_similarity = compute_semantic_similarity(text1, text2)

    return token_similarity * 0.5 + semantic_similarity * 0.5


def compute_similarity(bht, choicest_quotes):
    choicest_quotes_comparisons = []
    best_scores = []
    for i, bht_sentence in enumerate(nlp(bht).sents):
        # compute similarity score with product.
        
        best_score = 0
        for commentator in choicest_quotes:
            for j, quote in enumerate(choicest_quotes[commentator]):
                if not quote:
                    continue

                score = compute_combined_similarity(bht_sentence, quote)
                if score > best_score:
                    best_score = score

                choicest_quotes_comparisons.append((i, bht_sentence, commentator, j, quote, score))
        
        best_scores.append(best_score)


    # can use this to get footnotes!!!    

    # sort by bht_sentence, then highest score.
    # choicest_quotes_comparisons.sort(key=lambda x: (x[0], -x[5]))

    # for comp in choicest_quotes_comparisons: 
        # i, bht_sentence, commentator, j, quote, score = comp
        # print(i, score, commentator, j)
        # print(f"BHT: {bht_sentence}")
        # print(f"Quote: {quote}")
        # print()

    return sum(best_scores) / len(best_scores)


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
        bht = parse_bht(bht_content)
        choicest_quotes = parse_choicest_quotes(bht_content)
        missing_commentators, phantom_commentators = check_commentators(bht_content, book, chapter, verse, COMMENTATORS_SET)

        for missing_commentator in missing_commentators:
            output_file.write(f"## {missing_commentator} for {book} {chapter}:{verse} has commentary but is missing!\n\n")
            missing_commentator_count += 1

        for phantom_commentator in phantom_commentators:
            output_file.write(f"## {phantom_commentator} for {book} {chapter}:{verse} has no commentary but was quoted!\n\n")
            phantom_commentator_count += 1

        corrupted_quotes = get_corrupted_commentator_quotes(bht_content, book, chapter, verse, choicest_quotes)
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

        proportion = get_bht_tokens_proportion(bht, choicest_quotes)
        if proportion < 0.5:
            output_file.write(f"## {verse_ref} BHT uses only {proportion} of words from quotes.\n")
            output_file.write(f"BHT:\n{bht}\n")
            corrupted_verses.add(get_verse_ref(book, chapter, verse))
            low_proportion_bht_count += 1

        overall_similarity[verse_ref] = compute_similarity(bht, choicest_quotes)

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