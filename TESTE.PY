import anthropic
import os
from dotenv import load_dotenv
result = load_dotenv()

API_KEY = os.getenv("CLAUDE_API_KEY")
print(API_KEY)
print(result)
client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=API_KEY,
)
message = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "qual idade da terra?"}
    ]
)
print(message.content)