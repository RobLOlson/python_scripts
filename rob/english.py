import datetime
import re
import shelve
from pathlib import Path

import appdirs
import toml
import typer
from openai import OpenAI
from rst2pdf.createpdf import RstToPdf

app = typer.Typer()

GPT_CLIENT = OpenAI()  # API key must be in environment as "OPENAI_API_KEY"

_THIS_FILE = Path(__file__)

_BOOKS_FILE = (
    Path(appdirs.user_data_dir()) / "robolson" / "data" / "english" / "books.pkl"
)
_PROGRESS_FILE = (
    Path(appdirs.user_data_dir()) / "robolson" / "data" / "english" / "progress.pkl"
)
# _PROGRESS_FILE = Path("data/progress.pkl")

LATEX_FILE = Path("config/latex_templates.toml")
LATEX_FILE = Path(_THIS_FILE.parent) / "config" / "english" / "latex_templates.toml"
LATEX_FILE.parent.mkdir(exist_ok=True)
LATEX_FILE.touch()
LATEX_TEMPLATES = toml.loads(open(LATEX_FILE.absolute(), "r").read())

_LATEX_PAGE_HEADER = """\n\\noindent\\makebox[\\textwidth]{
\\large\\textbf{TITLEGOESHERE}%
  \\hfill \\hspace{-2.5cm} DATEGOESHERE

}\\newline\\textbf{by AUTHORGOESHERE}\\newline"""
_LATEX_PAGE_HEADER = LATEX_TEMPLATES["page_header"]
_LATEX_DOC_HEADER = """\\documentclass[12pt]{article}
\\usepackage[a4paper,
            bindingoffset=0.2in,
            left=0.5in,
            right=0.5in,
            top=0.5in,
            bottom=0.5in,
            footskip=.25in]{geometry}
\\begin{document}
\\pagenumbering{gobble}"""
_LATEX_DOC_HEADER = LATEX_TEMPLATES["doc_header"]

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

For 3rd and last question, ask a question that probes the reader's overall understanding of the passage."""


@app.command("ingest")
def ingest_text_file(target: str, chars_per_page: int = 5_000, debug: bool = False):
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

    chapter_pattern = re.compile(r"( *CHAPTER (\d+) ?(.*))")
    section_pattern = re.compile(r"\n[^a-z\n\.\?\]\)]+\??\n")

    book = []
    for chapter in chapter_pattern.findall(text):
        chapter_number = int(chapter[1])
        chapter_name = chapter[2]
        full_chapter = f"Chapter {chapter_number}{f': {chapter_name.title()}' if chapter_name else ''}"
        split = text.split(str(chapter[0]))  # chapter[0] is the full match
        chapter_text = split[1]
        chapter_text = chapter_pattern.split(chapter_text)[0]
        subsections = []

        breakpoint()
        section_titles = section_pattern.findall(chapter_text)
        section_titles = [e.strip() for e in section_titles]
        section_titles.insert(0, full_chapter)
        section_texts = section_pattern.sub(r"SPLIT_CHAPTER_HERE", chapter_text).split(
            "SPLIT_CHAPTER_HERE"
        )
        breakpoint()
        for i, section_title in enumerate(section_titles):
            subsections.append(
                {"title": section_title, "text": section_texts[i].rstrip()}
            )

        for section in subsections:
            section_length = len(section["text"])
            page_count = section_length // chars_per_page + 1
            if page_count > 1:
                paragraphs = section["text"].split("\n")
                paragraphs = [p for p in paragraphs if p]
                paginated = []
                page_counter = 0
                while paragraphs:
                    new_page = ""
                    page_counter += 1
                    while len(new_page) < section_length / page_count and paragraphs:
                        new_page += f"\n\n \\indent {paragraphs[0]}"
                        del paragraphs[0]
                    doc = {
                        "title": section["title"] + f" (Part {page_counter})",
                        "text": new_page,
                    }

                    paginated.append(doc)

                for part in paginated:
                    book.append(part)
            else:
                book.append(section)

    if not debug:
        with shelve.open(_BOOKS_FILE.name) as db:
            db[target] = {"book": book, "author": author, "title": title}


@app.command("set_progress")
def set_progress(target: str, progress: int = 0):
    with shelve.open(_PROGRESS_FILE.name) as db:
        db[target] = progress


@app.command("generate")
def generate_pages(target: str, n: int = 7, debug: bool = True):
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

    with shelve.open(_BOOKS_FILE.name) as db:
        book = db[target]["book"]
        title = db[target]["title"]
        author = db[target]["author"]
        book_size = len(book)
        for index in range(n):
            underline = "#" * len(book[(PROGRESS_INDEX + index) % book_size]["title"])

            if not debug:
                response = GPT_CLIENT.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": SYSTEM_INSTRUCTION},
                        {
                            "role": "user",
                            "content": book[(PROGRESS_INDEX + index) % book_size][
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
                questions = "QUESTIONS GO HERE"
            dated_header = re.sub("DATEGOESHERE", dates[index], _LATEX_PAGE_HEADER)
            titled_header = re.sub("TITLEGOESHERE", title, dated_header)
            authored_header = re.sub("AUTHORGOESHERE", author, titled_header)
            breakpoint()
            mytext += f"{authored_header}\n\\section*{{{book[(PROGRESS_INDEX + index) % book_size]['title']}}}\n\n{book[(PROGRESS_INDEX + index) % book_size]['text']}\n\n{questions}\\newpage"

        mytext = re.sub(pattern=r"&", repl=r"\\&", string=mytext)
        print(mytext)
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
    # ingest_text_file(debug=False)
    # generate_pages(7, debug=False)
    # db = shelve.open(_BOOKS_FILE.name)
