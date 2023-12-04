import re
import string
from gensim.utils import tokenize
from bht.bht_common import *
from bht.bht_semantics import BHTSemantics
from bht.bht_readability import calculate_flesch_kincaid_ease, calculate_flesch_kincaid_grade, calculate_automated_readability_index, calculate_dale_chall_readability, calculate_gunning_fog

from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

import requests

LEMMATIZER = WordNetLemmatizer()
LEMMATIZER.lemmatize("init")

# TODO: Make this class make sense.
class BHTAnalyzer:
    def __init__(self):
        self.bht_semantics = BHTSemantics()

    def get_bht_content(self, folder_to_check, book, chapter, verse):
        return open(f"{folder_to_check}/{book}/Chapter {chapter}/{book} {chapter} {verse} bht.md", 'r', encoding="utf-8").read()
    
    def get_bht_and_quotes(self, bht_folder, verse_ref):
        book, chapter, verse = get_book_chapter_verse(verse_ref)
        bht_content = self.get_bht_content(bht_folder, book, chapter, verse)
        bht = self.parse_bht(bht_content)
        quotes = self.parse_choicest_quotes(bht_content)

        return bht, quotes

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

    def get_commentators_and_commentary(self, book, chapter, verse, all_commentators):
        commentaries = {}
        for commentator in all_commentators:
            commentary = get_commentary(commentator, get_verse_ref(book, chapter, verse))
            if commentary:
                commentaries[commentator] = commentary

        return commentaries


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
            quote = quote.strip()

            if not quote:
                continue

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

        tokens_not_from_quotes = bht_tokens_set - quotes_tokens_set - self.bht_semantics.get_stop_words()
        proportion = 1 - len(tokens_not_from_quotes) / len(bht_tokens_set)

        return proportion

    # def get_overall_semantic_similarity(bht, choicest_quotes):
    #     return calculate_similarity_sklearn(bht, '\n\n'.join('\n'.join(l) for l in choicest_quotes.values()))


    def get_stop_words(self):
        return set([line.strip() for line in open('src/stopwords.txt', 'r')])

    def tokenize_using_lemmatization(self, text):
        translator = str.maketrans('', '', string.punctuation)
        words = word_tokenize(text.lower().translate(translator))
        return set([LEMMATIZER.lemmatize(word) for word in words])

    def compute_token_similarity(self, text1, text2):
        stop_words = self.get_stop_words()
        tokens1 = self.tokenize_using_lemmatization(text1) - stop_words
        tokens2 = self.tokenize_using_lemmatization(text2) - stop_words

        if len(tokens1) + len(tokens2) == 0:
            return 0

        similarity = len(tokens1 & tokens2) / len(tokens1 | tokens2)
        
        return similarity

    def compute_semantic_similarity(self, text1, text2):
        return self.bht_semantics.calculate_similarity_tensorflow(text1, text2)

    def compute_combined_similarity(self, text1, text2):
        text1, text2 = str(text1), str(text2)
        token_similarity = self.compute_token_similarity(text1, text2)
        semantic_similarity = self.compute_semantic_similarity(text1, text2)

        return token_similarity * 0.5 + semantic_similarity * 0.5
    
    def aggregate_quality_score(self, similarity_scores):
        tier1 = []
        tier2 = []
        tier3 = []

        quote_availability_score = 0

        for commentator in similarity_scores:
            scores = similarity_scores[commentator]
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
            
        quote_availability_score /= 19

        tier_weight = 0
        if tier1:
            tier_weight += 3
        if tier2: 
            tier_weight += 2
        if tier3:
            tier_weight += 1

        t1_avg = self.avg(tier1)
        t2_avg = self.avg(tier2)
        t3_avg = self.avg(tier3)

        final_sim_score = (t1_avg * 3 + t2_avg * 2 + t3_avg)
        if tier_weight != 0:
            final_sim_score /= tier_weight

        return final_sim_score, quote_availability_score, t1_avg, t2_avg, t3_avg
    
    
    def compute_quality_score(self, verse_ref, bht, choicest_quotes):
        aggregated_sim_scores_by_commentator = {}

        sim_scores = self.compute_similarity_scores(verse_ref, bht, choicest_quotes)
        for bht_sentence, commentator, quote_number, token_similarity, semantic_similarity in sim_scores:
            if commentator not in aggregated_sim_scores_by_commentator:
                aggregated_sim_scores_by_commentator[commentator] = []

            aggregated_sim_scores_by_commentator[commentator].append(2 * float(semantic_similarity) + float(token_similarity))

        final_sim_score, quote_availability_score, t1_avg, t2_avg, t3_avg = self.aggregate_quality_score(aggregated_sim_scores_by_commentator)

        return 2 * final_sim_score + quote_availability_score, t1_avg, t2_avg, t3_avg
    

    # Based on V2 scores. Comparable to V2 Normalized scores.
    def normalize_quality_score(self, q_score):
        low = 0.2602646291
        high = 3.268045236

        return 100 * (q_score - low) / (high - low)
    
    def get_footnotes(self, verse_ref, bht, choicest_quotes, top_n = 30):
        similarity_scores = self.compute_similarity_scores(verse_ref, bht, choicest_quotes)
        footnotes = {}
        quote_locations = {}

        book, chapter, verse = get_book_chapter_verse(verse_ref)
        commentaries = self.get_commentators_and_commentary(book, chapter, verse, COMMENTATORS_SET)

        for bht_sentence_index, commentator, quote_number, token_sim, semantic_sim in similarity_scores:
            score = 2 * semantic_sim + token_sim
            if score >= 1:
                if bht_sentence_index not in footnotes:
                    footnotes[bht_sentence_index] = []

                commentary = commentaries[commentator]
                quote = choicest_quotes[commentator][quote_number-1]
                if (commentator, quote_number) not in quote_locations:
                    quote_locations[(commentator, quote_number)] = self.find_quote_in_commentary(quote, commentary)

                location = quote_locations[(commentator, quote_number)]
                footnotes[bht_sentence_index].append((commentator, quote_number, score, location))

        for key, footnote_list in footnotes.items():
            # Sort footnotes from best to worst by bht sentence and only include the `top_n` best.
            footnotes[key] = sorted(footnote_list, key=lambda o: -o[2])[:top_n]

        return footnotes

    # existing bug: If there are word insertions / deletions in either quotes 
    # or commentary and they differ in that way, quote will not be able to be found.
    # Example: 1 Peter 1:2 JFB Quote 3. Result: -1.
    def find_quote_in_commentary(self, quote, commentary):
        commentary = commentary.lower()
        quote_tokens = list(tokenize(quote.lower()))
        commentary_untagged = re.sub(r'<.*?>', ' ', commentary)
        commentary_tokens = list(tokenize(commentary_untagged))
        tokenized_commentary_string = ' '.join(commentary_tokens)        
        # print(tokenized_commentary_string)
        # print(quote_tokens)

        q = 0 # quote tokens index
        t = quote_tokens[q].lower().strip()
        c = tokenized_commentary_string.count(t)
        last_start = 0
        while c != 1:
            # print(last_start, q, t, c)

            q += 1

            if c < 1 or q >= len(quote_tokens):
                last_start += 1

                if last_start >= len(quote_tokens):
                    return -1

                q = last_start
                t = quote_tokens[q].lower().strip()
            elif c > 1:
                t += ' ' + quote_tokens[q].lower().strip()

            c = tokenized_commentary_string.count(t)

        loc_in_tokenized_commentary_string = tokenized_commentary_string.find(t)
        
        # Need to build mapping between tokenized string and original commentary to know where original location is
        index_in_tokenized_string = 0
        index_in_original = 0
        for i, c_token in enumerate(commentary_tokens):
            loc_in_tokenized_string = tokenized_commentary_string.find(c_token, index_in_tokenized_string)
            index_in_tokenized_string = loc_in_tokenized_string + len(c_token)

            loc_in_original = commentary.find(c_token, index_in_original)
            index_in_original = loc_in_original + len(c_token)

            if loc_in_tokenized_string == loc_in_tokenized_commentary_string:
                return loc_in_original

        return -1


    # returns list of object: [BHT Sentence Number, Commentator, Choicest Quote Number, Token Similarity, Semantic Similarity]
    def compute_similarity_scores(self, verse_ref, bht, choicest_quotes):
        choicest_quotes_comparisons = []
        # best_scores = []
        for i, bht_sentence in enumerate(self.bht_semantics.get_nlp()(bht).sents):        
            # best_score = 0
            for commentator in choicest_quotes:
                for j, quote in enumerate(choicest_quotes[commentator]):
                    if not quote:
                        continue
                    
                    bht_sentence, quote = str(bht_sentence), str(quote)
                    semantic_similarity = self.compute_semantic_similarity(bht_sentence, quote)
                    token_similarity = self.compute_token_similarity(bht_sentence, quote)
                    # score = token_similarity * 0.2 + semantic_similarity * 0.8
                    # if score > best_score:
                    #     best_score = score

                    # print(verse_ref, i, j, semantic_similarity, token_similarity)

                    choicest_quotes_comparisons.append((i + 1, commentator, j + 1, token_similarity, semantic_similarity))
            
            # best_scores.append(best_score)


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
            overall_similarity_scores[verse_ref] = self.aggregate_quality_score(similarity_scores[verse_ref])

        return overall_similarity_scores


    def post(self, json_data):
        response = requests.post('https://bible-go-internal.vercel.app/api/commentaries', json=json_data)
        if response.status_code == 200:
            return True
        else:
            print(f'POST request failed with status code {response.status_code}')
            return False
        
        
    def generate_json_data(self, folder_name, book, chapter, verse, bht, commentaries):
        json_data = {
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "bht": bht,
            "bhtUpdateDescription": folder_name
        }

        for commentator, commentary in commentaries.items():
            json_data[get_commentatory_shorthand_name(commentator)] = commentary

        return json_data
    

    def post_all_commentary_json(self, folder_name):
        verses = get_verses_from_folder(folder_name)

        for i, verse_ref in enumerate(verses):
            book, chapter, verse = get_book_chapter_verse(verse_ref)
            bht_content = self.get_bht_content(folder_name, book, chapter, verse)
            bht = self.parse_bht(bht_content)
            commentaries = self.get_commentators_and_commentary(book, chapter, verse, COMMENTATORS_SET)

            json_data = self.generate_json_data(folder_name, book, chapter, verse, bht, commentaries)

            succeeded = self.post(json_data)

            if not succeeded:
                input("Something failed. Take a look!")

            print(f"{i+1} / {len(verses)} {get_verse_ref(book, chapter, verse)} {succeeded}")
    

    def check_bht_contents(self, folder_name, verses, output_filename):
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
            print(f"{verse_i} / {len(verses)} {get_verse_ref(book, chapter, verse)}")
            bht_content = self.get_bht_content(folder_name, book, chapter, verse)
            bht = self.parse_bht(bht_content)
            choicest_quotes = self.parse_choicest_quotes(bht_content)
            missing_commentators, phantom_commentators = self.check_commentators(bht_content, book, chapter, verse, COMMENTATORS_SET)
            commentaries = self.get_commentators_and_commentary(book, chapter, verse, COMMENTATORS_SET)

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

        # similarity_scores = self.get_similarity_scores()

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

        # output_file.write("## Similarity Scores:\n")
        # output_file.write("Book|Chapter|Verse|VerseID|Similarity Score|Quote Availability Score|tier1|tier2|tier3\n")
        # for a in sorted(similarity_scores.items(), key=lambda x: x[0]):
        #     book, chapter, verse = get_book_chapter_verse(a[0])
        #     sim_score, avail_score, t1, t2, t3 = a[1]
        #     output_file.write(f'{book}|{chapter}|{verse}|{book} {chapter}:{verse}|{sim_score}|{avail_score}|{t1}|{t2}|{t3}\n')

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