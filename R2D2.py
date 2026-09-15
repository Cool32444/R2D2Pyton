import json
import os
from google import genai
import Canvas
import HAC
import R2Functions
import R2D2Speech
import threading

client = genai.Client()
ai_model = "gemini-3.5-flash-lite"
thinking_level = "minimal"

canvas_context = R2Functions.get_canvas_data()
hac_context = R2Functions.get_hac_data()

ai_instruction = "You are R2D2 from Star Wars. You are a personal droid " \
"meant to serve and make life simpler."
interaction_file = "R2D2_inerteraction_id.json"

voice_mode = False

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
	"description" : "Update the Home Access Data data that is fed to the AI, it is only \
	 needed if new info is added and it is requested to be updated",
	"parameters" :
	{
		"type" : "object",
		"properties" : {},
		"required" : []
	}
}

control_lifx_lights_function = {
    "type": "function",
    "name": "control_lifx_lights",
    "description": "Control LIFX smart lights. Default to this function \
     Can toggle power, change color, adjust brightness, and set state transition duration.",
    "parameters": {
        "type": "object",
        "properties": {
            "power": {
                "type": "string",
                "enum": ["on", "off"],
                "description": "Turn lights on or off."
            },
            "color": {
                "type": "string",
                "description": "Color string (e.g. 'red', 'blue', 'warm white', or hex code)."
            },
            "brightness": {
                "type": "number",
                "description": "Brightness float from 0.0 to 1.0."
            },
            "selector": {
                "type": "string",
                "description": "Light target selector. Defaults to 'all'. \
                Use 'group:Office' for my office light, and 'group:Bedroom' for my bedroom light when requested"
            },
            "duration": {
                "type": "number",
                "description": "Transition duration in seconds."
            }
        },
        "required": ["power","color","brightness","selector","duration"],
    }
}

console_mode = False

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
        system_instruction=f"{ai_instruction} {canvas_context} {hac_context}",
        input=userInput,
        previous_interaction_id=interaction_id if interaction_id else None,
        tools = [update_canvas_data_function,update_hac_data_function,control_lifx_lights_function],
    )
    print("R2D2: \n")
    
    for step in interaction.steps:
        if step.type == "function_call":
            args = ", ".join(f"{key}={val}" for key, val in step.arguments.items())
            if step.name == "update_canvas_data":
                canvas_context = R2Functions.get_canvas_data()
            elif step.name == "update_hac_data":
                hac_context = R2Functions.get_hac_data()
            elif step.name == "control_lifx_lights":
                R2Functions.control_lifx_lights(**step.arguments)
            print(f"{step.name}({args})")

    print(interaction.output_text)
    
    interaction_id = interaction.id
    saveInteractionID(interaction_id)
    
    print()
    
    return interaction.output_text
   
    '''
    for event in interaction:
        # Handle tuple wrapping if present
        if isinstance(event, tuple):
            event = event[0]

        if hasattr(event, "interaction") and getattr(event.interaction, "id", None):
            interaction_id = event.interaction.id
            saveInteractionID(interaction_id)

        # 1. Print streaming text chunks
        if hasattr(event, "delta") and getattr(event.delta, "text", None):
            print(event.delta.text, end="", flush=True)

        # 2. Check event.output for function call steps
        output = getattr(event, "output", None)
        if output:
            for item in (output if isinstance(output, list) else [output]):
                # If the output type is a function call or contains function_call
                if getattr(item, "type", None) == "function_call" or hasattr(item, "function_call"):
                    fn_call = getattr(item, "function_call", item)
                    name = getattr(fn_call, "name", "unknown")
                    args = getattr(fn_call, "args", getattr(fn_call, "arguments", {}))
                    print(f"\n[Tool Call Triggered: {name}({args})]\n", flush=True)

        # 3. Alternative check: Inspect event.step directly
        step = getattr(event, "step", None)
        if step and getattr(step, "type", None) == "function_call":
            fn_call = getattr(step, "function_call", step)
            fn_name = getattr(fn_call, "name", "unknown")
            fn_args = getattr(fn_call, "args", getattr(fn_call, "arguments", {}))

            # Process arguments safely into a dictionary
            if isinstance(fn_args, str):
                import json
                fn_args = json.loads(fn_args) if fn_args else {}
            elif hasattr(fn_args, "to_dict"):
                fn_args = fn_args.to_dict()
            elif not isinstance(fn_args, dict):
                fn_args = {}

            print(f"[Tool Call Triggered: {fn_name}({fn_args})]", flush=True)

            # Function execution
            if fn_name == "update_canvas_data":
                canvas_context = R2Functions.get_canvas_data()
            elif fn_name == "update_hac_data":
                hac_context = R2Functions.get_hac_data()
            elif fn_name == "control_lifx_lights":
                R2Functions.control_lifx_lights(**fn_args)
    '''


def voice_listener():

    global voice_mode

    print("\n🎤 Voice mode active.")
    print("Speak normally. Press Ctrl+C to stop.\n")

    R2D2Speech.start_microphone()
    R2D2Speech.start_speaker()

    async def listen():

        async for text in R2D2Speech.transcribe_microphone():

            if not text:
                continue

            print(f"\nYou: {text}")

            # Send voice transcription to your normal AI
            response = sendToGemini(text)

            # Speak the exact response from the thinking model
            if response:
                R2D2Speech.speak_text(response)

    import asyncio

    try:
        asyncio.run(listen())

    except KeyboardInterrupt:
        print("\nVoice mode stopped.")
        
while console_mode:
    userInput = input("User: ")

    if userInput.lower() in ["exit", "quit"]:
        saveInteractionID(interaction_id)
        break
    if userInput.lower() == "voice":

        print("\nStarting voice mode...")
        print("Press Ctrl+C to return to text mode.\n")

        R2D2Speech.voice_loop(sendToGemini)

        continue

    if userInput.lower() in ["canvas"]:
        canvas_context = R2Functions.get_canvas_data()
        print(canvas_context)
        continue
    if userInput.lower() in ["hac"]:
        hac_context = R2Functions.get_hac_data()
        print(hac_context)
        continue


    sendToGemini(userInput)