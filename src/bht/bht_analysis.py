import os
import re
import string
from gensim.utils import tokenize
from bht.bht_generation import generate_bhts, get_commentary, get_verse_ref, get_book_chapter_verse
from bht.bht_semantics import calculate_similarity_bert, calculate_similarity_sklearn, calculate_similarity_tensorflow, STOP_WORDS_SET, nlp
from bht.bht_readability import calculate_flesch_kincaid_ease, calculate_flesch_kincaid_grade, calculate_automated_readability_index, calculate_dale_chall_readability, calculate_gunning_fog

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


# TODO: Make this class make sense.
class BHTAnalyzer:
    def __init__(self):
        pass

    def get_bht_content(self, folder_to_check, book, chapter, verse):
        return open(f"{folder_to_check}/{book}/Chapter {chapter}/{book} {chapter} {verse} bht.md", 'r', encoding="utf-8").read()

    def get_commentators_used(self, bht_content):
        pattern = r'^### .+:$'
        commentators = set([c[4:-1] for c in re.findall(pattern, bht_content, re.MULTILINE)])
        return commentators

    def get_commentators_with_commentary(self, book, chapter, verse, all_commentators):
        commentators_with_commentary = set([])
        for commentator in all_commentators:
            commentary = get_commentary(commentator, get_verse_ref(book, chapter, verse))
            if commentary:
                commentators_with_commentary.add(commentator)

        return commentators_with_commentary


    def check_commentators(self, bht_content, book, chapter, verse, all_commentators):
        commentators_used = self.get_commentators_used(bht_content)
        commentators_with_commentary = self.get_commentators_with_commentary(book, chapter, verse, all_commentators)

        missing_commentators = commentators_with_commentary - commentators_used
        phantom_commentators = commentators_used - commentators_with_commentary

        return missing_commentators, phantom_commentators


    def parse_choicest_quotes(self, bht_content):
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

            quote = re.sub(r'^\d. *', '', line)
            quote = re.sub(r'^"', '', quote)
            quote = re.sub(r'"$', '', quote)

            commentator_quotes[current_commentator].append(quote)

        return commentator_quotes


    def parse_bht(self, bht_content):
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


    def get_corrupted_commentator_quotes(self, bht_content, book, chapter, verse, choicest_quotes):
        commentators = self.get_commentators_used(bht_content)

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


    def get_bht_tokens_proportion(self, bht, choicest_quotes):
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


    def get_stop_words(self):
        return set([line.strip() for line in open('src/stopwords.txt', 'r')])

    def tokenize_using_lemmatization(self, text):
        lemmatizer = WordNetLemmatizer()
        translator = str.maketrans('', '', string.punctuation)
        words = word_tokenize(text.lower().translate(translator))
        return set([lemmatizer.lemmatize(word) for word in words])

    def compute_token_similarity(self, text1, text2):
        stop_words = self.get_stop_words()
        tokens1 = self.tokenize_using_lemmatization(text1) - stop_words
        tokens2 = self.tokenize_using_lemmatization(text2) - stop_words

        if len(tokens1) + len(tokens2) == 0:
            return 0

        similarity = len(tokens1 & tokens2) / len(tokens1 | tokens2)
        
        return similarity

    def compute_semantic_similarity(self, text1, text2):
        return calculate_similarity_tensorflow(text1, text2)

    def compute_combined_similarity(self, text1, text2):
        text1, text2 = str(text1), str(text2)
        token_similarity = self.compute_token_similarity(text1, text2)
        semantic_similarity = self.compute_semantic_similarity(text1, text2)

        return token_similarity * 0.5 + semantic_similarity * 0.5


    def compute_similarity_score(self, bht, choicest_quotes):
        choicest_quotes_comparisons = []
        best_scores = []
        for i, bht_sentence in enumerate(nlp(bht).sents):        
            best_score = 0
            for commentator in choicest_quotes:
                for j, quote in enumerate(choicest_quotes[commentator]):
                    if not quote:
                        continue
                    
                    bht_sentence, quote = str(bht_sentence), str(quote)
                    semantic_similarity = self.compute_semantic_similarity(bht_sentence, quote)
                    token_similarity = self.compute_token_similarity(bht_sentence, quote)
                    score = token_similarity * 0.2 + semantic_similarity * 0.8
                    if score > best_score:
                        best_score = score

                    choicest_quotes_comparisons.append((i + 1, commentator, j + 1, token_similarity, semantic_similarity))
            
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

        return choicest_quotes_comparisons


    def avg(self, nums):
        if not nums:
            return 0
        
        return sum(nums) / len(nums)


    def get_similarity_scores(self):
        similarity_scores = {}
        with open('scripts output/V2 quote similarity scores.txt', 'r') as file:
            lines = file.readlines()
            rows = lines[1:]
            for row in rows:
                row = row.strip().split('|')
                book, chapter, verse, bht_i, commentator, q_i, token_similarity, semantic_similarity = row
                verse_ref = get_verse_ref(book, chapter, verse)
                
                if verse_ref not in similarity_scores:
                    similarity_scores[verse_ref] = {}

                if commentator not in similarity_scores[verse_ref]:
                    similarity_scores[verse_ref][commentator] = []    

                similarity_scores[verse_ref][commentator].append(2 * float(semantic_similarity) + float(token_similarity))

        overall_similarity_scores = {}
        for verse_ref in similarity_scores:
            tier1 = []
            tier2 = []
            tier3 = []

            quote_availability_score = 0

            for commentator in similarity_scores[verse_ref]:
                scores = similarity_scores[verse_ref][commentator]
                score = self.avg(scores)

                if commentator in ("Henry Alford", "Jamieson-Fausset-Brown", "Marvin Vincent", "Archibald T. Robertson"):
                    tier1.append(score)
                    quote_availability_score += 3
                elif commentator in ("Albert Barnes", "Philip Schaff"):
                    tier2.append(score)
                    quote_availability_score += 2
                elif commentator in ("John Wesley", "John Gill", "John Calvin"):
                    tier3.append(score)
                    quote_availability_score += 1
                else:
                    raise Exception("Uncategorized Commentator.")

            tier_weight = 0
            if tier1:
                tier_weight += 3
            if tier2: 
                tier_weight += 2
            if tier3:
                tier_weight += 1

            overall_score = (self.avg(tier1) * 3 + self.avg(tier2) * 2 + self.avg(tier3)) 
            if tier_weight != 0:
                overall_score /= tier_weight

            overall_similarity_scores[verse_ref] = (overall_score, quote_availability_score / 19, avg(tier1), avg(tier2), avg(tier3))

        return overall_similarity_scores




    def check_bht_contents(self, folder_to_check, verses, output_filename):
        output_file = open(output_filename, 'w', encoding="utf-8")
        output_file.write("# Issues Found:\n\n")

        corrupted_verses = set()
        missing_commentator_count = 0
        phantom_commentator_count = 0
        misquoted_commentator_count = 0
        low_proportion_bht_count = 0
        verse_i = 0
        similarity_scores = {}
        choicest_quotes_scores = {}
        readability_scores = {}

        for verse_ref in verses:
            book, chapter, verse = get_book_chapter_verse(verse_ref)
            verse_i += 1
            print(f"\r{verse_i} / {len(verses)} {get_verse_ref(book, chapter, verse)} {' ' * 10}", end="")
            bht_content = self.get_bht_content(folder_to_check, book, chapter, verse)
            bht = self.parse_bht(bht_content)
            choicest_quotes = self.parse_choicest_quotes(bht_content)
            missing_commentators, phantom_commentators = self.check_commentators(bht_content, book, chapter, verse, COMMENTATORS_SET)

            for missing_commentator in missing_commentators:
                output_file.write(f"## {missing_commentator} for {book} {chapter}:{verse} has commentary but is missing!\n\n")
                missing_commentator_count += 1

            for phantom_commentator in phantom_commentators:
                output_file.write(f"## {phantom_commentator} for {book} {chapter}:{verse} has no commentary but was quoted!\n\n")
                phantom_commentator_count += 1

            corrupted_quotes = self.get_corrupted_commentator_quotes(bht_content, book, chapter, verse, choicest_quotes)
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

            proportion = self.get_bht_tokens_proportion(bht, choicest_quotes)
            if proportion < 0.5:
                output_file.write(f"## {verse_ref} BHT uses only {proportion} of words from quotes.\n")
                output_file.write(f"BHT:\n{bht}\n")
                corrupted_verses.add(get_verse_ref(book, chapter, verse))
                low_proportion_bht_count += 1

            # choicest_quotes_scores[verse_ref] = compute_similarity(bht, choicest_quotes)
            
            readability_scores[verse_ref] = [
                calculate_flesch_kincaid_ease(bht),
                calculate_flesch_kincaid_grade(bht),
                calculate_automated_readability_index(bht),
                calculate_gunning_fog(bht),
                calculate_dale_chall_readability(bht)
            ]

        similarity_scores = self.get_similarity_scores()

        result_text = f"""
    # Summary:
    {len(verses)} verses checked.
    Missing Commentator Count: {missing_commentator_count} (How many commentaries should have quotes but they're missing?)
    Phantom Commentator Count: {phantom_commentator_count} (How many commentaries have quotes but there's no commentary?)
    Misquoted Commentator Count: {misquoted_commentator_count} (How many commentaries have quotes with chatGPT injected opinions?)
    Low Proportion BHT Count: {low_proportion_bht_count} (How many BHTs use <50% words from quotes?)
    Corrupted Verses Count: {len(corrupted_verses)} (All verses with any of the issues above.)

    """
        
        output_file.write(result_text)

        # output_file.write("## Similarity Scores (Legacy):\n")
        # output_file.write("Verse Ref|Similarity Score\n")
        # for a in sorted(similarity_scores.items(), key=lambda x: x[0]):
        #     verse_ref, score = a
        #     output_file.write(f'{verse_ref}|{score}\n')

        output_file.write("## Similarity Scores:\n")
        output_file.write("Book|Chapter|Verse|VerseID|Similarity Score|Quote Availability Score|tier1|tier2|tier3\n")
        for a in sorted(similarity_scores.items(), key=lambda x: x[0]):
            book, chapter, verse = get_book_chapter_verse(a[0])
            sim_score, avail_score, t1, t2, t3 = a[1]
            output_file.write(f'{book}|{chapter}|{verse}|{book} {chapter}:{verse}|{sim_score}|{avail_score}|{t1}|{t2}|{t3}\n')

        # output_file.write("## Choicest Quotes Scores:\n")
        # output_file.write("Book|Chapter|Verse|BHT Sentence Number|Commentator|Quote Number|Token Similarity|Semantic Similarity\n")
        # for verse_ref, quotes_scores in choicest_quotes_scores.items():
        #     for quote_score in quotes_scores:
        #         i, commentator, j, token_simlarity, semantic_similarity = quote_score
        #         book, chapter, verse = get_book_chapter_verse(verse_ref)
        #         output_file.write(f"{book}|{chapter}|{verse}|{i}|{commentator}|{j}|{token_simlarity}|{semantic_similarity}\n")

        # output_file.write("## Readability Scores:\n")
        # output_file.write("Book|Chapter|Verse|Flesch Kincaid Ease|Flesch Kincaid Grade|Automated Readability Index|Gunning Fog|Dale Chall Readability\n")
        # for verse_ref in readability_scores:
        #     book, chapter, verse = get_book_chapter_verse(verse_ref)
        #     fke, fkg, ari, gf, dcr = readability_scores[verse_ref]
        #     output_file.write(f"{book}|{chapter}|{verse}|{fke}|{fkg}|{ari}|{gf}|{dcr}\n")



        output_file.close()

        print(result_text)

        return corrupted_verses