import re
from gensim.utils import tokenize

class BHT:
    def __init__(self, text):
        self.text = text
        self.text = self.text.replace("\"", "") # Remove quotation marks.
        # self.text = re.sub(r'^[^a-zA-Z]*', '', self.text) # Remove non-letter characters from beginning.

        self.tokens = list(tokenize(self.text.lower()))
        self.tokens_set = set(self.tokens)
        self.word_count = len(self.tokens)
        self.checked = False

    def init_checks(self, choicests_tokens_set, stop_words_set, word_limits, proportion_limits, strict_word_limits, strict_proportion_limits, target_word_count, target_proportion):
        if self.checked:
            return
        
        self.target_word_count = target_word_count
        self.target_proportion = target_proportion

        tokens_not_from_choicests = len(self.tokens_set - choicests_tokens_set - stop_words_set)
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
        self.commentator_in_tokens = "commentator" in self.tokens_set or "commentators" in self.tokens_set
        self.list_detected = re.search(r'(^|\n)\d[\.)] .*', self.text)

        self.injected_words = sorted(list(self.tokens_set - choicests_tokens_set))
        self.injected_significant_words = sorted(list(self.tokens_set - choicests_tokens_set - stop_words_set))

        self.checked = True

    def check_results(self):
        return [
            self.too_many_words,
            self.not_enough_words,
            self.not_enough_from_quotes,
            self.too_much_from_quotes,
            self.commentator_in_tokens,
            self.list_detected
        ]

    def get_score_tuple(self):
        return (
            not self.list_detected,
            not self.too_much_from_quotes,
            not self.commentator_in_tokens,
            not self.not_enough_words,
            not self.too_many_words,
            not self.not_enough_from_quotes,
            not self.outside_strict_word_limits, 
            not self.outside_strict_proportion_limits,
            self.content_score
        )

    def passes_checks(self):
        return not any(self.check_results())
    
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
