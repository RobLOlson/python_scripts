import datetime
import re
from pathlib import Path

import appdirs
import survey
import toml
import typer
from openai import OpenAI

from . import tomlshelve

app = typer.Typer()
list_app = typer.Typer(no_args_is_help=True)
app.add_typer(list_app, name="list")

GPT_CLIENT = OpenAI()  # API key must be in environment as "OPENAI_API_KEY"

_THIS_FILE = Path(__file__)

_BOOKS_FILE = (
    Path(appdirs.user_data_dir()) / "robolson" / "english" / "data" / "books.toml"
)
_PROGRESS_FILE = (
    Path(appdirs.user_data_dir()) / "robolson" / "english" / "data" / "progress.toml"
)

_BOOKS_FILE.parent.mkdir(parents=True, exist_ok=True)
_PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)

_BOOKS_FILE.touch()
_PROGRESS_FILE.touch()

_LATEX_FILE = Path(_THIS_FILE.parent) / "config" / "english" / "latex_templates.toml"
_LATEX_FILE.parent.mkdir(exist_ok=True)
_LATEX_FILE.touch()
LATEX_TEMPLATES = toml.loads(open(_LATEX_FILE.absolute(), "r").read())

_LATEX_PAGE_HEADER = LATEX_TEMPLATES["page_header"]
_LATEX_DOC_HEADER = LATEX_TEMPLATES["doc_header"]

_CONFIG_FILE = Path(_THIS_FILE.parent) / "config" / "english" / "config.toml"
_CONFIG_FILE.parent.mkdir(exist_ok=True)
_CONFIG_FILE.touch()
CONFIGURATION = toml.loads(open(_CONFIG_FILE.absolute(), "r").read())

_WEEKDAYS = CONFIGURATION["constants"]["weekdays"]
_MONTHS = CONFIGURATION["constants"]["months"]
_SYSTEM_INSTRUCTION = CONFIGURATION["constants"]["instruction"]

_LINES = r"""
\\[12pt]
\rule{\linewidth}{.5pt}
\\[12pt]
\rule{\linewidth}{.5pt}
\\[12pt]
\rule{\linewidth}{.5pt}
\\[12pt]
\rule{\linewidth}{.5pt}
\\[12pt]
\rule{\linewidth}{.5pt}
\\
Write a brief summary of the passage.
\\[12pt]
\rule{\linewidth}{.5pt}
\\[12pt]
\rule{\linewidth}{.5pt}
\\[12pt]
\rule{\linewidth}{.5pt}
\\[12pt]
\rule{\linewidth}{.5pt}
\\[12pt]
\rule{\linewidth}{.5pt}
"""


@app.command("ingest")
def ingest_text_file(target: str, chars_per_page: int = 5_000, debug: bool = False):
    """Import a (properly formatted) book.txt

    line 1: Book Title
    line 2: Book Author
    CHAPTER 1 Optional Chapter Title
    SUBSECTION IN ALL CAPS
    One line of text per paragraph."""

    target = Path(target).name

    fp = open(target, "r", encoding="utf-8")
    lines = fp.readlines()

    title = lines[0].strip()
    author = lines[1].strip()

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

        section_titles = section_pattern.findall(chapter_text)
        section_titles = [e.strip() for e in section_titles]
        section_titles.insert(0, full_chapter)
        section_texts = section_pattern.sub(r"SPLIT_CHAPTER_HERE", chapter_text).split(
            "SPLIT_CHAPTER_HERE"
        )

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

                    # If remaining text is less than half the size of a normal excerpt
                    # Then just append it to the penultimate excerpt
                    if len("\n".join(paragraphs)) < chars_per_page / 2:
                        while paragraphs:
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
        with tomlshelve.open(str(_BOOKS_FILE)) as db:
            db[target] = {"book": book, "author": author, "title": title}

    # with tomlshelve.open(str(_BOOKS_FILE) + ".toml") as db:
    #     breakpoint()
    #     db[target] = {"book": book, "author": author, "title": title}


@app.command("set-progress")
def set_progress(target: str = None, progress: int = None):
    """Set progress for registered books.
    Future generation will proceed from the progress point."""

    with tomlshelve.open(str(_PROGRESS_FILE)) as progress_db:
        if target and (progress is not None):
            progress_db[target] = progress
            return

        with tomlshelve.open(_BOOKS_FILE) as db:
            form = {
                k: survey.widgets.Count(
                    value=progress_db[k] if k in progress_db.keys() else 0
                )
                for k in db.keys()
            }
        if form:
            data = survey.routines.form("Set Progress:", form=form)
            progress_db.update(data)
        else:
            print("No books have been ingested yet.  Aborting.")
            exit(1)


@app.command("generate")
def generate_pages(
    target: str = None,
    n: int = 7,
    debug: bool = True,
    start_date: datetime.datetime = datetime.datetime.today(),
):
    if target is None:
        with tomlshelve.open(_BOOKS_FILE) as db:
            candidates = list(db.keys())

            index = survey.routines.select(
                "Select book to generate questions: ", options=candidates
            )
            if index is None:
                print("No books ingested.  Aborting.")
                exit(1)

            target = candidates[index]

    target = Path(target).name

    with tomlshelve.open(str(_PROGRESS_FILE)) as db:
        if target in db.keys():
            PROGRESS_INDEX = db[target]
        else:
            db[target] = 0
            PROGRESS_INDEX = 0

    mytext = _LATEX_DOC_HEADER
    start = datetime.datetime.today()
    days = [start + datetime.timedelta(days=i) for i in range(30)]
    dates = [
        f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}"
        for day in days
    ]

    # with shelve.open(_BOOKS_FILE.name) as db:
    with tomlshelve.open(str(_BOOKS_FILE)) as db:
        if target not in db.keys():
            print(f"{target} not ingested.")
            return

        book = db[target]["book"]
        title = db[target]["title"]
        author = db[target]["author"]
        book_size = len(book)
        for index in range(n):
            if not debug:
                response = GPT_CLIENT.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": _SYSTEM_INSTRUCTION},
                        {
                            "role": "user",
                            "content": book[(PROGRESS_INDEX + index) % book_size][
                                "text"
                            ],
                        },
                    ],
                )

                questions = str(response.choices[0].message.content)
                lines = questions.split("\n")

                questions = [line for line in lines if len(line) > 0]
                questions = [f"{i+1}.) {text}" for i, text in enumerate(questions)]
                questions = "\n\n".join(questions)
            else:
                questions = "QUESTIONS GO HERE"
            dated_header = re.sub("DATEGOESHERE", dates[index], _LATEX_PAGE_HEADER)
            titled_header = re.sub("TITLEGOESHERE", title, dated_header)
            authored_header = re.sub("AUTHORGOESHERE", author, titled_header)
            mytext += f"{authored_header}\n\\section*{{{book[(PROGRESS_INDEX + index) % book_size]['title']}}}\n\n{book[(PROGRESS_INDEX + index) % book_size]['text']}\n\n{questions}{_LINES}\\newpage"

        mytext = re.sub(pattern=r"&", repl=r"\\&", string=mytext)
        if not debug:
            fp = open(
                f"English Reading {_MONTHS[datetime.datetime.now().month]} {datetime.datetime.now().day} {datetime.datetime.now().year}.tex",
                "w",
                encoding="utf-8",
            )
            print(f"Writing English homework to {fp.name}")
        else:
            print("Use '--no-debug' to save progress.")
            fp = open("English Sample.tex", "w", encoding="utf-8")

        mytext += r"\end{document}"

        fp.write(mytext)
        fp.close()

    if not debug:
        with tomlshelve.open(str(_PROGRESS_FILE)) as db:
            db[target] = PROGRESS_INDEX + n


@list_app.command("books")
def list_books():
    """List available books and current progress."""
    progress_db = tomlshelve.open(_PROGRESS_FILE)

    with tomlshelve.open(_BOOKS_FILE) as db:
        for book in db.keys():
            try:
                current_progress = progress_db[book]
            except KeyError:
                current_progress = 0

            print(f"{book} (Progress: {current_progress} / {len(db[book]['book'])})")


@app.callback(invoke_without_command=True)
def english_default(ctx: typer.Context):
    if ctx and ctx.invoked_subcommand:
        return

    available_books = list(tomlshelve.open(_BOOKS_FILE).keys())
    book_choice = survey.routines.select("Select a book: ", options=available_books)
    book_choice = available_books[book_choice]

    start_date = survey.routines.datetime(
        "Select assignment start date: ",
        attrs=("month", "day", "year"),
    )

    if not start_date:
        start_date = datetime.datetime.today()

    assignment_count = survey.routines.numeric(
        "How many reading assignments to generate? ", decimal=False, value=5
    )

    debug_status = survey.routines.inquire("Debug? ", default=True)

    generate_pages(
        target=book_choice,
        n=assignment_count,
        start_date=start_date,
        debug=debug_status,
    )


if __name__ == "__main__":
    app()
    # ingest_text_file(debug=False)
    # generate_pages(7, debug=False)
    # db = shelve.open(_BOOKS_FILE.name)
