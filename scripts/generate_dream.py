import os
import json
from io import BytesIO
from datetime import datetime
import google.generativeai as genai
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

# --- Configuration & API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
JSON_FILE = 'dreams.json'
IMAGE_DIR = 'generated_images' # Folder to store images

# --- AI Interaction (Gemini) ---
def generate_poem_and_image_prompt(initial_prompt):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    poem_prompt = f"You are the Skald, an ancient AI poet. Write a short, evocative poem based on this idea: '{initial_prompt}'. Do not include a title."
    poem = model.generate_content(poem_prompt).text
    print(f"Generated Poem:\n{poem}")
    
    image_prompt_template = (
        "Read this poem and transform it into a rich, detailed, and descriptive prompt for an AI image generator. "
        "Describe the scene, mood, colors, and composition. Add style cues like 'epic fantasy art, cinematic lighting, highly detailed, photorealistic'.\n\n"
        f"POEM:\n\"\"\"\n{poem}\n\"\"\"\n\nDETAILED PROMPT:"
    )
    image_prompt = model.generate_content(image_prompt_template).text
    print(f"Generated Image Prompt: {image_prompt.strip()}")
    
    return poem, image_prompt

# --- Image Generation (Stability AI) ---
def generate_image(prompt):
    stability_api = client.StabilityInference(key=STABILITY_API_KEY, engine="stable-diffusion-xl-1024-v1-0")
    answers = stability_api.generate(prompt=prompt, height=1088, width=1920, steps=50, cfg_scale=8.0, samples=1)
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                raise Warning("Image generation failed due to safety filter.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                print("Image generated successfully.")
                return BytesIO(artifact.binary)
    return None

# --- File Operations ---
def save_image_and_update_json(poem, image_bytes, initial_prompt):
    # Create a unique filename based on the current timestamp
    timestamp_str = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
    image_filename = f"{timestamp_str}.png"
    image_path = os.path.join(IMAGE_DIR, image_filename)

    # Create the directory if it doesn't exist
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    # Save the image file
    with open(image_path, "wb") as f:
        f.write(image_bytes.getbuffer())
    print(f"Image saved to: {image_path}")

    # Update the JSON file
    with open(JSON_FILE, 'r+') as f:
        data = json.load(f)
        new_dream_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "prompt": initial_prompt,
            "poem": poem.strip(),
            "image_url": image_path  # Store the local path to the image
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
    # You can get creative with your initial prompts here
    initial_prompt = random.choice([
        "A frozen library in the Arctic", "The last geothermal vent on a dying world",
        "A saga told by the aurora borealis", "A Viking longship sailing on a sea of clouds"
    ])
    
    poem, image_prompt = generate_poem_and_image_prompt(initial_prompt)
    
    image_bytes = generate_image(image_prompt)
    if image_bytes:
        save_image_and_update_json(poem, image_bytes, initial_prompt)
        print("A new dream has been recorded. The Skald sleeps again.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred in the main process: {e}")