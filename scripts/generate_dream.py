import os
import json
import random
import sys
import base64
import requests
from io import BytesIO
from datetime import datetime
import google.generativeai as genai

# --- Configuration & API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
JSON_FILE = 'dreams.json'
IMAGE_DIR = 'generated_images'

def generate_creative_prompt():
    print("DEBUG: Generating creative prompt...")
    # Simplified for stability
    prompt = "a Viking longship sailing the aurora borealis, about a forgotten saga, as a prophecy"
    print("DEBUG: Creative prompt generated.")
    return prompt

def generate_poem_and_image_prompt(initial_prompt):
    print("DEBUG: Configuring Gemini API...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("DEBUG: Gemini configured. Generating poem...")
    
    poem_response = model.generate_content(f"Write a short, evocative poem based on this idea: '{initial_prompt}'.")
    poem = str(getattr(poem_response, 'text', ''))
    print("DEBUG: Poem generation complete.")

    image_prompt_template = "Create a concise, powerful prompt for an AI image generator based on this poem... Example: Epic fantasy art, etc."
    image_prompt_response = model.generate_content(image_prompt_template)
    image_prompt = str(getattr(image_prompt_response, 'text', ''))
    print("DEBUG: Image prompt generation complete.")
    
    return poem, image_prompt

def generate_image(prompt):
    print("DEBUG: Preparing to call Stability AI REST API...")
    engine_id = "stable-diffusion-v1-6"
    api_host = "https://api.stability.ai"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {STABILITY_API_KEY}"
    }
    payload = {
        "text_prompts": [{"text": prompt}],
        "cfg_scale": 7, "height": 576, "width": 1024,
        "samples": 1, "steps": 30,
    }
    print("DEBUG: Calling Stability AI API endpoint...")
    response = requests.post(f"{api_host}/v1/generation/{engine_id}/text-to-image", headers=headers, json=payload)
    print(f"DEBUG: Stability AI response status code: {response.status_code}")

    if response.status_code != 200:
        raise Exception(f"Non-200 response from Stability API: {response.text}")

    data = response.json()
    print("DEBUG: JSON response from Stability AI parsed.")

    for image in data.get("artifacts", []):
        image_bytes = base64.b64decode(image["base64"])
        print("DEBUG: Image decoded from base64.")
        return BytesIO(image_bytes)
    
    return None

def save_image_and_update_json(poem, image_bytes, initial_prompt):
    print("DEBUG: Starting file-saving process...")
    timestamp_str = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
    image_filename = f"{timestamp_str}.png"
    image_path = os.path.join(IMAGE_DIR, image_filename)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    print(f"DEBUG: Saving image to {image_path}...")
    with open(image_path, "wb") as f:
        f.write(image_bytes.read())
    print("DEBUG: Image file written successfully.")

    with open(JSON_FILE, 'r+') as f:
        data = json.load(f)
        new_dream_entry = {
            "timestamp": str(datetime.utcnow().isoformat() + "Z"),
            "prompt": str(initial_prompt),
            "poem": str(poem).strip(),
            "image_url": str(image_path)
        }
        data['dreams'].append(new_dream_entry)
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    print("DEBUG: JSON file updated successfully.")

def main():
    print("DEBUG: Main function started.")
    if not all([GEMINI_API_KEY, STABILITY_API_KEY]):
        raise ValueError("DEBUG FAIL: API keys are missing.")
    
    print("DEBUG: STEP 1 - GENERATE PROMPT")
    initial_prompt = generate_creative_prompt()
    
    print("DEBUG: STEP 2 - GENERATE TEXTS FROM GEMINI")
    poem, image_prompt = generate_poem_and_image_prompt(initial_prompt)
    
    if not image_prompt or not image_prompt.strip():
        raise ValueError("DEBUG FAIL: Image prompt from Gemini is empty.")

    print("DEBUG: STEP 3 - GENERATE IMAGE FROM STABILITY AI")
    image_bytes = generate_image(image_prompt)
    
    if image_bytes:
        print("DEBUG: STEP 4 - SAVE FILES")
        save_image_and_update_json(poem, image_bytes, initial_prompt)
        print("DEBUG: Main function finished successfully.")
    else:
        raise Exception("DEBUG FAIL: No image was returned from Stability AI.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR in main process: {e}", file=sys.stderr)
        sys.exit(1)