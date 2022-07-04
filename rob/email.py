import os

from redmail import gmail

from .parser.email_parser import email_parser

# Execute the parse_args() method
args = email_parser.parse_args()

_TARGET = args.target
_CONTENT = " ".join(args.content)


# If target points at environment variable, replace pointer with contents of variable
_TARGET = [
    os.environ.get(elem) if elem in os.environ.keys() else elem for elem in _TARGET
]

gmail.username = os.environ.get("GMAIL_ADDRESS")
gmail.password = os.environ.get("GMAIL_APP_PASSWORD")

if len(_CONTENT) > 20:
    subject = _CONTENT[:16] + "..."
else:
    subject = _CONTENT

gmail.send(subject=subject, receivers=_TARGET, text=_CONTENT)
