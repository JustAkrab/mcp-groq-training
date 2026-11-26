import os


from dotenv import load_dotenv
from groq import Groq



load_dotenv()

client = Groq(api_key= os.environ["GROQ_API_KEY"],)
MODEL = "openai/gpt-oss-120b"



response = client.chat.completions.create(
    model = MODEL,
    messages=[{"role": "user", "content": "What time is it right now?"}],
    
)

print(response.choices[0].message.content)

