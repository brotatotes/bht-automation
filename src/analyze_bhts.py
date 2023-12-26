from bht.bht_analysis import BHTAnalyzer, COMMENTATORS
from bht.bht_common import get_verses_from_folder, get_book_chapter_verse, BOOKS
# from bht.bht_generation import BHTGenerator
import os
import json
import statistics

bht_analyzer = BHTAnalyzer()

v2_md_folder = 'bht gen 2'
v3_json_folder = 'bht gen 3 json'
output_folder = 'scripts output/v2_v3_analysis/'
v2_output_path = f'{output_folder}/v2_json'
v3_output_path = f'{output_folder}/v3_json'
v2_json = {}
v3_json = {}

def get_v2_scores(folder, verse_ref):
    bht, quotes = bht_analyzer.get_bht_and_quotes(folder, verse_ref)

for book in BOOKS:
    for verse_ref in book:
        pass


# CHOICEST_PROMPT = "choicest prompt v0.4"
# BHT_PROMPT = "bht prompt v0.8"

# folder_to_check = "bht gen 1"
# folder_to_check = "gpt output/bht/json/choicest prompt v0.4 X bht prompt v0.8"
# folder_to_check = f"gpt output/bht/{CHOICEST_PROMPT} X {BHT_PROMPT}"
# output_filename = f'scripts output/analyze_bhts {folder_to_check.replace("/", "-")}.md'
# os.makedirs("scripts output", exist_ok=True)

# verses_to_check = get_verses_from_folder(folder_to_check)

# while verses_to_check:
    # bht_analyzer = BHTAnalyzer()
    # bht_generator = BHTGenerator()

    # corrupted_verses = bht_analyzer.check_bht_contents(folder_to_check, verses_to_check, output_filename)

    # if corrupted_verses:
    #     print(corrupted_verses)
    #     print(f"Could retry {len(corrupted_verses)} corrupted verses.")
    #     bht_generator.generate_bhts(corrupted_verses, [CHOICEST_PROMPT], [BHT_PROMPT], COMMENTATORS, redo_choicest=True, redo_bht=True)

    # verses_to_check = corrupted_verses

# scores = {}

# for verse_ref in verses_to_check:
#     book, chapter, verse = get_book_chapter_verse(verse_ref)
#     json_file_name = f'{folder_to_check}/{book}/Chapter {chapter}/{book} {chapter} {verse} bht.json'
#     json_data = json.load(open(json_file_name))
#     accuracy_score = json_data["bestBHT"]["qualityScore"]
    
#     scores[verse_ref] = accuracy_score

# john_scores = [v for k, v in scores.items() if k.startswith("Mark")]

# print(statistics.mean(scores.values()))
# print(statistics.median(scores.values()))

# print(statistics.mean(john_scores))
# for verse_ref in ["John 9:9", "John 4:8", "John 12:17", "John 16:17", "John 3:16", "John 18:4", "John 9:33", "John 13:27", "John 7:22"]:
#     print(verse_ref, scores[verse_ref])

