import re
from gensim.utils import tokenize
import json


class BHT:
    def __init__(self, bht_text, choicest_quotes):
        self.bht = bht_text
        self.bht = self.bht.replace("\"", "") # Remove quotation marks.

        self.choicest_quotes = choicest_quotes
        
        self.tokens = list(tokenize(self.bht.lower()))
        self.tokens_set = set(self.tokens)
        self.word_count = len(self.tokens)
        self.checked = False

    def run_generation_time_checks(self, stop_words_set, word_limits, proportion_limits, strict_word_limits, strict_proportion_limits, target_word_count, target_proportion):
        if self.checked:
            return
        
        self.choicests_tokens_set = set()
        for choicest in self.choicest_quotes.values():
            self.choicests_tokens_set |= set(tokenize(choicest.lower()))
        
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

        excluded_words_set = set(["commentator", "commentators", "verse"])

        self.commentator_in_tokens = "commentator" in self.tokens_set or "commentators" in self.tokens_set or "commentary" in self.tokens_set
        self.verse_in_tokens = "verse" in self.tokens_set
        self.excluded_word_in_tokens = len(self.tokens_set | excluded_words_set) > 0
        self.list_detected = re.search(r'(^|\n)\d[\.)] .*', self.bht)

        self.injected_words = sorted(list(self.tokens_set - self.choicests_tokens_set))
        self.injected_significant_words = sorted(list(self.tokens_set - self.choicests_tokens_set - stop_words_set))

        self.checked = True

    def get_generation_time_checks(self):
        return [
            self.too_many_words,
            self.not_enough_words,
            self.not_enough_from_quotes,
            self.too_much_from_quotes,
            self.excluded_word_in_tokens,
            self.list_detected,
        ]

    def get_score_tuple(self):
        return (
            not self.list_detected,
            not self.too_much_from_quotes,
            not self.excluded_word_in_tokens,
            not self.not_enough_words,
            not self.too_many_words,
            not self.not_enough_from_quotes,
            not self.outside_strict_word_limits, 
            not self.outside_strict_proportion_limits,
            self.content_score
        )

    def passes_checks(self):
        return not any(self.get_generation_time_checks())
    
    # Define custom comparison methods
    def __lt__(self, other):
        return not self.__ge__(self, other)

    def __le__(self, other):
        return not self.__gt__(self, other)

    def __eq__(self, other):
        if other == None:
            return False

        return self.get_score_tuple() == other.get_score_tuple()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        if other == None:
            return True
        
        return self.get_score_tuple() > other.get_score_tuple()
    

    def __ge__(self, other):
        return self.__gt__(self, other) or self.__eq__(self, other)
    

    def get_json(self):
        return json.dumps({
            "bht": self.bht,
            "quotes": self.choicest_quotes
        })
