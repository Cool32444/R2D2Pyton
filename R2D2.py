from google import genai

client = genai.Client()

userInput = input("User: ");

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input= userInput,
)
print("R2D2: " + interaction.output_text)