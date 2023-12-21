import datetime
import re
import shelve
from pathlib import Path

import typer
from openai import OpenAI
from rst2pdf.createpdf import RstToPdf

app = typer.Typer()

GPT_CLIENT = OpenAI()

_THIS_FILE = Path(__file__)

_BOOKS_FILE = _THIS_FILE / "data" / "books.pkl"
_PROGRESS_FILE = _THIS_FILE / "data" / "progress.pkl"
# _PROGRESS_FILE = Path("data/progress.pkl")

_LATEX_PAGE_HEADER = """\n\\noindent\\makebox[\\textwidth]{
  \\large\\textbf{TEST2}%
  \\hfill%
  TEST1
}"""

_LATEX_DOC_HEADER = """\\documentclass[12pt]{article}

\\begin{document}
\\pagenumbering{gobble}
\\addtolength{\\oddsidemargin}{-1in}
\\addtolength{\\evensidemargin}{-1in}
\\addtolength{\\textwidth}{2in}

\\addtolength{\\topmargin}{-1in}


\\addtolength{\\textheight}{2in}"""


PAGEBREAK = """
.. raw:: pdf

    PageBreak"""

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
MONTHS = [
    0,
    "Jan",
    "Feb",
    "March",
    "April",
    "May",
    "June",
    "July",
    "Aug",
    "Sept",
    "Oct",
    "Nov",
    "Dec",
]

SYSTEM_INSTRUCTION = """You are helping a student comprehend a passage by asking a few probing questions.  All questions should be one sentence at most.

The first question begins:

"Circle or highlight the section of the passage which ..."

For the second question, supply the student with the definition of a vocabulary word from the passage and instruct them to determine which word matches the definition.  The second question begins:

"What word from the text means... "

For 3rd and last question, ask the student a question that tests for an overall understanding of its meaning or significance."""


@app.command("ingest")
def import_text_file(target: str, chars_per_page: int = 5_000, debug: bool = False):
    """Import a (properly formatted) book.txt

    line 1: Book Title
    line 2: Book Author
    CHAPTER 1 Optional Chapter Title
    SUBSECTION IN ALL CAPS
    One line of text per paragraph."""

    fp = open(target, "r", encoding="utf-8")
    lines = fp.readlines()

    title = lines[0]
    author = lines[1]

    text = "\n".join(lines[2:])
    # sections = text.split("START_OF_NEW_SECTION")
    # sections = [e.strip() for e in sections]
    chapter_pattern = re.compile(r"( *CHAPTER (\d+) ?(.*))")
    section_pattern = re.compile(r"[^a-z\n\.\?\]\)]+\??\n")

    book = []
    for chapter in chapter_pattern.findall(text):
        chapter_number = int(chapter[1])
        chapter_name = chapter[2]
        full_chapter = f"Chapter {chapter_number}{f': {chapter_name.title()}' if chapter_name else ''}"
        split = text.split(str(chapter[0]))  # chapter[0] is the full match
        chapter_text = split[1]
        chapter_text = chapter_pattern.split(chapter_text)[0]
        subsections = []

        if not section_pattern.search(chapter_text):
            subsections = [{"title": f"{full_chapter}", "text": chapter_text}]

        for subsection in section_pattern.findall(chapter_text):
            breakpoint()
            section_text = chapter_text.split(subsection)[0]
            section_name = subsection
            subsections.append(
                {"title": f"{full_chapter}\\\\\n{section_name}", "text": section_text}
            )

        for section in subsections:
            section_length = len(section["text"])
            page_count = section_length // chars_per_page + 1
            if page_count > 1:
                paragraphs = section["text"].split("\n")
                paginated = []
                counter = 0
                while paragraphs:
                    counter += 1
                    new_page = ""
                    while len(new_page) < section_length and paragraphs:
                        new_page += f"{paragraphs[0]}"
                        del paragraphs[0]
                    doc = {
                        "title": section["title"] + f" (Part {counter})",
                        "text": new_page,
                    }

                    paginated.append(doc)

                for part in paginated:
                    book.append(part)
            else:
                book.append(section)
    breakpoint()
    # paragraph_pattern = re.compile(r"($.+\.\n")
    chapters = chapter_pattern.split(text)
    # book = []

    # for i, section in enumerate(sections):
    #     page = {}
    #     title = chapter_pattern.search(section)
    #     if title:
    #         title = title[0]

    #     else:
    #         title = f"Section {i}"

    #     page["title"] = title.strip()
    #     text = chapter_pattern.sub("", section)
    #     # text = paragraph_pattern.sub()
    #     page["text"] = text.strip()
    #     book.append(page)

    # book2 = []

    # for page in book:
    #     size = len(page["text"])
    #     pages_of_content = size // 5000 + 1  # 5k chars per page max
    #     if pages_of_content > 1:
    #         content_size = size // pages_of_content  # paginate evenly
    #         paragraphs = page["text"].split("\n")
    #         paginated_pages = []
    #         counter = 0
    #         while paragraphs:
    #             counter += 1
    #             new_page = ""
    #             while len(new_page) < content_size and paragraphs:
    #                 new_page += f"{paragraphs[0]}"
    #                 del paragraphs[0]
    #             doc = {"title": page["title"] + f" (Part {counter})", "text": new_page}

    #             paginated_pages.append(doc)

    #         for part in paginated_pages:
    #             book2.append(part)

    #     else:
    #         book2.append(page)

    # book = book2
    if not debug:
        with shelve.open(_BOOKS_FILE.name) as db:
            db[target] = book


@app.command("set_progress")
def set_progress(target: str, progress: int = 0):
    with shelve.open(_PROGRESS_FILE.name) as db:
        db[target] = progress


@app.command("generate")
def generate_pages(target: str, n: int = 7, debug: bool = False):
    with shelve.open(_PROGRESS_FILE.name) as db:
        if target in db.keys():
            PROGRESS_INDEX = db[target]
        else:
            db[target] = 0
            PROGRESS_INDEX = 0

    mytext = _LATEX_DOC_HEADER
    start = datetime.datetime.today()
    days = [start + datetime.timedelta(days=i) for i in range(30)]
    dates = [
        f"{WEEKDAYS[day.weekday()]} {MONTHS[day.month]} {day.day}, {day.year}"
        for day in days
    ]

    pdf = RstToPdf()
    with shelve.open(_BOOKS_FILE.name) as db:
        book_size = len(db[target])
        for index in range(n):
            underline = "#" * len(
                db[target][(PROGRESS_INDEX + index) % book_size]["title"]
            )

            if not debug:
                response = GPT_CLIENT.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": SYSTEM_INSTRUCTION},
                        {
                            "role": "user",
                            "content": db[target][(PROGRESS_INDEX + index) % book_size][
                                "text"
                            ],
                        },
                    ],
                )

                questions = response.choices[0].message.content
                lines = questions.split("\n")

                questions = [line for line in lines if len(line) > 0]
                questions = [f"{i+1}.) {text}" for i, text in enumerate(questions)]
                questions = "\n\n".join(questions)
            else:
                questions = "[QUESTIONS GO HERE]"

            mytext += f"{_LATEX_PAGE_HEADER}\n{db[target][(PROGRESS_INDEX + index) % book_size]['title']}{dates[index]}\\newline{db[target][(PROGRESS_INDEX + index) % book_size]['text']} \\newline {questions}\\newpage"
            # mytext += f"{db[target][(PROGRESS_INDEX + index) % book_size]['title']}{dates[index]}\\\\{db[target][(PROGRESS_INDEX + index) % book_size]['text']} \\\\ {questions}\\newpage\\\\"
            # mytext += f"{db[target][(PROGRESS_INDEX + index) % book_size]['title']}\n{underline}\n{dates[index]}\n{'='*len(dates[index])}\n{db[target][(PROGRESS_INDEX + index) % book_size]['text']} \n\n {questions}\n\n{PAGEBREAK}\n\n"

        mytext = re.sub(pattern=r"&", repl=r"\\&", string=mytext)
        print(mytext)
        # pdf.createPdf(
        #     text=mytext,
        #     output=f"ENGLISH {datetime.datetime.today().day} {datetime.datetime.today().month} {datetime.datetime.today().year}.pdf",
        # )
        fp = open(
            f"English Reading {MONTHS[datetime.datetime.now().month]} {datetime.datetime.now().day} {datetime.datetime.now().year}.tex",
            "w",
            encoding="utf-8",
        )
        mytext += r"\end{document}"

        fp.write(mytext)

    if not debug:
        with shelve.open(_PROGRESS_FILE.name) as db:
            db[target] = PROGRESS_INDEX + n


if __name__ == "__main__":
    app()
    # import_text_file(debug=False)
    # generate_pages(7, debug=False)
    # db = shelve.open(_BOOKS_FILE.name)
