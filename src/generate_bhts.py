from bht.bht_generation import BHTGenerator
from bht.bht_common import COMMENTATORS, BOOKS
import time
from bibleref import BibleRange

if __name__ == '__main__':
    verses = []
    for book in [BibleRange(b) for b in [
        # "Matthew",
        # "Mark",
        "Luke",
        # "John",
        "Acts",
        "Romans",
        "1 Corinthians",
        "2 Corinthians",
        "Galatians",
        "Ephesians",
        "Philippians",
        "Colossians",
        "1 Thessalonians",
        "2 Thessalonians",
        # "1 Timothy",
        # "2 Timothy",
        "Titus",
        "Philemon",
        # "Hebrews",
        # "James",
        "1 Peter",
        "2 Peter",
        "1 John",
        "2 John",
        "3 John",
        "Jude",
        # "Revelation",
        ]]:
        for verse in book:
            verses.append(verse)

    # User Test
    # verses = ["1 Corinthians 11:14", "1 John 4:11", "James 2:8", "Romans 12:3", "1 Corinthians 8:12", "Galatians 1:19", "Acts 16:33", "Colossians 2:12", "1 Corinthians 10:3", "1 Corinthians 11:20", "Acts 8:12", "John 4:5", "Luke 17:17", "Hebrews 5:5", "Romans 10:4", "Revelation 1:12", "Luke 16:21", "Luke 6:35", "Mark 14:48",]

    bht_generator = BHTGenerator()

    bht_generator.generate_bhts(verses, ["choicest prompt v0.4"], ["bht prompt v0.8"], COMMENTATORS, redo_choicest=False, redo_bht=False, debug=False)