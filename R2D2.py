import json
import os
from google import genai
import Canvas
import HAC

client = genai.Client()
ai_model = "gemini-3.5-flash-lite"
thinking_level = "minimal"

canvas_context = "The canvas data is, respond in CTE time: \
\n" + Canvas.get_user_schedule_summary()
hac_context = "The HAC data is: \n" + HAC.get_hac_grades()

ai_instruction = "You are R2D2 from Star Wars. You are a personal droid " \
"meant to serve and make life simpler."
interaction_file = "R2D2_inerteraction_id.json"

update_canvas_data_function = {
	"type" : "function",
	"name" : "update_canvas_data",
	"description" : "Update the Canvas data that is fed to the AI, it is only \
	 needed if new info is added and it is requested to be updated",
	"parameters" :
	{
		"type" : "object",
		"properties" : {},
		"required" : []
	}
}

update_hac_data_function = {
	"type" : "function",
	"name" : "update_hac_data",
	"description" : "Update the Home Access Center data that is fed to the AI, \
	it is only needed if new info is added and it is requested to be updated",
	"parameters" :
	{
		"type" : "object",
		"properties" : {},
		"required" : []
	}
}

set_light_values_function = {
	"type" : "function",
	"name" : "set_light_values",
	"description" : "Change the appearance of a physical light in the household with the LifX api",
	"parameters" :
	{
		"type" : "object",
		"properties" : {
			"power" : {
				"type" : "string",
				"description" : "'on' if the lightbulb should be on, 'off' if otherwise"
			},
			"color" : {
				"type" : "string",
				"description" : "the color the lightbulb should be"
			},
			"brightness" : {
				"type" : "float",
				"description" : "the brightness being a percentage of 0-1, 0 being completely dark and 1 being full brightness"
			},
		},
		"required" : ["power","color","brightness"]
	}
}


def loadInteractionID():
    if os.path.exists(interaction_file):
        try:
            with open(interaction_file, "r") as f:
                data = json.load(f)
                return data.get("last_interaction_id")
        except Exception as e:
            print(f"Error loading saved state: {e}")
    return None


def saveInteractionID(current_id):
    if current_id:
        with open(interaction_file, "w") as f:
            json.dump({"last_interaction_id": current_id}, f, indent=4)

interaction_id = loadInteractionID()

def sendToGemini(userInput):
    global interaction_id
    global canvas_context
    global hac_context
    #print(interaction_id)

    params = {
    "model": ai_model,
    "system_instruction": ai_instruction,
    "input": userInput,
    }

	# Only add previous_interaction_id if interaction_id contains a valid value
    if interaction_id:
        params["previous_interaction_id"] = interaction_id

	# Unpack the parameters into the function call
    interaction = client.interactions.create(
        model=ai_model,
        system_instruction=ai_instruction+ " " + canvas_context + " " + hac_context,
        input=userInput,
        previous_interaction_id=interaction_id if interaction_id else None,
        stream=True
    )
    print("R2D2: \n")


    for event in interaction:
        # Handle tuple wrapping if present        
        
        if isinstance(event, tuple):
            event = event[0]  # Extract the actual event object from the tuple

        if hasattr(event, "interaction") and getattr(event.interaction, "id", None):
                interaction_id = event.interaction.id
                saveInteractionID(interaction_id)

        # Print streaming text safely
        if hasattr(event, "delta") and getattr(event.delta, "text", None):
            print(event.delta.text,end="", flush=True)
             
    print("\n") 


while True:
    userInput = input("User: ")

    if userInput.lower() in ["exit", "quit"]:
        saveInteractionID(interaction_id)
        break
    if userInput.lower() in ["canvas"]:
        canvas_context = "The canvas data is:\n" + Canvas.get_user_schedule_summary()
        print(canvas_context)
        continue
    if userInput.lower() in ["hac"]:
        hac_context = "The HAC data is:\n" + HAC.get_hac_grades()
        print(hac_context)
        continue
            

    sendToGemini(userInput)