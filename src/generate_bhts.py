from bibleref import BibleRange, BibleVerse
from bht.bht_generation import generate_bhts

commentators = [
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

books = [BibleRange(b) for b in [
        "Matthew",
        "Mark",
        "Luke",
        "John",
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
        "1 Timothy",
        "2 Timothy",
        "Titus",
        "Philemon",
        "Hebrews",
        "James",
        "1 Peter",
        "2 Peter",
        "1 John",
        "2 John",
        "3 John",
        "Jude",
        "Revelation",
        ]]

if __name__ == '__main__':
    verses = []
    for book in books:
        for verse in book:
            verses.append(verse)

    verses = ["Ephesians 1:22", "2 Peter 1:19"]

    # generate_bhts(verses, ["choicest prompt v2", "choicest prompt v3"], ["bht prompt v5"], COMMENTATORS)

    generate_bhts(verses, ["choicest prompt gpt-prompt-engineering"], ["bht prompt gpt-prompt-engineering"], commentators)