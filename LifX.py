import os
import requests

TOKEN = os.getenv("LIFX_TOKEN")
def set_lifx_light_color(color,selector,brightness,power,duration):
    print(f"{color}")
    url = f"https://api.lifx.com/v1/lights/{selector}/state"
    headers = {"Authorization": f"Bearer {TOKEN}"}  # Fixed capitalization
    
    payload = {"duration": duration}
    
    if power:
        payload["power"] = power.lower()
    if color:
        payload["color"] = color
    if brightness is not None:
        # Scale 1-100 percentage down to 0.0-1.0 float if needed
        val = brightness / 100.0 if brightness > 1.0 else brightness
        payload["brightness"] = max(0.0, min(1.0, val))

    try:
        response = requests.put(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return {
            "status": "success",
            "modified_lights": len(data.get("results", [])),
            "details": data.get("results", [])
        }
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}
