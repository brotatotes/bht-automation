from bht.bht_analysis import BHTAnalyzer, COMMENTATORS
from bht.bht_common import get_verses_from_folder
from bht.bht_generation import BHTGenerator
import os

CHOICEST_PROMPT = "choicest prompt v2"
BHT_PROMPT = "bht prompt v5"

# folder_to_check = "bht gen 1"
folder_to_check = "bht gen 2"
# folder_to_check = f"gpt output/bht/{CHOICEST_PROMPT} X {BHT_PROMPT}"
output_filename = f'scripts output/analyze_bhts {folder_to_check.replace("/", "-")}.md'
os.makedirs("scripts output", exist_ok=True)

verses_to_check = get_verses_from_folder(folder_to_check)

while verses_to_check:
    bht_analyzer = BHTAnalyzer()
    bht_generator = BHTGenerator()
    corrupted_verses = bht_analyzer.check_bht_contents(folder_to_check, verses_to_check, output_filename)

    if corrupted_verses:
        print(corrupted_verses)
        print(f"Could retry {len(corrupted_verses)} corrupted verses.")
        bht_generator.generate_bhts(corrupted_verses, [CHOICEST_PROMPT], [BHT_PROMPT], COMMENTATORS, redo_choicest=True, redo_bht=True)

    verses_to_check = corrupted_verses