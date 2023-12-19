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

    verses = ["1 Corinthians 11:14", "1 John 4:11", "James 2:8", "Romans 12:3", "1 Corinthians 8:12", "Galatians 1:19", "Acts 16:33", "Colossians 2:12", "1 Corinthians 10:3", "1 Corinthians 11:20", "Acts 8:12", "John 4:5", "Luke 17:17", "Hebrews 5:5", "Romans 10:4", "Revelation 1:12", "Luke 16:21", "Luke 6:35", "Mark 14:48",]

    bht_generator = BHTGenerator()

    bht_generator.generate_bhts(verses, ["choicest prompt v0.4"], ["bht prompt v0.7"], COMMENTATORS, redo_bht=True, debug=False)