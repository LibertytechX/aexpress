from google import genai

client = genai.Client(api_key="AIzaSyDTyIGMYJm0rKFWg3U6K9ATENmoOEUw4Pg")
for m in client.models.list():
    print(m.name)
