from google import genai

client = genai.Client(api_key="[ENCRYPTION_KEY]")
for m in client.models.list():
    print(m.name)
