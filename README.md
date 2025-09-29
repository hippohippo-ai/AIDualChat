# Gemini Dual Chat GUI

A Python-based desktop application for interacting with Google's Gemini AI models. This tool provides a dual-chat environment where users can manage two concurrent Gemini instances, configure their behaviors, and facilitate an auto-reply interaction between them.

![Application Snapshot](example/2025-09-29%2008_44_16-Clipboard.png)

## Features

- **Dual Chat Interface**: Interact with two Gemini models simultaneously in a clean, tabbed interface.
- **Raw Text View**: Each chat has a corresponding "Raw" tab that displays the conversation in plain text, without any markdown formatting, for clarity and debugging.
- **Rich Configuration**: Independently configure each agent's model, system instructions, and generation parameters (temperature, etc.).
- **Auto-Reply Functionality**: Enable one agent to automatically reply to the other, allowing for continuous conversations. The delay between replies is configurable.
- **File Attachments**: Attach and send local files (text, images, etc.) to the models.
- **Session Management**: Save and load the complete state of an agent (model, system prompt, history) to a JSON file.
- **Real-time Token Counts**: Monitor token usage for the last turn and the total session for each agent.
- **Improved Markdown Rendering**: Responses are rendered with improved markdown support for headings, blockquotes, code blocks, bold, italic, and strikethrough text, using inline styles for better compatibility with the display component.
- **Fixed Doubled Input**: Resolved an issue where user input messages would sometimes appear twice in the chat display.
- **Robust Gemini API Content Handling**: Improved the internal handling of message objects from the Gemini API for more stable chat history management.
- **Separated Conversation Logging**: All interactions for each agent are automatically saved to a separate, timestamped session log file.
- **UI Conveniences**: Features collapsible sidebars (left sidebar collapsed by default) and a configurable minimum window size (1000x800) for a better user experience.

## Known Issues

- **Text Selection**: Due to limitations of the `tkhtmlview.HTMLLabel` component, selecting and copying text directly from the chat display may not work reliably.

---

## 已知问题

- **文本选择**: 由于 `tkhtmlview.HTMLLabel` 组件的限制，直接从聊天显示中选择和复制文本可能无法可靠工作。

## Setup and Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd GeminiWindows
    ```

2.  **Install dependencies**:
    The application relies on a few key libraries. You can install them using pip:
    ```bash
    pip install customtkinter google-generativeai
    ```

3.  **Obtain a Gemini API Key**:
    - Go to [Google AI Studio](https://aistudio.google.com/).
    - Click "Get API key" and generate a new key.

4.  **Configure API Key**:
    - Run the application for the first time. It will prompt you to enter your API key.
    - The key is saved in a `config.json` file that is created automatically. You can also edit this file directly to change the key.

## Usage

1.  **Run the application**:
    ```bash
    python main.py
    ```

2.  **Initial Setup**: On the first run, enter your Gemini API key when prompted.

3.  **Main Interface**:
    - **Left Sidebar (Studio)**: Collapsed by default. Contains session management controls like "New Session", "Save", and "Load" for each Gemini agent.
    - **Central Area (Chat)**: A tabbed view for "Gemini 1", "Gemini 2", and their corresponding "Raw" text views.
    - **Right Sidebar (Configuration)**: Allows you to select models, set the auto-reply delay, and configure each Gemini agent's system prompt and parameters.

4.  **Configuring Agents**:
    - Use the right sidebar to select a model for each Gemini agent.
    - Expand the "Gemini X Settings" panel to write custom system instructions and adjust the temperature.
    - Click "Save & Reset Session" to apply your changes. This will start a new session for that agent with the new settings.

5.  **Interacting with Agents**:
    - Type a message in an agent's input box and click "Send" or press `Ctrl+Enter`.
    - To have one agent automatically respond to the other, check the "Auto-reply" box in the sender's control area.
    - **Stop Generation**: You can stop any ongoing generation by clicking the "Stop" button.

## Logging

All conversations for each agent are saved into separate log files in the `logs` directory. The filename is based on the session start time and the agent ID (e.g., `session_20231027_143000_gemini_1.txt`).

## Contributing

Feel free to fork the repository, make improvements, and submit pull requests.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

---

# Gemini 双聊天 GUI (Mandarin)

一个基于 Python 的桌面应用程序，用于与 Google 的 Gemini AI 模型进行交互。该工具提供了一个双聊天环境，用户可以在其中管理两个并发的 Gemini 实例，配置它们的行为，并启用它们之间的自动回复交互。

![Application Snapshot](example/2025-09-29%2008_44_16-Clipboard.png)

## 功能

- **双聊天界面**: 在一个整洁的标签页界面中同时与两个 Gemini 模型进行交互。
- **原始文本视图**: 每个聊天都有一个对应的“Raw”标签页，以纯文本形式显示对话，没有任何 Markdown 格式，便于清晰阅读和调试。
- **丰富的配置**: 独立配置每个智能体的模型、系统指令和生成参数（如温度等）。
- **自动回复功能**: 启用一个智能体自动回复另一个，允许进行连续对话。回复之间的延迟是可配置的。
- **文件附件**: 将本地文件（文本、图像等）附加并发送到模型。
- **会话管理**: 将智能体的完整状态（模型、系统提示、历史记录）保存和加载到 JSON 文件。
- **实时令牌计数**: 监控每个智能体上一轮和整个会话的令牌使用情况。
- **改进的 Markdown 渲染**: 响应以改进的 Markdown 格式呈现，支持标题、引用块、代码块、粗体、斜体和删除线文本，使用内联样式以更好地兼容显示组件。
- **修复了重复输入问题**: 解决了用户输入消息有时会在聊天显示中出现两次的问题。
- **健壮的 Gemini API 内容处理**: 改进了 Gemini API 消息对象的内部处理，以实现更稳定的聊天历史管理。
- **分离的对话日志**: 每个智能体的所有交互都会自动保存到一个独立的、带时间戳的会话日志文件中。
- **界面便利功能**: 具有可折叠的侧边栏（左侧边栏默认折叠）和可配置的最小窗口尺寸（1000x800），以提供更好的用户体验。

## 设置与安装

1.  **克隆存储库**:
    ```bash
    git clone <repository_url>
    cd GeminiWindows
    ```

2.  **安装依赖项**:
    该应用程序依赖于一些关键库。您可以使用 pip 安装它们：
    ```bash
    pip install customtkinter google-generativeai
    ```

3.  **获取 Gemini API 密钥**:
    - 前往 [Google AI Studio](https://aistudio.google.com/)。
    - 点击 “Get API key” 并生成一个新的密钥。

4.  **配置 API 密钥**:
    - 首次运行应用程序。它会提示您输入 API 密钥。
    - 密钥保存在自动创建的 `config.json` 文件中。您也可以直接编辑此文件来更改密钥。

## 使用方法

1.  **运行应用程序**:
    ```bash
    python main.py
    ```

2.  **初始设置**: 首次运行时，根据提示输入您的 Gemini API 密钥。

3.  **主界面**:
    - **左侧边栏 (Studio)**: 默认折叠。包含会话管理控件，如“New Session”、“Save”和“Load”等，用于每个 Gemini 智能体。
    - **中央区域 (Chat)**: 一个标签页视图，包含“Gemini 1”、“Gemini 2”及其对应的“Raw”原始文本视图。
    - **右侧边栏 (Configuration)**: 允许您选择模型，设置自动回复延迟，并配置每个 Gemini 智能体的系统提示和参数。

4.  **配置智能体**:
    - 使用右侧边栏为每个 Gemini 智能体选择一个模型。
    - 展开 “Gemini X Settings” 面板以编写自定义系统指令并调整温度。
    - 点击 “Save & Reset Session” 以应用您的更改。这将为该智能体使用新设置启动一个新会话。

5.  **与智能体交互**:
    - 在智能体的输入框中输入消息，然后单击“Send”或按 `Ctrl+Enter`。
    - 要让一个智能体自动响应另一个，请在发送方的控制区域中勾选“Auto-reply”复选框。
    - **停止生成**: 您可以随时通过单击“Stop”按钮停止任何正在进行的生成。

## 日志记录

每个智能体的所有对话都保存在 `logs` 目录下的独立日志文件中。文件名基于会话开始时间和智能体 ID（例如，`session_20231027_143000_gemini_1.txt`）。

## 贡献

欢迎 fork 存储库，进行改进并提交拉取请求。

## 许可证

该项目根据 MIT 许可证获得许可 - 有关详细信息，请参阅 `LICENSE` 文件。