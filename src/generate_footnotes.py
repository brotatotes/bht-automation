from bht.bht_analysis import BHTAnalyzer
from bht.bht_common import get_verses_from_folder
from bht.bht_semantics import NLP, nltk




if __name__ == '__main__':
    # print(get_clauses("In order to encourage Gaius to continue showing kindness to the same individuals, the apostle highlights how they had spoken highly of his previous acts of love in front of the church."))

    # print(get_clauses("He eats cheese, but he won't eat ice cream"))

    # print(get_clauses("This all encompassing experience wore off for a moment and in that moment, my awareness came gasping to the surface of the hallucination and I was able to consider momentarily that I had killed myself by taking an outrageous dose of an online drug and this was the most pathetic death experience of all time."))


    bht_folder = "bht gen 2"

    verses_to_check = get_verses_from_folder(bht_folder)

    bht_analyzer = BHTAnalyzer()

    for i, verse_ref in enumerate(verses_to_check):
        print(f"{i}/{len(verses_to_check)}")

        print(verse_ref)
        bht, quotes = bht_analyzer.get_bht_and_quotes(bht_folder, verse_ref)
        footnotes = bht_analyzer.get_footnotes(verse_ref, bht, quotes)

        for bht_sentence_index in footnotes:
            print(f"BHT Sentence: {bht_sentence_index}")
            for footnote in footnotes[bht_sentence_index]:
                print(f"\t{footnote}")

