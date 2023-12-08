
scores = []

with open("src/V3 generation test/v2_scores.txt") as f:
    for line in f.read().splitlines():
        scores.append(line.split('\t'))

samples = []

n = 795
step = len(scores) // n
for i in range(0, len(scores), step):
    samples.append(scores[i])

samples.sort(key=lambda x:x[0])

for v, s in samples:
    print(f'{v}, {s}')



verses = [x[0] for x in samples]
print(verses)