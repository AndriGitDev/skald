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

# --- Dynamic Prompt Generation ---
SUBJECTS = [
    "a geothermal lagoon under a sky of stars", "a library carved from glacial ice",
    "a Viking longship sailing the aurora borealis", "a lighthouse at the edge of the world",
    "a rune-carved stone humming with power", "the heart of a sleeping volcano",
    "a forgotten fishing village", "a path of glowing moss in a lava field"
]
CONCEPTS = [
    "a forgotten saga", "the memory of the first winter", "the silence between worlds",
    "the solitude of the midnight sun", "an echo from a dying star",
    "the weight of an ancient promise", "the birth of a new god"
]
STYLES = [
    "as a lost myth", "whispered by the arctic wind", "etched in volcanic rock",
    "as a prophecy", "as a sailor's final log entry", "as a lullaby for a giant"
]

def generate_creative_prompt():
    subject = random.choice(SUBJECTS)
    concept = random.choice(CONCEPTS)
    style = random.choice(STYLES)
    return f"{subject}, about {concept}, {style}"

# --- AI Interaction (Gemini) ---
def generate_poem_and_image_prompt(initial_prompt):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    poem_prompt = f"You are the Skald, an ancient AI poet. Write a short, evocative poem based on this idea: '{initial_prompt}'. Do not include a title."
    poem = str(getattr(model.generate_content(poem_prompt), 'text', ''))
    
    image_prompt_template = (
        "Read the following poem. Based on its mood, subjects, and feeling, create a concise and powerful prompt for an AI image generator. "
        "The prompt should be a single line of comma-separated keywords and descriptive phrases. Include artistic styles like 'epic fantasy art' or 'photorealistic'.\n\n"
        f"POEM:\n\"\"\"\n{poem}\n\"\"\"\n\nCONCISE PROMPT:"
    )
    image_prompt = str(getattr(model.generate_content(image_prompt_template), 'text', ''))
    return poem, image_prompt

# --- Image Generation (Stability AI via REST API) ---
def generate_image(prompt):
    engine_id = "stable-diffusion-xl-1024-v1-0"
    api_host = "https://api.stability.ai"
    
    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {STABILITY_API_KEY}"
        },
        json={
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            # THE FINAL FIX: Using dimensions allowed by the SDXL 1.0 model.
            "height": 768,
            "width": 1344,
            "samples": 1,
            "steps": 30,
        },
    )

    if response.status_code != 200:
        raise Exception(f"Non-200 response from Stability API: {response.text}")

    data = response.json()
    for image in data.get("artifacts", []):
        image_bytes = base64.b64decode(image["base64"])
        return BytesIO(image_bytes)
        
    return None

# --- File Operations ---
def save_image_and_update_json(poem, image_bytes, initial_prompt):
    timestamp_str = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
    image_filename = f"{timestamp_str}.png"
    image_path = os.path.join(IMAGE_DIR, image_filename)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    with open(image_path, "wb") as f:
        f.write(image_bytes.read())
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

# --- Main Execution ---
def main():
    if not all([GEMINI_API_KEY, STABILITY_API_KEY]):
        raise ValueError("Gemini or Stability API key is missing. Check your GitHub Secrets.")
    
    print("The Skald is waking...")
    initial_prompt = generate_creative_prompt()
    print(f"--- Initial Idea ---\n{initial_prompt}")
    
    poem, image_prompt = generate_poem_and_image_prompt(initial_prompt)
    print(f"--- Generated Poem ---\n{poem.strip()}")
    print(f"--- Generated Image Prompt ---\n{image_prompt.strip()}")
    
    if not poem or not poem.strip() or not image_prompt or not image_prompt.strip():
        raise ValueError("A required text (poem or image prompt) from Gemini was empty. Halting run.")

    image_bytes = generate_image(image_prompt)
    if image_bytes:
        save_image_and_update_json(poem, image_bytes, initial_prompt)
        print("A new dream has been recorded. The Skald sleeps again.")
    else:
        raise Exception("No image was returned from the generation service after a successful prompt.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR in main process: {e}", file=sys.stderr)
        sys.exit(1)