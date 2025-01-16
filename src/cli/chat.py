import os

import typer
from openai import OpenAI

app = typer.Typer()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
    model="gpt-4o",
)


@app.command()
def chat() -> None:
    """Chat with your pins! Ask for recommendations or itineraries."""
    print(chat_completion.choices[0].message.content)
