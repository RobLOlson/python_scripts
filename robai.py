import os
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.Completion.create(
  engine="davinci",
  prompt="Once upon a time",
  max_tokens=5
)
