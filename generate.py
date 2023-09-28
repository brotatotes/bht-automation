from bibleref import BibleRange, BibleVerse

from bht_generation import generate_bhts

if __name__ == '__main__':
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
    
    verses = []
    for book in books:
        for verse in book:
            verses.append(verse)

    generate_bhts(verses, ["choicest prompt v2"], ["bht prompt v5"], COMMENTATORS)