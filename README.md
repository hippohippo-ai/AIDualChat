# Gemini Dual Chat GUI

This is a Python-based desktop application that provides a dual chat interface for interacting with Google's Gemini AI models. It allows users to have two separate chat sessions running concurrently, each configurable with different Gemini models and parameters. The application supports sending text messages, attaching files, and features like auto-reply between the two chat instances, session saving/loading, and basic markdown rendering with optional code syntax highlighting.

## Recent Changes

- **Fix: Gemini Prefix and Message Spacing**: The "Gemini X" prefix now appears at the beginning of the response stream, and the spacing between messages has been corrected to ensure each message appears on a new line.

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

---

# Gemini 双聊天 GUI (Mandarin)

这是一个基于 Python 的桌面应用程序，提供了一个用于与 Google 的 Gemini AI 模型进行交互的双聊天界面。它允许用户同时运行两个独立的聊天会话，每个会话都可以配置不同的 Gemini 模型和参数。该应用程序支持发送短信、附加文件，并具有在两个聊天实例之间自动回复、会话保存/加载以及带有可选代码语法高亮的基本 markdown 渲染等功能。

## 最近更新

- **修复：Gemini 前缀和消息间距**：“Gemini X” 前缀现在会出现在响应流的开头，并且消息之间的间距已得到纠正，以确保每条消息都显示在新行上。

## 功能

- **双聊天界面**：同时与两个 Gemini 模型进行交互。
- **可配置模型**：为每个聊天会话选择不同的 Gemini 模型。
- **可调参数**：控制每个模型的 `temperature` 和 `top_p`。
- **系统提示**：为每个 Gemini 实例设置自定义系统提示。
- **文件附件**：发送本地文件作为提示的一部分。
- **自动回复**：配置一个 Gemini 实例以自动回复另一个实例。
- **会话管理**：保存和加载聊天会话，包括历史记录和设置。
- **Markdown 渲染**：响应的基本 markdown 支持。
- **代码语法高亮**：（可选）如果安装了 Pygments，代码块将进行语法高亮。
- **令牌使用情况显示**：监控每个响应的令牌计数和每个会話的总令牌。
- **对话日志记录**：所有对话都记录到文本文件中。

## 设置和安装

1.  **克隆存储库**（如果适用）：
    ```bash
    git clone <repository_url>
    cd GeminiWindows
    ```

2.  **安装依赖项**：
    ```bash
    pip install -r requirements.txt
    ```
    （注意：假设存在 `requirements.txt` 文件。如果不存在，您需要手动安装 `tkinter`、`customtkinter`、`google-generativeai`、`Pygments`（可选）。）
    
    根据 `main.py`，关键依赖项是：
    - `customtkinter`
    - `google-generativeai`
    - `Pygments`（可选，用于语法高亮）

    您可以使用以下命令安装它们：
    ```bash
    pip install customtkinter google-generativeai Pygments
    ```

3.  **获取 Gemini API 密钥**：
    - 前往 [Google AI Studio](https://aistudio.google.com/)
    - 生成一个 API 密钥。

4.  **配置 API 密钥**：
    - 应用程序将在首次运行时提示您输入 API 密钥。
    - 或者，您可以手动编辑 `config.json`（将在首次运行时创建）并将 `"PASTE_YOUR_GEMINI_API_KEY_HERE"` 替换为您的实际 API 密钥。

## 用法

1.  **运行应用程序**：
    ```bash
    python main.py
    ```

2.  **初始设置**：首次运行时，系统将提示您输入 Gemini API 密钥。该密钥将保存到 `config.json`。

3.  **聊天界面**：GUI 将打开，其中包含两个聊天面板。每个面板都有：
    - 模型选择器下拉列表。
    - Gemini 响应的导航按钮。
    - 保存/加载会话按钮。
    - 聊天显示区域。
    - 用户输入文本框。
    - 发送和停止按钮。
    - 自动回复复选框。
    - 令牌使用信息。

4.  **选项卡**：每个聊天面板都有一个“选项”选项卡，您可以在其中：
    - 设置系统提示。
    - 调整 `Temperature` 和 `Top-P` 滑块。
    - 配置自动回复延迟。
    - 添加/删除要附加的文件。
    - 保存设置并重置聊天。

5.  **发送消息**：在输入框中键入您的消息，然后按“发送”或 `Ctrl+Enter`。

6.  **文件附件**：使用“选项”选项卡中的“添加文件”按钮将文件附加到您的下一条消息中。

7.  **自动回复**：选中“自动回复 Gemini X”复选框以启用两个聊天实例之间的自动响应。

8.  **会话管理**：使用“保存”和“加载”按钮来持久化和检索聊天会话。

## 日志记录

所有对话都记录到 `logs` 目录中，文件名指示聊天 ID 和时间戳（例如，`gemini_1_full_YYYYMMDD_HHMMSS.txt`）。

## 贡献

欢迎 fork 存储库，进行改进并提交拉取请求。

## 许可证

该项目根据 MIT 许可证获得许可 - 有关详细信息，请参阅 `LICENSE` 文件。