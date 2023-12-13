from bht.bht_semantics import BHTSemantics, NLP
from bht.bht_common import *
import glob
import os


def get_commentary_range_files(commentary_folder, commentator, book, chapter):
    folder = f'{commentary_folder}/{commentator}/{book}/Chapter {chapter}'
    txt_files = glob.glob(os.path.join(folder, '*.txt'))
    range_files = []
    for filepath in txt_files:
        filename = os.path.basename(filepath)
        if '-' in filename:
            range_files.append(filepath)

    return range_files


def get_all_commentary_range_files(commentary_folder, commentators):
    filepaths = []
    for commentator in commentators:
        for book in BOOK_CHAPTERS:
            for chapter in range(1, BOOK_CHAPTERS[book] + 1):
                filepaths.extend(get_commentary_range_files(commentary_folder, commentator, book, chapter))

    return filepaths




def test_luke5_example():
    bht_semantics = BHTSemantics()


    # Luke 5:33-39
    verses = [
        "And they said to Him, “The disciples of John often fast and offer prayers, the disciples of the Pharisees also do [o]the same, but Yours eat and drink.”",
        "And Jesus said to them, “You cannot make the [p]attendants of the bridegroom fast while the bridegroom is with them, can you?",
        "But the days will come; and when the bridegroom is taken away from them, then they will fast in those days.”",
        "And He was also telling them a parable: “No one tears a piece of cloth from a new garment and puts it on an old garment; otherwise he will both tear the new, and the piece from the new will not match the old.",
        "And no one puts new wine into old wineskins; otherwise the new wine will burst the skins and it will be spilled out, and the skins will be ruined.",
        "But new wine must be put into fresh wineskins.",
        "And no one, after drinking old wine wishes for new; for he says, ‘The old is good enough.’”"
    ]

    commentary = "Having drunk old wine ... - Wine increases its strength and flavor, and its mildness and mellowness, by age, and the old is therefore preferable. They who had tasted such mild and mellow wine would not readily drink the comparatively sour and astringent juice of the grape as it came from the press. The meaning of this proverb in this place seems to be this: You Pharisees wish to draw my disciples to the “austere” and “rigid” duties of the ceremonial law - to fasting and painful rites; but they have come under a milder system. They have tasted the gentle and tender blessings of the gospel; they have no “relish” for your stern and harsh requirements. To insist now on their observing them would be like telling a man who had tasted of good, ripe, and mild wine to partake of that which is sour and unpalatable. At the proper time all the sterner duties of religion will be properly regarded; but “at present,” to teach them to fast when they see “no occasion” for it - when they are full of joy at the presence of their Master - would be like putting a piece of new cloth on an old garment, or new wine into old bottles, or drinking unpleasant wine after one had tasted that which was more pleasant. It would be ill-timed, inappropriate, and incongruous."

    commentary_sentences = [str(s) for s in NLP(commentary).sents]

    gpt_selected_quotes = [
        "You Pharisees wish to draw my disciples to the 'austere' and 'rigid' duties of the ceremonial law - to fasting and painful rites; but they have come under a milder system.",
        "They have tasted the gentle and tender blessings of the gospel; they have no 'relish' for your stern and harsh requirements.",
        "At the proper time all the sterner duties of religion will be properly regarded; but 'at present,' to teach them to fast when they see 'no occasion' for it - when they are full of joy at the presence of their Master - would be like putting a piece of new cloth on an old garment, or new wine into old bottles, or drinking unpleasant wine after one had tasted that which was more pleasant."
    ]

    first_verse_number = 33
    for quote in gpt_selected_quotes:
        best_matching_verse = None
        print(f'[Commentary Quote]')
        print(quote)
        print()

        for i, verse in enumerate(verses):
            current_verse_number = first_verse_number + i 
            similarity_score = bht_semantics.calculate_similarity_tensorflow(verse, quote)

            print(f'[Luke 5:{current_verse_number}]')
            print(verse)
            print(f'SIMILARITY SCORE: {similarity_score}')
            print()

            if best_matching_verse == None or similarity_score > best_matching_verse[0]:
                best_matching_verse = (similarity_score, current_verse_number, verse)
        
        best_score, best_v_n, best_verse = best_matching_verse
        print(f'[BEST MATCHING VERSE: {best_score} {best_v_n}]')
        print(best_verse)
        print()
        input()




if __name__ == '__main__':
    # test_luke5_example()
    filepaths = get_all_commentary_range_files(COMMENTARY_FOLDER, COMMENTATORS)
    print(len(filepaths))
    for f in filepaths:
        print(f)