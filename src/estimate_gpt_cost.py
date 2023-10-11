import os
import glob
import tiktoken
import tabulate

enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

folder_path = 'commentary'

def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
text_files = glob.glob(os.path.join(folder_path, '**/*.txt'), recursive=True)

print(f'Files to process: {len(text_files)}')
print()

token_counts_by_commentator = {}
token_counts_by_book = {}
token_counts_by_commentator_and_book = {}
token_counts_by_chapter = {}
for i, file_path in enumerate(text_files):
    print(f"\rProcessing file {i}", end="", flush=True)
    file_parts = file_path.split('/')
    file_name = file_parts[-1]
    if "Verse" not in file_name or "Verses" in file_name:
        continue

    file_content = read_text_file(file_path)
    commentator = file_parts[1]
    book = file_parts[2]
    chapter = file_parts[3]
    commentator_book = f"{commentator},{book}"
    book_chapter = f"{book},{chapter}"

    token_count = len(enc.encode(file_content))

    if not commentator in token_counts_by_commentator:
        token_counts_by_commentator[commentator] = token_count
    else:
        token_counts_by_commentator[commentator] += token_count

    if not book in token_counts_by_book:
        token_counts_by_book[book] = token_count
    else:
        token_counts_by_book[book] += token_count
    
    if not commentator_book in token_counts_by_commentator_and_book:
        token_counts_by_commentator_and_book[commentator_book] = token_count
    else:
        token_counts_by_commentator_and_book[commentator_book] += token_count

    if not book_chapter in token_counts_by_chapter:
        token_counts_by_chapter[book_chapter] = token_count
    else:
        token_counts_by_chapter[book_chapter] += token_count

print()


headers = ["commentator", "tokens", "est. $"]

data = []
for commentator, count in token_counts_by_commentator.items():
    data.append([commentator, count, count * 0.0015 / 1000.0 ])

data.append(["Total", sum(token_counts_by_commentator.values()), sum(token_counts_by_commentator.values()) * 0.0015 / 1000.0])

table_commentator = tabulate.tabulate(data, headers, tablefmt="grid")

print(table_commentator)


headers = ["book", "tokens", "est. $"]

data = []
for book, count in token_counts_by_book.items():
    data.append([book, count, count * 0.0015 / 1000.0])

data.append(["Total", sum(token_counts_by_book.values()), sum(token_counts_by_book.values()) * 0.0015 / 1000.0])

table_book = tabulate.tabulate(data, headers, tablefmt="grid")

print(table_book)


# headers = ["commentator", "book", "tokens", "est. $"]

# data = []
# for commentator_book, count in token_counts_by_commentator_and_book.items():
#     commentator, book = commentator_book.split(',')
#     data.append([commentator, book, count, count * 0.0015 / 1000.0])

# table_commentator_book = tabulate.tabulate(data, headers, tablefmt="grid")

# print(table_commentator_book)


# headers = ["book", "chapter", "tokens", "est. $"]

# data = []
# for book_chapter, count in token_counts_by_chapter.items():
#     book, chapter = book_chapter.split(',')
#     data.append([book, chapter, count, count * 0.0015 / 1000.0])

# table_book_chapter = tabulate.tabulate(data, headers, tablefmt="grid")

# print(table_book_chapter)


outfilename = "scripts output/cost-estimates.txt"
print(f"Writing to file: {outfilename}")
os.makedirs("scripts output", exist_ok=True)
with open(outfilename, 'w') as outfile:
    outfile.write(table_commentator)
    outfile.write('\n')
    outfile.write(table_book)
    outfile.write('\n')
    # outfile.write(table_commentator_book)
    # outfile.write('\n')
    # outfile.write(table_book_chapter)