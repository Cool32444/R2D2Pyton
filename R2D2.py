from google import genai

client = genai.Client()

while True:
    userInput = input("User: ")

    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input=userInput,
    )
    print(interaction.output_text)