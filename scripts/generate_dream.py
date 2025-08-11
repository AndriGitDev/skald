import os
import json
import random
import requests
import google.generativeai as genai
from datetime import datetime

# --- Configuration ---
# Fetch the API key from GitHub Actions secrets
API_KEY = os.getenv("GEMINI_API_KEY")
JSON_FILE = 'dreams.json'

# --- Prompt Generation ---
# A list of random concepts to inspire the AI
SUBJECTS = ["a lone lighthouse", "a forgotten library", "a city of glass", "a forest of singing trees", "an ocean of stars"]
CONCEPTS = ["the edge of reality", "the memory of a forgotten god", "the birth of a new color", "the future's echo", "the silence after the end"]
STYLES = ["in the style of a lost myth", "as a cryptic warning", "as a child's nursery rhyme", "as a final transmission", "as a love letter to the void"]

def generate_creative_prompt():
    """Creates a random, evocative prompt for the AI."""
    subject = random.choice(SUBJECTS)
    concept = random.choice(CONCEPTS)
    style = random.choice(STYLES)
    return f"{subject}, about {concept}, {style}"

# --- AI Interaction ---
def generate_art_and_poem(prompt):
    """Generates a poem and an image URL based on the prompt."""
    if not API_KEY:
        raise ValueError("API Key not found. Please set the GEMINI_API_KEY secret.")
    
    genai.configure(api_key=API_KEY)
    
    # Text generation model for the poem
    text_model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Image generation model
    # Note: As of mid-2024, direct image generation via API is often handled by specific models.
    # We will use Gemini to generate a *prompt* for an image, then use a free source for the image.
    # For a real-world high-quality image, you would use a dedicated image generation API.
    # Let's use the Unsplash API as a high-quality, free alternative.
    
    # 1. Generate the poem
    poem_prompt = f"Write a short, cryptic, and beautiful poem based on this idea: '{prompt}'. Do not include a title."
    poem_response = text_model.generate_content(poem_prompt)
    poem = poem_response.text

    # 2. Generate a search query for a high-quality image
    image_query_prompt = f"Based on the prompt '{prompt}', what is a one or two-word search term I could use to find a stunning, high-quality, atmospheric photograph on a site like Unsplash? Only return the search term."
    image_query_response = text_model.generate_content(image_query_prompt)
    search_term = image_query_response.text.strip()
    
    # 3. Fetch the image from a free source (Unsplash)
    # This gives us a new, high-quality, full-screen image every time.
    image_url = f"https://source.unsplash.com/1920x1080/?{search_term}"
    
    return poem, image_url, search_term

# --- File Operations ---
def update_json_file(new_dream):
    """Appends the new dream to the JSON file."""
    with open(JSON_FILE, 'r+') as f:
        data = json.load(f)
        data['dreams'].append(new_dream)
        f.seek(0) # Rewind to the start of the file
        json.dump(data, f, indent=4)

# --- Main Execution ---
if __name__ == "__main__":
    try:
        print("Skald is waking up...")
        prompt = generate_creative_prompt()
        print(f"Generated Prompt: {prompt}")

        poem, image_url, search_term = generate_art_and_poem(prompt)
        print(f"Found image for '{search_term}' and generated poem.")

        new_dream_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "prompt": prompt,
            "poem": poem.strip(),
            "image_url": image_url
        }

        update_json_file(new_dream_entry)
        print("A new dream has been recorded. Skald sleeps again.")
        
    except Exception as e:
        print(f"An error occurred: {e}")