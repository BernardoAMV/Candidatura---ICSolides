import anthropic
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("CLAUDE_API_KEY")
client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=API_KEY,
)
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "qual idade da terra?"}
    ]
)
print(message.content)