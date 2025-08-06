# Gemini Dual Chat GUI

This is a Python-based desktop application that provides a dual chat interface for interacting with Google's Gemini AI models. It allows users to have two separate chat sessions running concurrently, each configurable with different Gemini models and parameters. The application supports sending text messages, attaching files, and features like auto-reply between the two chat instances, session saving/loading, and basic markdown rendering with optional code syntax highlighting.

## Features

- **Dual Chat Interface**: Interact with two Gemini models simultaneously.
- **Configurable Models**: Select different Gemini models for each chat session.
- **Adjustable Parameters**: Control `temperature` and `top_p` for each model.
- **System Prompts**: Set custom system prompts for each Gemini instance.
- **File Attachment**: Send local files as part of your prompts.
- **Auto-Reply**: Configure one Gemini instance to automatically reply to the other.
- **Session Management**: Save and load chat sessions, including history and settings.
- **Markdown Rendering**: Basic markdown support for responses.
- **Code Syntax Highlighting**: (Optional) If Pygments is installed, code blocks are syntax highlighted.
- **Token Usage Display**: Monitor token counts for each response and total tokens per session.
- **Conversation Logging**: All conversations are logged to text files.

## Setup and Installation

1.  **Clone the repository** (if applicable):
    ```bash
    git clone <repository_url>
    cd GeminiWindows
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    (Note: A `requirements.txt` file is assumed. If not present, you'll need to install `tkinter`, `customtkinter`, `google-generativeai`, `Pygments` (optional) manually.)
    
    Based on `main.py`, the key dependencies are:
    - `customtkinter`
    - `google-generativeai`
    - `Pygments` (optional, for syntax highlighting)

    You can install them using:
    ```bash
    pip install customtkinter google-generativeai Pygments
    ```

3.  **Obtain a Gemini API Key**:
    - Go to [Google AI Studio](https://aistudio.google.com/)
    - Generate an API key.

4.  **Configure API Key**:
    - The application will prompt you for your API key on first run.
    - Alternatively, you can manually edit `config.json` (which will be created on first run) and replace `"PASTE_YOUR_GEMINI_API_KEY_HERE"` with your actual API key.

## Usage

1.  **Run the application**:
    ```bash
    python main.py
    ```

2.  **Initial Setup**: On first run, you will be prompted to enter your Gemini API key. This will be saved to `config.json`.

3.  **Chat Interface**: The GUI will open with two chat panels. Each panel has:
    - A model selector dropdown.
    - Navigation buttons for Gemini responses.
    - Save/Load session buttons.
    - A chat display area.
    - A user input text box.
    - Send and Stop buttons.
    - An auto-reply checkbox.
    - Token usage information.

4.  **Options Tab**: Each chat panel has an "Options" tab where you can:
    - Set a system prompt.
    - Adjust `Temperature` and `Top-P` sliders.
    - Configure auto-reply delay.
    - Add/Remove files for attachment.
    - Save settings and reset the chat.

5.  **Sending Messages**: Type your message in the input box and press "Send" or `Ctrl+Enter`.

6.  **File Attachments**: Use the "Add Files" button in the "Options" tab to attach files to your next message.

7.  **Auto-Reply**: Check the "Auto-reply to Gemini X" checkbox to enable automatic responses between the two chat instances.

8.  **Session Management**: Use the "Save" and "Load" buttons to persist and retrieve chat sessions.

## Logging

All conversations are logged to the `logs` directory, with filenames indicating the chat ID and a timestamp (e.g., `gemini_1_full_YYYYMMDD_HHMMSS.txt`).

## Contributing

Feel free to fork the repository, make improvements, and submit pull requests.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
