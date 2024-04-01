import os
from datetime import datetime
import time
import re
import google.generativeai as genai
from google.api_core import exceptions, retry
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the API key from the environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Define the models with descriptions
MODELS = {
    "gemini-1.5-pro-latest": {
        "model": genai.GenerativeModel("gemini-1.5-pro-latest"),
        "description": "Powerful model capable of handling text and image inputs, optimized for various language tasks like code generation, text editing, and problem solving.",
        "rate_limit": (2, 60),  # 2 queries per minute
        "daily_limit": 1000,
    },
    "gemini-1.0-pro-latest": {
        "model": genai.GenerativeModel("gemini-1.0-pro-latest"),
        "description": "Versatile model for text generation and multi-turn conversations, suitable for zero-shot, one-shot, and few-shot tasks.",
        "rate_limit": (60, 60),  # 60 queries per minute
    },
}

# For convenience, a simple wrapper to let the SDK handle error retries
# Added specific exception handling


@retry.Retry(
    initial=0.1,
    maximum=60.0,
    multiplier=2.0,
    deadline=600.0,
    exceptions=(exceptions.GoogleAPICallError,),
)
def generate_with_retry(model, prompt):
    try:
        return model.generate_content(prompt)
    except exceptions.InvalidArgument as e:
        raise ValueError(f"Invalid input provided: {e}")
    except exceptions.DeadlineExceeded as e:
        raise exceptions.DeadlineExceeded(
            f"Deadline exceeded while generating content: {e}")
    except exceptions.ResourceExhausted as e:
        raise exceptions.ResourceExhausted(
            f"Resource exhausted (quota limit reached): {e}")

# Prompts


def get_persona():
    print("Persona Options:")
    print("1. Award-winning science fiction author")
    print("2. Bestselling mystery novelist")
    print("3. Acclaimed fantasy writer")
    print("4. Custom persona")
    choice = input(
        "Enter the number corresponding to your desired persona (1-4): ")
    if choice == "1":
        return """
        You are an award-winning science fiction author with a penchant for expansive,
        intricately woven stories. Your ultimate goal is to write the next award-winning
        sci-fi novel.
        """
    elif choice == "2":
        return """
        You are a bestselling mystery novelist known for crafting intricate plots and
        suspenseful narratives. Your aim is to keep readers guessing until the very end.
        """
    elif choice == "3":
        return """
        You are an acclaimed fantasy writer with a talent for creating immersive worlds
        and compelling characters. Your goal is to transport readers to realms of magic
        and adventure.
        """
    elif choice == "4":
        return input("Enter your custom persona description: ")
    else:
        print("Invalid choice. Using the default science fiction author persona.")
        return """
        You are an award-winning science fiction author with a penchant for expansive,
        intricately woven stories. Your ultimate goal is to write the next award-winning
        sci-fi novel.
        """


def get_writing_guidelines():
    print("Writing Guideline Options:")
    print("1. Default guidelines")
    print("2. Descriptive and immersive")
    print("3. Fast-paced and action-oriented")
    print("4. Custom guidelines")
    choice = input(
        "Enter the number corresponding to your desired writing guidelines (1-4): ")
    if choice == "1":
        return """
        Writing Guidelines:
        Delve deeper. Lose yourself in the world you're building. Unleash vivid
        descriptions to paint the scenes in your reader's mind. Develop your
        characters—let their motivations, fears, and complexities unfold naturally.
        Weave in the threads of your outline, but don't feel constrained by it. Allow
        your story to surprise you as you write. Use rich imagery, sensory details, and
        evocative language to bring the setting, characters, and events to life.
        Introduce elements subtly that can blossom into complex subplots, relationships,
        or world building details later in the story. Keep things intriguing but not
        fully resolved. Avoid boxing the story into a corner too early. Plant the seeds
        of subplots or potential character arc shifts that can be expanded later.
        Remember, your main goal is to write as much as you can. If you get through
        the story too fast, that is bad. Expand, never summarize.
        """
    elif choice == "2":
        return """
        Writing Guidelines:
        Focus on creating a rich and immersive story world. Use vivid descriptions to
        engage the reader's senses and bring the setting to life. Develop complex
        characters with distinct personalities, motivations, and backstories. Explore
        their relationships, conflicts, and growth throughout the story. Use evocative
        language and sensory details to create a strong sense of atmosphere and mood.
        Take your time to build the world and establish the rules and history that
        govern it. Encourage the reader to lose themselves in the story and become
        fully invested in the characters and their journeys.
        """
    elif choice == "3":
        return """
        Writing Guidelines:
        Prioritize fast-paced action and keep the story moving forward. Use short,
        punchy sentences to create a sense of urgency and excitement. Focus on
        dynamic dialogue and intense action sequences to keep the reader engaged.
        Develop characters through their actions and reactions to high-stakes
        situations. Use cliffhangers and plot twists to maintain suspense and keep
        the reader guessing. Avoid lengthy descriptions or exposition that may slow
        down the pace. Aim for a tight, focused narrative that keeps the reader on
        the edge of their seat from start to finish.
        """
    elif choice == "4":
        return input("Enter your custom writing guidelines: ")
    else:
        print("Invalid choice. Using the default writing guidelines.")
        return """
        Writing Guidelines:
        Delve deeper. Lose yourself in the world you're building. Unleash vivid
        descriptions to paint the scenes in your reader's mind. Develop your
        characters—let their motivations, fears, and complexities unfold naturally.
        Weave in the threads of your outline, but don't feel constrained by it. Allow
        your story to surprise you as you write. Use rich imagery, sensory details, and
        evocative language to bring the setting, characters, and events to life.
        Introduce elements subtly that can blossom into complex subplots, relationships,
        or world building details later in the story. Keep things intriguing but not
        fully resolved. Avoid boxing the story into a corner too early. Plant the seeds
        of subplots or potential character arc shifts that can be expanded later.
        Remember, your main goal is to write as much as you can. If you get through
        the story too fast, that is bad. Expand, never summarize.
        """


def get_user_input(prompt):
    return input(prompt)


def write_story(model_name):
    model_config = MODELS[model_name]
    model = model_config["model"]
    rate_limit = model_config.get("rate_limit")
    daily_limit = model_config.get("daily_limit")

    persona = get_persona()
    guidelines = get_writing_guidelines()

    premise_prompt = f"""
    {persona}
    Write a single sentence premise for a sci-fi story featuring cats.
    """
    premise = generate_with_retry(model, premise_prompt).text
    print("Generated Premise:")
    print(premise)

    outline_prompt = f"""
    {persona}
    You have a gripping premise in mind:
    {premise}
    Write an outline for the plot of your story.
    """
    outline = generate_with_retry(model, outline_prompt).text
    print("Generated Outline:")
    print(outline)

    # Generate and save title
    title_prompt = f"""
    {persona}
    Generate a single captivating title for your story based on the premise:
    {premise}
    
    Provide the title in the following format:
    Title: <title>
    """
    title_text = generate_with_retry(model, title_prompt).text.strip()
    print("Generated Title:")
    print(title_text)

    # Extract the title from the generated text
    title_match = re.search(r"Title: (.*)", title_text, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
    else:
        # Fallback to extracting the first line as the title
        lines = title_text.split("\n")
        if lines:
            title = lines[0].strip()
        else:
            # Fallback to a default title if no title is found
            title = "Untitled"

    starting_prompt = f"""
    {persona}
    You have a gripping premise in mind:
    {premise}
    Your imagination has crafted a rich narrative outline:
    {outline}
    First, silently review the outline and the premise. Consider how to start the
    story.
    Start to write the very beginning of the story. You are not expected to finish
    the whole story now. Your writing should be detailed enough that you are only
    scratching the surface of the first bullet of your outline. Try to write AT
    MINIMUM 1000 WORDS.
    {guidelines}
    """

    # Continuation prompt with summary
    continuation_prompt = f"""
    {persona}
    You have a gripping premise in mind:
    {premise}
    Your imagination has crafted a rich narrative outline:
    {outline}
    Here's a summary of what you've written so far:
    {{story_summary}}
    =====
    Continue writing the story from where you left off. Focus on the next part of your outline.
    Aim for at least 1000 words, but only write "IAMDONE" when the story is completely finished.
    {guidelines}
    """

    # Create a directory for the story and its parts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    story_dir = f"story_{timestamp}"
    os.makedirs(story_dir, exist_ok=True)

    # Extract text from response more robustly
    def extract_text(response):
        for part in response.parts:
            if hasattr(part, "text"):  # Check if the "text" attribute exists
                return part.text  # Access the text attribute using dot notation
        return ""  # Return empty string if no text part is found

    starting_draft = extract_text(generate_with_retry(model, starting_prompt))
    print("Starting Draft:")
    print(starting_draft)

    # Save starting draft
    starting_draft_filename = f"{story_dir}/starting_draft.txt"
    with open(starting_draft_filename, "w", encoding="utf-8") as file:
        file.write(starting_draft)

    draft = starting_draft

    # Update continuation extraction as well
    continuation = extract_text(generate_with_retry(
        model, continuation_prompt.format(story_summary="")))
    print("Continuation:")
    print(continuation)

    draft = draft + "\n\n" + continuation

    query_count = 1

    # Maximum iteration limit to prevent infinite loop
    max_iterations = 20

    for i in range(max_iterations):
        if "IAMDONE" in continuation:
            break

        if rate_limit:
            if query_count % rate_limit[0] == 0:
                time.sleep(rate_limit[1])

        if daily_limit and query_count >= daily_limit:
            print("Daily query limit reached. Please try again tomorrow.")
            break

        try:
            continuation = extract_text(generate_with_retry(
                model, continuation_prompt.format(story_summary=draft)))
        except exceptions.InvalidArgument as e:
            print(f"Invalid input provided: {e}")
            break
        except exceptions.DeadlineExceeded as e:
            print(f"Deadline exceeded while generating content: {e}")
            break
        except exceptions.ResourceExhausted as e:
            print(f"Resource exhausted (quota limit reached): {e}")
            break

        # Save each continuation
        continuation_filename = f"{story_dir}/continuation_{i+1}.txt"
        with open(continuation_filename, "w", encoding="utf-8") as file:
            file.write(continuation)

        draft = draft + "\n\n" + continuation
        query_count += 1

    final = draft.replace("IAMDONE", "").strip()
    print("Final Story:")
    print(final)

    # Sanitize title for filename
    def sanitize_title(title):
        # Replace invalid characters with underscores
        sanitized_title = re.sub(r"[^\w\-_\. ]", "_", title)
        # Limit the title length to a maximum of 100 characters
        sanitized_title = sanitized_title[:100]
        return sanitized_title

    # Save final story with sanitized title
    final_filename = f"{story_dir}/{sanitize_title(title)}.txt"
    with open(final_filename, "w", encoding="utf-8") as file:
        file.write(final)

    print(f"Final story saved to {final_filename}")


# Prompt the user to choose a model
print("Available models:")
for i, (model_name, model_info) in enumerate(MODELS.items(), start=1):
    print(f"{i}. {model_name} - {model_info['description']}")

while True:
    try:
        choice = int(
            input("Enter the number corresponding to the model you want to use: "))
        if 1 <= choice <= len(MODELS):
            selected_model = list(MODELS.keys())[choice - 1]
            break
        else:
            print("Invalid choice. Please enter a valid number.")
    except ValueError:
        print("Invalid input. Please enter a valid number.")

write_story(selected_model)
