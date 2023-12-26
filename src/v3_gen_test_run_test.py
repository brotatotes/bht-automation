import random
import os
import json
import time
from bht.bht_common import *
from bht.bht_analysis import BHTAnalyzer
from bht.bht_generation import BHTGenerator
from bht.multi_threaded_work_queue import MultiThreadedWorkQueue
from bibleref import BibleRange


# params
choicest_prompt = "choicest prompt v0.4"
bht_prompt = "bht prompt v0.8"
REGENERATE_BHTS = False
RECOMPUTE_V2_SCORES = False
n = 200




folder = 'src'
csv = f'{folder}/v2_scores.csv'

def get_score_file(verse_ref, folder):
    book, chapter, verse = get_book_chapter_verse(verse_ref)
    return f'{folder}/{book} {chapter} {verse}.txt'

if RECOMPUTE_V2_SCORES:
    print("Computing quality scores for V2...")
    bht_analyzer = BHTAnalyzer()

    # data = {}
    # with open('src/v2_scores.csv') as f:
    #     for line in f.readlines():
    #         verse_ref, score, t1, t2, t3 = line.split(',')
    #         data[verse_ref] = list(map(float, (score, t1, t2, t3)))
    
    os.makedirs(folder, exist_ok=True)

    def compute_score(verse_ref, folder):
        score, v2t1, v2t2, v2t3 = bht_analyzer.get_score_details('bht gen 2', verse_ref)
        with open(get_score_file(verse_ref, folder), 'w') as f:
            f.write(f'{score},{v2t1},{v2t2},{v2t3}')

    # work_queue = MultiThreadedWorkQueue(num_threads=1000)

    with open(csv, 'w') as f:
        i = 0
        for book in BOOKS:
            for verse_ref in book:
                i += 1
                score, v2t1, v2t2, v2t3 = bht_analyzer.get_score_details('bht gen 2', verse_ref)
                f.write(f'{verse_ref},{score},{v2t1},{v2t2},{v2t3}\n')
                print(f'\r{i}/7957', end='')

    # work_queue.start()
    # work_queue.wait_for_completion()
    # work_queue.stop()

    print("Done.")


print("Reading V2 Scores from file...")

scores = {}
tiers = {}

# for book in BOOKS:
#     for verse_ref in book:                
#         score, v2t1_raw, v2t2_raw, v2t3_raw = map(float, open(get_score_file(verse_ref, folder)).read().strip().split(','))
#         scores[verse_ref] = score
#         tiers[verse_ref] = (v2t1_raw, v2t2_raw, v2t3_raw)   
    
with open(csv) as f:
    for line in f.readlines():
        verse_ref, score, v2t1, v2t2, v2t3 = line.strip().split(',')
        score = float(score)
        v2t1 = float(v2t1)
        v2t2 = float(v2t2)
        v2t3 = float(v2t3)
        scores[verse_ref] = score
        tiers[verse_ref] = (v2t1, v2t2, v2t3)

print("Done.")

print(f"Selecting verses for {n} buckets...")

lowest = min(scores.values())
highest = max(scores.values())

samples = []

score_group_size = (highest - lowest) / n
groups = []
curr_group = lowest
while curr_group < highest:
    group = []
    lower = curr_group
    higher = curr_group + score_group_size
    for verse_ref, score in scores.items():
        if score >= lower and score < higher:
           group.append((verse_ref, score)) 

    groups.append(group)

    curr_group += score_group_size

verses = []
verses_and_scores = []

for group in groups:
    if group:
        verse_ref, score = group[len(group) // 2]
        # verse_ref, score = random.choice(group)
        verses.append(verse_ref)
        verses_and_scores.append((verse_ref, score))

# inject custom test set
# verses = [str(v) for v in BibleRange("Matthew 22:1-14")]
verses = ALL_VERSES
verses_and_scores = [(v, scores[v]) for v in verses]


print(f"Selected {len(verses)} verses.")
time.sleep(1)
print(verses_and_scores)
print()


print("Generating V3 BHTs for these verses...")
bht_generator = BHTGenerator()
bht_generator.generate_bhts(verses, [choicest_prompt], [bht_prompt], COMMENTATORS, redo_bht=REGENERATE_BHTS)
print("Done.")

print("Compiling data...")

data_rows = []

data = {}

data['v2_scores'] = []
data['v3_scores'] = []
data['improvements'] = []
data['commentator_counts'] = []
data['commentator_tier_similarities'] = []
data['v2_tiers'] = []
data['v3_tiers'] = []

folder = f'gpt output/bht/json/{choicest_prompt} X {bht_prompt}'
for verse_ref, v2_score in verses_and_scores:
    book, chapter, verse = get_book_chapter_verse(verse_ref)
    v3_path = f'{folder}/{book}/Chapter {chapter}/{book} {chapter} {verse} bht.json'
    result_json = json.load(open(v3_path))
    v3_score = result_json["bestBHT"]["qualityScore"]

    v2t1_raw, v2t2_raw, v2t3_raw = tiers[verse_ref]
    tier_total = v2t1_raw + v2t2_raw + v2t3_raw
    v2t1 = round(100 * v2t1_raw / tier_total, 2)
    v2t2 = round(100 * v2t2_raw / tier_total, 2)
    v2t3 = round(100 * v2t3_raw / tier_total, 2)

    commentator_count = len(result_json["choicestQuotes"])
    improvement = v3_score - v2_score
    v3t1, v3t2, v3t3 = result_json["bestBHT"]["commentatorTierSimilarities"]
    data_rows.append(f'{verse_ref},{v2_score},{v3_score},{improvement},{commentator_count},{v2t1},{v2t2},{v2t3},{v3t1},{v3t2},{v3t3}')

    data['v2_scores'].append(v2_score)
    data['v3_scores'].append(v3_score)
    data['improvements'].append(improvement)
    data['commentator_counts'].append(commentator_count)
    data['v2_tiers'].append((v2t1, v2t2, v2t3))
    data['v3_tiers'].append((v3t1, v3t2, v3t3))

print("Done.")

# write to CSV
print('Writing results to CSV file...')

csv_file_path = f'scripts output/v3_gen_test-{n}-buckets.csv'
with open(csv_file_path, 'w') as csv_file:
    csv_file.write('Verse,V2 Score,V3 Score,Improvement,Commentator Count, V2 Tier 1, V2 Tier 2, V2 Tier 3, V3 Tier 1, V3 Tier 2, V3 Tier 3\n')
    for row in data_rows:
        csv_file.write(row + '\n')

print('Done.')

print('[Summary]')
print(f'- V2 Average: {sum(data["v2_scores"]) / len(data["v2_scores"])}')
print(f'- V3 Average: {sum(data["v3_scores"]) / len(data["v3_scores"])}')
print(f'- V2 Median: {sorted(data["v2_scores"])[len(data["v2_scores"]) // 2]}')
print(f'- V3 Median: {sorted(data["v3_scores"])[len(data["v3_scores"]) // 2]}')

target_improvement = []
for i in range(len(data_rows)):
    if data['commentator_counts'][i] >= 3:
        if data['v2_scores'][i] > 2.5 and data['v3_scores'][i] > 2:
            continue
        target_improvement.append(data['improvements'][i])
        
print(f'\n[Improvement of verses]')
print(f'- Total: {sum(target_improvement)}')
print(f'- Average: {sum(target_improvement) / len(target_improvement)}')
print(f'- Median: {sorted(target_improvement)[len(target_improvement) // 2]}')

def print_average_tiers(tiers, version):
    t1s = [t[0] for t in tiers]
    t2s = [t[1] for t in tiers]
    t3s = [t[2] for t in tiers]
    print(f'- {version} Tiers: {sum(t1s) / len(t1s)} {sum(t2s) / len(t2s)} {sum(t3s) / len(t3s)}')

print(f'\n[Commentator Tier Similarity]')
print_average_tiers(data['v2_tiers'], 'V2')
print_average_tiers(data['v3_tiers'], 'V3')