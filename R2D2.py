import json
import os
from google import genai
import Canvas

client = genai.Client()
ai_model = "gemini-3.6-flash"
thinking_level = "minimal"

canvas_context = "The canvas data is:\n{Canvas.get_user_schedule_summary()}"

ai_instruction = "You are R2D2 from Star Wars. You are a personal droid " \
"meant to serve and make life simpler."
interaction_file = "R2D2_inerteraction_id.json"



def loadInteractionID():
    if os.path.exists(interaction_file):
        try:
            with open(interaction_file, "r") as f:
                data = json.load(f)
                return data.get("last_interaction_id")
        except Exception as e:
            print(f"Error loading saved state: {e}")
    return None

def saveInteractionID():
    with open(interaction_file, "w") as f:
        json.dump({"last_interaction_id": interaction_id}, f, indent=4)

interaction_id = loadInteractionID()

def sendToGemini(userInput):
    global interaction_id
    params = {
        "model":ai_model,
        "input":userInput,
        "system_instruction":ai_instruction+canvas_context,
        "generation_config":
        {
            "thinking_level":thinking_level
        },
        "stream":True,
    }

    if interaction_id:
        params["previous_interaction_id"] = interaction_id

    stream = client.interactions.create(**params)
    
    print("R2D2: ")

    for event in stream:

        if hasattr(event, "interaction") and event.interaction and event.interaction.id:
            interaction_id = event.interaction.id
            saveInteractionID()

        if event.event_type == "step.delta":
            if event.delta.type == "text":
                print(event.delta.text, end="")
    print("\n")


while True:
    userInput = input("User: ")

    if userInput.lower() in ["exit", "quit"]:
        saveInteractionID()
        break
    else:
        if userInput.lower() in ["canvas"]:
            canvas_context = "The canvas data is:\n{Canvas.get_user_schedule_summary()}"

    sendToGemini(userInput)