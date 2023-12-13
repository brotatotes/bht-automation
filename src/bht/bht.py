import re
from gensim.utils import tokenize
import json
from bht.bht_analysis import BHTAnalyzer
from bht.bht_common import get_book_chapter_verse, get_commentatory_shorthand_name
from bht.bht_semantics import NLP

class BHTGeneration:
    def __init__(self, timestamp_string, bht, choicest_prompt_version, bht_prompt_version, commentators, bht_attempts, attempts_limit):
        self.timestamp_string = timestamp_string
        self.bht = bht
        self.choicest_prompt_version = choicest_prompt_version
        self.bht_prompt_version = bht_prompt_version
        self.commentators = commentators
        self.bht_attempts = bht_attempts
        self.attempts_limit = attempts_limit

    def to_json(self):
        data = {
            "timestamp": self.timestamp_string,
            "verseRef": self.bht.verse_ref,
            "bestBHT": eval(self.bht.to_json()),
            "choicestQuotes": self.bht.choicest_quotes,
            "choicestPrompt": self.choicest_prompt_version,
            "bhtPrompt": self.bht_prompt_version,
            "commentators": self.commentators,
            "bhtAttemptsLimit": self.attempts_limit,
            "bhtAttemptsCount": len(self.bht_attempts),
            "bhtAttempts": [eval(b.to_json()) for b in self.bht_attempts],
        }

        return json.dumps(data, indent=4)

class BHT:
    def __init__(self, verse_ref, bht_text, choicest_quotes, generation_attempt = -1):
        self.verse_ref = str(verse_ref)

        self.bht = bht_text
        self.bht = self.bht.replace("\"", "") # Remove quotation marks.

        self.choicest_quotes = choicest_quotes
        self.generation_attempt = generation_attempt
        
        self.tokens = list(tokenize(self.bht.lower()))
        self.tokens_set = set(self.tokens)
        self.word_count = len(self.tokens)

        self.bht_analyzer = BHTAnalyzer()
        self.quality_score = None

        self.checked = False

        # self.footnotes = self.bht_analyzer.get_footnotes(self.verse_ref, self.bht, self.choicest_quotes)


    def run_generation_time_checks(self, stop_words_set, word_limits, proportion_limits, strict_word_limits, strict_proportion_limits, target_word_count, target_proportion):
        if self.checked:
            return
        
        self.choicests_tokens_set = set()
        for quotes in self.choicest_quotes.values():
            self.choicests_tokens_set |= set(map(lambda t: tokenize(t.lower()), quotes))
        
        self.target_word_count = target_word_count
        self.target_proportion = target_proportion

        tokens_not_from_choicests = len(self.tokens_set - self.choicests_tokens_set - stop_words_set)
        self.proportion = 1 - tokens_not_from_choicests / len(self.tokens_set)
        self.proportion_percentage = round(self.proportion * 100, 2)

        self.min_word_limit, self.max_word_limit = word_limits
        self.min_proportion_limit, self.max_proportion_limit = proportion_limits
        self.min_strict_word_limit, self.max_strict_word_limit = strict_word_limits
        self.min_strict_proportion_limit, self.max_strict_proportion_limit = strict_proportion_limits

        self.outside_strict_word_limits = self.word_count < self.min_strict_word_limit or self.word_count > self.max_strict_word_limit
        self.outside_strict_proportion_limits = self.proportion < self.min_strict_proportion_limit or self.proportion > self.max_strict_proportion_limit

        self.content_score = 100 - abs(self.word_count - self.target_word_count) - 100 * abs(self.proportion - self.target_proportion)

        self.too_many_words = self.word_count > self.max_word_limit
        self.not_enough_words = self.word_count < self.min_word_limit
        self.not_enough_from_quotes = self.proportion < self.min_proportion_limit
        self.too_much_from_quotes = self.proportion > self.max_proportion_limit

        excluded_words_set = set(["commentator", "commentators", "verse", "passage"])

        self.commentator_in_tokens = "commentator" in self.tokens_set or "commentators" in self.tokens_set or "commentary" in self.tokens_set or "commentaries" in self.tokens_set
        self.verse_in_tokens = "verse" in self.tokens_set
        self.verse_ref_in_bht = self.verse_ref in self.bht or (get_book_chapter_verse(self.verse_ref)[0]) in self.bht
        self.passage_in_tokens = "passage" in self.tokens_set
        self.excluded_word_in_tokens = len(self.tokens_set | excluded_words_set) > 0
        self.list_detected = re.search(r'(^|\n)\d[\.)] .*', self.bht)

        self.injected_words = sorted(list(self.tokens_set - self.choicests_tokens_set))
        self.injected_significant_words = sorted(list(self.tokens_set - self.choicests_tokens_set - stop_words_set))

        self.quality_score, self.t1_avg, self.t2_avg, self.t3_avg = self.bht_analyzer.compute_quality_score(self.verse_ref, self.bht, self.choicest_quotes)

        self.v2_normalized_quality_score = round(self.bht_analyzer.normalize_quality_score(self.quality_score), 2)

        tier_total = self.t1_avg + self.t2_avg + self.t3_avg
        self.t1_percent = round(100 * self.t1_avg / tier_total, 2)
        self.t2_percent = round(100 * self.t2_avg / tier_total, 2)
        self.t3_percent = round(100 * self.t3_avg / tier_total, 2)

        if self.t1_avg > self.t2_avg and self.t1_avg > self.t3_avg:
            self.max_commentator_tier = 1
        elif self.t2_avg > self.t1_avg and self.t2_avg > self.t3_avg:
            self.max_commentator_tier = 2
        else:
            self.max_commentator_tier = 3

        self.checked = True

    def get_generation_time_checks(self):
        return [
            self.outside_strict_word_limits,
            self.not_enough_words,
            # self.not_enough_from_quotes,
            self.too_much_from_quotes,
            # self.excluded_word_in_tokens,
            self.commentator_in_tokens,
            self.verse_ref_in_bht,
            self.verse_in_tokens,
            self.passage_in_tokens,
            self.list_detected,
        ]
    
    def get_score(self):
        return self.get_score_tuple()

    def get_score_tuple(self):
        return (
            not self.list_detected,            
            # not self.excluded_word_in_tokens,
            not self.commentator_in_tokens,
            not self.passage_in_tokens, 
            not self.verse_ref_in_bht,
            not self.verse_in_tokens,
            not self.too_much_from_quotes,
            not self.outside_strict_word_limits, 
            not self.outside_strict_proportion_limits,
            # not self.not_enough_words,
            # not self.too_many_words,
            # not self.not_enough_from_quotes,
            # self.content_score
            self.quality_score,
        )

    def passes_checks(self):
        return not any(self.get_generation_time_checks()) and self.quality_score >= 2
    
    def generate_footnotes(self):
        self.footnotes = self.bht_analyzer.get_footnotes(self.verse_ref, self.bht, self.choicest_quotes)
    
    # Define custom comparison methods
    def __lt__(self, other):
        return not self.__ge__(self, other)

    def __le__(self, other):
        return not self.__gt__(self, other)

    def __eq__(self, other):
        if other == None:
            return False

        return self.get_score() == other.get_score()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        if other == None:
            return True
        
        return self.get_score() > other.get_score()
    

    def __ge__(self, other):
        return self.__gt__(self, other) or self.__eq__(self, other)
    

    def to_json(self):
        return json.dumps({
            "bht": self.bht,
            "wordCount": self.word_count,
            "quoteTokenProportion": self.proportion_percentage,
            "qualityScore": self.quality_score,
            "qualityScoreNormalizedComparedToV2BHTs": self.v2_normalized_quality_score,
            "commentatorTierSimilarities": [self.t1_percent, self.t2_percent, self.t3_percent],
            "generationAttempt": self.generation_attempt,
            # "injectedWords": self.injected_words,
            # "injectedSignificantWords": self.injected_significant_words
        }, indent=4)


class BHTVersion:
    def __init__(self, version_number, all_bht_objects):
        self.version_number = version_number # int
        self.all_bht_objects = all_bht_objects # list of BHTWithFootnotes

    def to_json(self):
        data = {
            "bhtGenVersion": self.version_number,
            "bhts": [eval(bht.to_json()) for bht in self.all_bht_objects]
        }

        return json.dumps(data, indent=4)


class BHTWithFootnotes:
    def __init__(self, verse_ref, bht, choicest_quotes, footnotes):
        self.verse_ref = verse_ref # string
        self.book, self.chapter, self.verse_number = get_book_chapter_verse(verse_ref)
        self.bht_sentences = [s.text.strip() for s in NLP(bht).sents]
        self.choicest_quotes = choicest_quotes # ChoicestQuotesForVerse
        self.footnotes = footnotes # Footnotes

    def to_json(self):
        data = {
            "book": self.book,
            "chapter": self.chapter,
            "verseNumber": self.verse_number,
            "bhtSentences": self.bht_sentences,
            "quotes": eval(self.choicest_quotes.to_json()),
            "footnotes": eval(self.footnotes.to_json())
        }

        return json.dumps(data, indent=4)


class Footnotes:
    def __init__(self, verse_ref, footnotes):
        self.verse_ref = verse_ref

        self.footnotes = {}
        for bht_sentence_number, fnotes in footnotes.items():
            self.footnotes[bht_sentence_number] = []
            for fnote in fnotes:
                commentator, quote_number, score, location = fnote
                self.footnotes[bht_sentence_number].append(Footnote(verse_ref, bht_sentence_number, commentator, quote_number, score, location))
                                

    def to_json(self):
        footnotes = {}
        for k, v in self.footnotes.items():
            footnotes[k] = [eval(f.to_json()) for f in v]

        data = {
            "verseRef": self.verse_ref,
            "footnotes": footnotes,
        }

        return json.dumps(footnotes, indent=4)


class Footnote:
    def __init__(self, verse_ref, bht_sentence_number, commentator, quote_number, similarity_score, location):
        self.verse_ref = verse_ref
        self.bht_sentence_number = bht_sentence_number
        self.commentator = commentator
        self.quote_number = quote_number
        self.similarity_score = similarity_score
        self.location = location

    def to_json(self):
        data = {
            # "bhtSentenceNumber": self.bht_sentence_number,
            "commentator": get_commentatory_shorthand_name(self.commentator),
            "quoteNumber": self.quote_number,
            "similarityScore": self.similarity_score,
            "indexLocation": self.location
        }

        return json.dumps(data, indent=4)


# class ChoicestQuotesFromCommentator:
#     def __init__(self, verse_ref, commentator, choicest_quotes):
#         self.verse_ref = verse_ref
#         self.commentator = commentator
#         self.choicest_quotes = choicest_quotes

#     def to_json(self):
#         data = {
#             # "verseRef": self.verse_ref,
#             "commentator": self.commentator,
#             "quotes": self.choicest_quotes
#         }

#         return json.dumps(data)


class ChoicestQuotesForVerse:
    def __init__(self, verse_ref, choicest_quotes_by_commentator):
        self.verse_ref = verse_ref
        self.choicest_quotes_by_commentator = choicest_quotes_by_commentator
        self.choicest_quotes = {}
        for k, v in self.choicest_quotes_by_commentator.items():
            self.choicest_quotes[get_commentatory_shorthand_name(k)] = v

    def to_json(self):
        return json.dumps(self.choicest_quotes, indent=4)


if __name__ == '__main__':
    pass
    # q1 = ChoicestQuotesFromCommentator("John 3:16", "Henry Alford", ["1. first quote", "2. second quote.,", "3. third quote"])
    # q2 = ChoicestQuotesFromCommentator("John 3:16", "Albert Barnes", ["1. first quote", "2. second quote.,", "3. third quote"])

    # all_q = ChoicestQuotesForVerse("John 3:16", {"Henry Alford": q1, "Albert Barnes": q2})