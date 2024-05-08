import datetime
import json
import os
import re
from pathlib import Path

import appdirs
import google.generativeai as genai
import survey
import toml
import typer
from openai import OpenAI

try:
    from . import tomlshelve

except ImportError:
    import tomlshelve

app = typer.Typer()
list_app = typer.Typer(no_args_is_help=True)
config_app = typer.Typer()

app.add_typer(list_app, name="list")
app.add_typer(config_app, name="config")

GPT_CLIENT = OpenAI()  # API key must be in environment as "OPENAI_API_KEY"
_GEMINI_CREDENTIAL = os.environ.get("GOOGLE_AI_KEY")
genai.configure(api_key=_GEMINI_CREDENTIAL)

_GOOGLE_AI_MODELS = []
_OPEN_AI_MODELS = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]

for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        _GOOGLE_AI_MODELS.append(m.name)

_GOOGLE_LLM = genai.GenerativeModel("gemini-1.5-pro-latest")

_THIS_FILE = Path(__file__)

_BOOKS_FILE = (
    Path(appdirs.user_data_dir(roaming=True)) / "robolson" / "english" / "data" / "books.toml"
)
_PROGRESS_FILE = (
    Path(appdirs.user_data_dir(roaming=True)) / "robolson" / "english" / "data" / "progress.toml"
)

_BOOKS_FILE.parent.mkdir(parents=True, exist_ok=True)
_PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)

_BOOKS_FILE.touch()
_PROGRESS_FILE.touch()

_LATEX_DEFAULT_FILE = Path(_THIS_FILE.parent) / "config" / "english" / "latex_templates.toml"
_LATEX_FILE = (
    Path(appdirs.user_data_dir(roaming=True))
    / "robolson"
    / "english"
    / "config"
    / "latex_templates.toml"
)
_LATEX_FILE.parent.mkdir(exist_ok=True, parents=True)

if not _LATEX_FILE.exists():
    _LATEX_FILE.touch()
    _LATEX_TEMPLATES = toml.loads(open(_LATEX_DEFAULT_FILE.absolute(), "r").read())
    toml.dump(o=_LATEX_TEMPLATES, f=open(_LATEX_FILE.absolute(), "w"))

_LATEX_TEMPLATES = toml.loads(open(_LATEX_FILE.absolute(), "r").read())

_LATEX_PAGE_HEADER = _LATEX_TEMPLATES["page_header"]
_LATEX_DOC_HEADER = _LATEX_TEMPLATES["doc_header"]
_LATEX_ADDENDUM = _LATEX_TEMPLATES["addendum"]

_CONFIG_DEFAULT_FILE = Path(_THIS_FILE.parent) / "config" / "english" / "config.toml"
_CONFIG_FILE = (
    Path(appdirs.user_data_dir(roaming=True)) / "robolson" / "english" / "config" / "config.toml"
)
_CONFIG_FILE.parent.mkdir(exist_ok=True, parents=True)

if not _CONFIG_FILE.exists():
    _CONFIG_FILE.touch()
    _CONFIG = toml.loads(open(_CONFIG_DEFAULT_FILE.absolute(), "r").read())
    toml.dump(o=_CONFIG, f=open(_CONFIG_FILE.absolute(), "w"))
breakpoint()
_CONFIG = toml.loads(open(_CONFIG_FILE, "r").read())

_WEEKDAYS = _CONFIG["constants"]["weekdays"]
_MONTHS = _CONFIG["constants"]["months"]
_MODEL = _CONFIG["LLM"]["model"]
breakpoint()
_SYSTEM_INSTRUCTION = _CONFIG["LLM"]["instruction"]

_JSON_PATTERN = re.compile(r"```json\n(.*)\n```", flags=re.DOTALL + re.MULTILINE)

instruction2 = """You are helping a student comprehend a passage by asking probing questions.  Your questions will be served to the student by an application and must therefore conform to the following JSON schema, where {relevant_paragraph} is the single most relevant paragraph from the passage for that question:
{
    [
        {
            "question": "[Ask a question to test the reader's surface understanding of a salient paragraph in the passage.]",
            "answer": "[Example answer.],
            "paragraph": "{relevant_paragraph}"
        },
        {
            "question": "Based on the context of the passage define the word {SAT_word}.",
            "answer": "[Example answer.],
            "paragraph": "{relevant_paragraph}"
        },
        {
            "question": "[Ask a question that probes the reader's overall understanding of the passage.]",
            "answer": "[Example answer.],
            "paragraph": "{relevant_paragraph}"
        }
    ]
}"""

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

    chapter_pattern = re.compile(
        r"^ *((CHAPTER|BOOK|ACT) (\d+) ?(.*))", re.IGNORECASE + re.MULTILINE
    )
    section_pattern = re.compile(r"\n([^a-z\n\.\?\]\)]+\??) *\n")

    book = []

    for chapter in chapter_pattern.findall(text):
        chapter_type = chapter[1]
        chapter_number = int(chapter[2])
        chapter_name = chapter[3]
        full_chapter = f"{chapter_type.title()} {chapter_number}{f': {chapter_name.title()}' if chapter_name else ''}"
        split = text.split(str(chapter[0]))  # chapter[0] is the full match
        chapter_text = split[1]
        chapter_text = chapter_pattern.split(chapter_text)[0]
        subsections = []

        section_titles = section_pattern.findall(chapter_text)
        section_titles = [f"{full_chapter} \\newline {e.strip().title()}" for e in section_titles]

        section_titles.insert(0, full_chapter)
        section_texts = section_pattern.sub(r"SPLIT_CHAPTER_HERE", chapter_text).split(
            "SPLIT_CHAPTER_HERE"
        )

        for i, section_title in enumerate(section_titles):
            subsections.append({"title": section_title, "text": section_texts[i].rstrip()})

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


@app.command("remove")
def remove_book(target: str = None):
    """Remove book from database."""

    if target:
        with tomlshelve.open(str(_BOOKS_FILE)) as book_db, tomlshelve.open(
            str(_PROGRESS_FILE)
        ) as progress_db:
            if target not in book_db.keys():
                print(f"'{target}' not found in database.")
                return

            del book_db[target]
            try:
                del progress_db[target]
            except KeyError:
                pass

            book_db.sync()
            progress_db.sync()

            print(f"'{target}' removed from database.")
        return

    # no target supplied

    with tomlshelve.open(str(_BOOKS_FILE)) as book_db:
        books = list(book_db.keys())

        targets = survey.routines.basket("Remove which book(s)?", options=books)
        targets = [books[i] for i in targets]

        purge_list = ", ".join(target for target in targets)

        print(f"Removing '{purge_list}'.")

    for target in targets:
        remove_book(target)


@app.command("set-progress")
def set_progress(target: str = None, progress: int = None):  # type: ignore
    """Set progress for registered books.
    Future generation will proceed from the progress point."""

    with tomlshelve.open(str(_PROGRESS_FILE)) as progress_db:
        if target and (progress is not None):
            if target not in progress_db.keys():
                print(f"{target} not found in database.")
                return

            progress_db[target] = progress
            return

        with tomlshelve.open(_BOOKS_FILE) as db:
            form = {
                k: survey.widgets.Count(value=progress_db[k] if k in progress_db.keys() else 0)
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
    target: str = None,  # type:ignore
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
    # start = datetime.datetime.today()
    days = [start_date + datetime.timedelta(days=i) for i in range(30)]
    dates = [
        f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}" for day in days
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
                breakpoint()
                response = GPT_CLIENT.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": _SYSTEM_INSTRUCTION},
                        {
                            "role": "user",
                            "content": book[(PROGRESS_INDEX + index) % book_size]["text"],
                        },
                    ],
                )

                questions = str(response.choices[0].message.content)
                lines = questions.split("\n")

                questions = [line for line in lines if len(line) > 0]
                questions = [f"{i+1}.) {text}" for i, text in enumerate(questions)]
                questions = "\n\n".join(questions)
            else:
                json_response = None
                while not json_response:
                    response = _GOOGLE_LLM.generate_content(
                        f"{instruction2}\n\n{book[(PROGRESS_INDEX + index) % book_size]['text']}"
                    )
                    breakpoint()
                    json_response = _JSON_PATTERN.search(response.text)

                json_response = json_response.groups(0)[0]

                questions = "QUESTIONS GO HERE"

            dated_header = re.sub("DATEGOESHERE", dates[index], _LATEX_PAGE_HEADER)
            titled_header = re.sub("TITLEGOESHERE", title, dated_header)
            authored_header = re.sub("AUTHORGOESHERE", author, titled_header)
            mytext += f"{authored_header}\n\\section*{{{book[(PROGRESS_INDEX + index) % book_size]['title']}}}\n\n{book[(PROGRESS_INDEX + index) % book_size]['text']}\n\n{questions}{_LATEX_ADDENDUM}\\newpage"

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


@config_app.command("file")
def config_file():
    """Open config file with default text editor."""

    os.startfile(_CONFIG_FILE.absolute())


@config_app.command("creds")
def config_creds(google_api_key: str | None = None, openai_api_key: str | None = None):
    """Save your LLM API key to the appropriate environment variable."""

    if google_api_key:
        os.system(f"setx GOOGLE_AI_KEY {google_api_key}")

    if openai_api_key:
        os.system(f"setx OPENAI_API_KEY {openai_api_key}")

    if google_api_key or openai_api_key:
        return

    choices = survey.routines.select("Set which API keys?", options=["Google", "OpenAI"])

    if not choices:
        return

    for choice in choices:
        key = input(f"Enter your {choice} API key: ")

        match choice:
            case "Google":
                os.system(f"setx GOOGLE_AI_KEY {key}")

            case "OpenAI":
                os.system(f"setx OPENAI_API_KEY {key}")


@config_app.command("prompt")
def config_prompt():
    """Customize the prompt used for generating questions.

    WARNING: You must ensure the LLM generates JSON of the following schema:
    {
        [
            {
                "question": ...,
                "answer": ...,
                "passage": ...,
            }
        ]
    }"""

    form = {"prompt": survey.widgets.Input(value=_CONFIG["LLM"]["instruction"])}

    choice = survey.routines.form("", form=form)

    if not choice:
        return

    _CONFIG["LLM"]["instruction"] = choice["prompt"]

    toml.dump(o=_CONFIG, f=open(_CONFIG_FILE.absolute(), "w"))


@config_app.command("model")
def config_model(target: str | None = None):
    """Select an LLM to use for question generation."""

    models = (_GOOGLE_AI_MODELS if os.environ.get("GOOGLE_AI_KEY") else []) + (
        _OPEN_AI_MODELS if os.environ.get("OPENAI_API_KEY") else []
    )

    if target in models:
        choice = models.index(target)

    else:
        # choice = survey.routines.form("Frequency Weights (higher -> more frequent): ", form=form)
        choice = survey.routines.select("Use which model?", options=models)

    if not choice:
        return

    _CONFIG["LLM"]["model"] = models[choice]

    toml.dump(o=_CONFIG, f=open(_CONFIG_FILE.absolute(), "w"))


@config_app.callback(invoke_without_command=True)
def config(ctx: typer.Context):
    if ctx and ctx.invoked_subcommand:
        return

    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("GOOGLE_AI_KEY"):
        config_creds()

    config_model()
    config_prompt()


@app.callback(invoke_without_command=True)
def english_default(ctx: typer.Context):
    if ctx and ctx.invoked_subcommand:
        return

    if not _MODEL:
        print("AI model is not configured.\n")
        config_model()

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
