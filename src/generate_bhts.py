from bht.bht_generation import BHTGenerator
from bht.bht_common import COMMENTATORS, BOOKS
import time
from bibleref import BibleRange

if __name__ == '__main__':
    verses = []
    for book in BOOKS:
        for verse in book:
            verses.append(verse)

    verses =  ["Romans 6:7", "John 5:22", "Ephesians 1:22", "Ephesians 6:13", "Galatians 5:22", "John 10:27", "Romans 6:21", "Revelation 3:3"]

    # verses = ["Romans 6:7", "Ephesians 1:22", "Romans 6:21"]

    # verses = ["2 Corinthians 5:4", "Mark 4:5"]

    # verses = [str(v) for v in BibleRange("Romans 8")]

    verses = ["Luke 10:42"]

    bht_generator = BHTGenerator()

    bht_generator.generate_bhts(verses, ["choicest prompt v0.4"], ["bht prompt v0.7"], COMMENTATORS, redo_bht=True, debug=False)