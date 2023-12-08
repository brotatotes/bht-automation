from bht.bht_analysis import BHTAnalyzer
from bht.bht_common import get_verses_from_folder
from bht.bht_semantics import NLP, nltk
from bht.bht import Footnotes, BHTWithFootnotes, BHTVersion, ChoicestQuotesForVerse
import json
import time

# retroactively generate all JSONs for gen 2. 
# JSON needs to be incorporated in future generations as part of the pipeline. 
# Then this script should be deleted

if __name__ == '__main__':
    
    start_time = time.time()

    bht_folder = "bht gen 2"

    verses_to_check = get_verses_from_folder(bht_folder)

    bht_analyzer = BHTAnalyzer()    

    footnotes_by_verse = {}

    all_bht_objs = []

    for i, verse_ref in enumerate(verses_to_check):
        print(f"{i}/{len(verses_to_check)} {verse_ref}")
        bht, quotes = bht_analyzer.get_bht_and_quotes(bht_folder, verse_ref)
        footnotes_obj = Footnotes(verse_ref, bht_analyzer.get_footnotes(verse_ref, bht, quotes))
        quotes_obj = ChoicestQuotesForVerse(verse_ref, quotes)
        bht_obj = BHTWithFootnotes(verse_ref, bht, quotes_obj, footnotes_obj)
        all_bht_objs.append(bht_obj)

        for bht_sentence_index in footnotes_obj.footnotes:
            print(f"BHT Sentence: {bht_sentence_index}")
            for footnote in footnotes_obj.footnotes[bht_sentence_index]:
                print(f"\t{footnote.to_json()}")

        footnotes_by_verse[verse_ref] = footnotes_obj

    bht_gen = BHTVersion(float(bht_folder.split()[-1]), all_bht_objs)

    with open(f'scripts output/footnotes-{bht_folder}.json', 'w') as f:
        f.write(bht_gen.to_json())

        
    print(f"That took {round((time.time() - start_time)/60, 2)} minutes")