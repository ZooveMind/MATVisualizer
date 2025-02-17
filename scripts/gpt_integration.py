import json
import base64
import os
from openai import OpenAI

# OpenAI API Key (Replace with your key)
OPENAI_API_KEY = "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"
client = OpenAI(api_key=OPENAI_API_KEY)

RESULT_FOLDER = 'static/images'
os.makedirs(RESULT_FOLDER, exist_ok=True)

def send_to_gpt(data):
    """ Sends structured data to GPT for visualization suggestions """
    prompt = f"""
    You are an expert Data Analyst. Given the following `.mat` file data, generate structured insights and data visualizations.

    **Instructions**:
    - Perform **data profiling**: list all variables, types, missing values.
    - Compute **mean, median, std, min, max** for numeric variables.
    - Generate **visualizations** (scatter, heatmap, histogram, etc.).
    - Return images as **base64-encoded PNGs**.

    **Data**:
    ```json
    {json.dumps(data)}
    ```

    **Expected JSON Response**:
    ```json
    {{
        "summary": {{
            "variables": {{
                "var1": {{"type": "numeric", "mean": 5.2, "std": 1.4}},
                "var2": {{"type": "categorical", "categories": {{"A": 100, "B": 50}}}}
            }},
            "correlations": {{"var1": {{"var2": 0.87}}}}
        }},
        "visualizations": [
            {{"type": "histogram", "image": "base64_encoded_image"}},
            {{"type": "scatter_plot", "image": "base64_encoded_image"}}
        ]
    }}
    ```

    Return a JSON object with **summary + visualizations**.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )

    return json.loads(response["choices"][0]["message"]["content"])

def save_visualizations(visualizations):
    """ Decodes base64 images and saves them as PNG files """
    saved_images = []
    for i, vis in enumerate(visualizations):
        img_data = base64.b64decode(vis["image"])
        img_path = os.path.join(RESULT_FOLDER, f"plot_{i}.png")
        with open(img_path, "wb") as img_file:
            img_file.write(img_data)
        saved_images.append(f"/{img_path}")
    return saved_images
