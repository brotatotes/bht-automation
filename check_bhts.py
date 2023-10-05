from bht_analysis import *

CHOICEST_PROMPT = "choicest prompt v2"
BHT_PROMPT = "bht prompt v5"

# folder_to_check = "bht gen 1"
# folder_to_check = "bht gen 2"
folder_to_check = f"gpt output/bht/{CHOICEST_PROMPT} X {BHT_PROMPT}"
output_filename = f'check_bhts {folder_to_check}.md'

verses_to_check = get_verses_to_check(folder_to_check)

while verses_to_check:
    corrupted_verses = check_bht_contents(folder_to_check, verses_to_check, output_filename)

    if corrupted_verses:
        print(corrupted_verses)
        print(f"Could retry {len(corrupted_verses)} corrupted verses.")
        generate_bhts(corrupted_verses, [CHOICEST_PROMPT], [BHT_PROMPT], COMMENTATORS, redo_choicest=True, redo_bht=True)

    verses_to_check = corrupted_verses