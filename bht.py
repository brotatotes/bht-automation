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

    def init_checks(self, choicests_tokens_set, stop_words_set, word_limits, proportion_limits):
        if self.checked:
            return

        tokens_not_from_choicests = len(self.tokens_set - choicests_tokens_set - stop_words_set)
        self.proportion = 1 - tokens_not_from_choicests / len(self.tokens_set)
        self.proportion_percentage = round(self.proportion * 100, 2)

        self.min_word_limit, self.max_word_limit = word_limits
        self.min_proportion_limit, self.max_proportion_limit = proportion_limits

        self.too_many_words = self.word_count > self.max_word_limit
        self.not_enough_words = self.word_count < self.min_word_limit
        self.not_enough_from_quotes = self.proportion < self.min_proportion_limit
        self.too_much_from_quotes = self.proportion > self.max_proportion_limit
        self.commentator_in_tokens = "commentator" in self.tokens_set or "commentators" in self.tokens_set

        self.check_results = [self.too_many_words, self.not_enough_words, self.not_enough_from_quotes, self.too_much_from_quotes, self.commentator_in_tokens]

        self.injected_words = sorted(list(self.tokens_set - choicests_tokens_set))
        self.injected_significant_words = sorted(list(self.tokens_set - choicests_tokens_set - stop_words_set))

        self.checked = True


    def passes_checks(self):
        return not any(self.check_results)
    
    # Define custom comparison methods
    def __lt__(self, other):
        return not self.__ge__(self, other)

    def __le__(self, other):
        return not self.__gt__(self, other)

    def __eq__(self, other):
        if other == None:
            return False

        return (
            self.too_much_from_quotes == other.too_much_from_quotes and 
            self.commentator_in_tokens == other.commentator_in_tokens and
            self.proportion == other.proportion and 
            self.not_enough_words == other.not_enough_words and
            self.word_count == other.word_count)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        if other == None:
            return True
        # Order of importance: (
        #   not too much from quotes,
        #   no commentator in text,
        #   enough words,
        #   high proportion,
        #   low word_count)
        a = (
            self.passes_checks(),
            not self.too_much_from_quotes, 
            not self.commentator_in_tokens,
            not self.not_enough_words,
            self.proportion,            
            - self.word_count)
        
        b = (
            other.passes_checks(),
            not other.too_much_from_quotes, 
            not other.commentator_in_tokens,
            not other.not_enough_words,
            other.proportion,            
            - other.word_count)
        
        return a > b
    

    def __ge__(self, other):
        return self.__gt__(self, other) or self.__eq__(self, other)
