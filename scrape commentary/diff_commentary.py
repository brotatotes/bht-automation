import os
import re
from bs4 import BeautifulSoup

def list_files(start_path):
    all_files = []
    for root, dirs, files in os.walk(start_path):
        for file in files:
            full_path = os.path.join(root, file)
            all_files.append(full_path)
    return all_files


def remove_html_tags(text):
    # text = text.replace('</p>', '</p>\n')
    # text = re.sub(r'<.*?>', '', text)

    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()
    return text

def normalize_white_space(text):
    # text = re.sub(r'\.([^\.])', r'. \1', text)
    # text = re.sub(r'\)(\w)', r') \1', text)
    text = re.sub(r'\s+', '', text)
    return text


def compare_commentary(old_folder, new_folder, out_file_path):
    if os.path.exists(out_file_path):
        os.remove(out_file_path)

    old_files = list_files(old_folder)
    # new_files = list_files(new_path)

    file_count = len(old_files)

    for i, file_path in enumerate(old_files):
        if os.path.basename(file_path).startswith('.'):
            continue

        commentator, book, chapter, verse = file_path.split('/')[-4:]
        new_file_path = f'{new_folder}/{commentator}/{book}/{chapter}/{verse}'

        if not os.path.exists(new_file_path):
            with open(out_file_path, 'a') as out_file:
                out_file.write(f'FILE DOES NOT EXIST!!! {new_file_path}\n\n')
            continue
        
        old_content = normalize_white_space(open(file_path).read().strip())
        new_content = open(new_file_path).read().strip()
        processed_new_content = normalize_white_space(remove_html_tags(new_content).strip())

        print(f'{i+1}/{file_count} {old_content == processed_new_content}; {commentator} {book} {chapter} {verse}')

        if old_content != processed_new_content:
            with open(out_file_path, 'a') as out_file:
                out_file.write(f'"{file_path}" vs "{new_file_path}"')
                out_file.write('\n-------------------------------------------------\n')
                out_file.write(old_content)
                out_file.write('\n-------------------------------------------------\n')
                out_file.write(processed_new_content)
                out_file.write('\n-------------------------------------------------\n')
                out_file.write('\n\n')

            input('Continue? ')


if __name__ == '__main__':
    # old_folder = 'scrape commentary/commentary_output_all_old'
    old_folder = 'commentary'
    new_folder = 'scripts output/scrape commentary/commentary_output'
    out_file_path = f'scripts output/scrape commentary/report of {old_folder.split("/")[-1]} vs {new_folder.split("/")[-1]}.txt'

    compare_commentary(old_folder, new_folder, out_file_path)