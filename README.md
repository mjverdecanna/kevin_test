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

There are two ways to run this application:

### 1. GUI Mode (with Voice Input/Output)

To run the application with a graphical user interface and voice controls, run the following command:

```bash
python gui.py
```
Press the "Press to Talk" button to ask your weather question. The bot will listen, process your request, and then speak the answer.

### 2. Console Mode (Text-based)

If you prefer to use the command line, you can run the original text-based version:

```bash
python main.py
```
