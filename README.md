# Weather AI

This is a Python program that uses natural language processing to understand a user's question about the weather and then fetches the answer from a weather API.

## Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Download spaCy model:**
    ```bash
    python -m spacy download en_core_web_sm
    ```

3.  **Get an API Key:**
    Sign up for a free API key from [OpenWeatherMap](https://openweathermap.org/api).

4.  **Set Environment Variable:**
    Create a `.env` file in the root of the project and add your API key like this:
    ```
    OPENWEATHERMAP_API_KEY=your_api_key_here
    ```

## Usage

To run the application, use the following command:

```bash
python main.py
```
You can then type your weather-related questions directly into the console.
