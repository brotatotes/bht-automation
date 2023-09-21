from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
import time
import os

STUDYLIGHT_URL = "https://studylight.org"
COMMENTARY_FOLDER = "commentary_output"

STUDYLIGHT_NT_VERSE_PARTITIONED_COMMENTARIES = {
    "Henry Alford" : "https://studylight.org/commentaries/eng/hac.html",
    "Jamieson-Fausset-Brown" : "https://studylight.org/commentaries/eng/jfb.html",
    "Albert Barnes" : "https://studylight.org/commentaries/eng/bnb.html",
    "Marvin Vincent" : "https://studylight.org/commentaries/eng/vnt.html",
    "John Calvin" : "https://studylight.org/commentaries/eng/cal.html",
    "Philip Schaff" : "https://studylight.org/commentaries/eng/scn.html",
    "Archibald T. Robertson" : "https://studylight.org/commentaries/eng/rwp.html",
    "Adam Clarke" : "https://studylight.org/commentaries/eng/acc.html",
    "John Nelson Darby" : "https://studylight.org/commentaries/eng/dsn.html",
    "John Wesley" : "https://studylight.org/commentaries/eng/wen.html", 
    "John Gill" : "https://studylight.org/commentaries/eng/geb.html"
}

def generate_headers():
    # Define a user agent string
    ua = UserAgent()
    user_agent = ua.random

    # Set up headers with the User-Agent
    headers = {'User-Agent': user_agent}
    
    return headers

def record_commentary(commentator_name):
    folder_name = commentator_name
    commentary_url = STUDYLIGHT_NT_VERSE_PARTITIONED_COMMENTARIES[commentator_name]

    response = requests.get(commentary_url, headers=generate_headers())
    # print(response.content)

    # Parse the HTML content using BeautifulSoup
    alford_html = BeautifulSoup(response.content, 'html.parser')

    books = []

    books_element = alford_html.find_all("div", class_="bcv mtlrb20")[-1] # New Testament Only
    for book in books_element.find_all('a'):
        books.append((book.get_text(), STUDYLIGHT_URL + book.get('href')))

    for book in books:
        book_name, book_url = book

        chapters = []

        response = requests.get(book_url, headers=generate_headers())
        books_html = BeautifulSoup(response.content, 'html.parser')
        chapters_element = books_html.find("div", class_="bcv mtlrb20")

        for chapter in chapters_element.find_all('a'):
            chapters.append((chapter.get_text(), 'https:' + chapter.get('href')))
        
        for chapter in chapters:
            chapter_name, chapter_url = chapter

            folder_path = f"{COMMENTARY_FOLDER}/{folder_name}/{book_name}/{chapter_name}"
            if not os.path.exists(folder_path):
                print(f"Creating new folder: {folder_path}")
                os.makedirs(folder_path)
            else:
                print(f"Skipping folder because it already exists: {folder_path}")
                continue

            # Now process the all verses on a chapter webpage.
            response = requests.get(chapter_url, headers=generate_headers())
            chapter_html = BeautifulSoup(response.content, 'html.parser')
            verses_element = chapter_html.find("div", class_="commentaries-entries")

            print(f"Writing all commentary for: {book_name} {chapter_name}!")

            verses = verses_element.find_all('div', class_="commentaries-entry-div")
            for verse in verses:
                verse_number = verse.find('h3', class_="commentaries-entry-number").find('a', class_="com-number")
                verse_number = verse_number.get_text() if verse_number else "None"
                commentary_pieces = verse.find_all('p')
                
                # print(verse_number)
                # print(commentary)
                filename = f'{folder_path}/{verse_number}.txt'

                if not os.path.exists(filename):
                    verse_file = open(filename, 'w')
                    for commentary_piece in commentary_pieces:
                        # Corner case for John Wesley commentary on studylight: remove verse reference from the commentary.
                        if commentator_name == "John Wesley" and "emphasis bold" in str(commentary_piece):
                            continue
                            
                        verse_file.write(commentary_piece.get_text() + '\n')
                    verse_file.close()

                # break # test one verse only.

            time.sleep(0.5)
            # break # test one chapter only.
        
        # outfile.write(str(book_html.content))

        # break # test one book only.

def get_all_commentary():
    for commentator in STUDYLIGHT_NT_VERSE_PARTITIONED_COMMENTARIES:
        if os.path.exists(f"{COMMENTARY_FOLDER}/{commentator}"):
            print(f"{COMMENTARY_FOLDER}/{commentator} already exists. Skipping!")
            continue
        record_commentary(commentator)


if __name__ == '__main__':
    record_commentary("John Wesley")