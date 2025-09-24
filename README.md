# Gemini Multi-Agent Chat GUI

A Python-based desktop application for interacting with Google's Gemini AI models. This tool provides a multi-agent chat environment where users can manage two concurrent Gemini instances, configure their behaviors, and facilitate different modes of interaction between them.

## What's New in v3

- **Complete UI Overhaul**: The application now features a modern, three-column layout with collapsible sidebars for session management and configuration, providing a more organized and intuitive user experience.
- **Interaction Modes**: A major new feature allowing for advanced agent workflows:
    - **Focus Mode**: Standard mode for sending prompts to either of the two Gemini agents independently.
    - **Chained Mode**: The output from Gemini 1 is automatically used as the input prompt for Gemini 2, creating a sequential processing chain.
    - **Debate Mode**: The two agents interact with each other continuously based on an initial user prompt, with a configurable delay.
- **Enhanced Configuration**: A `config.json` file now stores default models, preferred model lists for dropdowns, system prompts, and generation parameters for each agent.
- **Improved Session Management**: The UI now includes dedicated buttons for starting a new session, saving the state of an individual agent, or loading a session from a file.
- **Robust Error Handling**: The application now automatically handles API rate limit errors (429) by waiting for the recommended duration and retrying the request.

## Features

- **Multi-Agent Interface**: Interact with two Gemini models simultaneously in various modes.
- **Flexible Interaction Modes**: Choose between Focus, Chained, and Debate modes.
- **Rich Configuration**: Independently configure each agent's model, system instructions, temperature, and more.
- **File Attachments**: Attach and send local files (text, images, etc.) to the models.
- **Session Management**: Save and load the complete state of an agent (model, system prompt, history) to a JSON file.
- **Real-time Token Counts**: Monitor token usage for the last turn and the total session for each agent.
- **Markdown Rendering**: Responses are rendered with basic markdown for bold and italic text.
- **Conversation Logging**: All interactions are automatically saved to a timestamped session log file.
- **Collapsible Sidebars**: Maximize screen real estate for the chat display by collapsing the side panels.

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
    - **Left Sidebar (Studio)**: Contains session management controls like "New Session", "Save", and "Load" for each Gemini agent.
    - **Central Area (Chat)**: Displays the conversation. At the bottom, you'll find the user input box and the "Interaction Mode" selector.
    - **Right Sidebar (Configuration)**: Allows you to select models, set the auto-reply delay for chained/debate modes, and configure each Gemini agent's system prompt and parameters.

4.  **Configuring Agents**:
    - Use the right sidebar to select a model for each Gemini agent.
    - Expand the "Gemini X Settings" panel to write custom system instructions and adjust the temperature.
    - Click "Save & Reset Session" to apply your changes. This will start a new session for that agent with the new settings.

5.  **Interacting with Agents**:
    - **Select a Mode**: Choose "Focus Mode", "Chained Mode", or "Debate Mode" from the dropdown above the input box.
    - **Focus Mode**: Type a message and click "To G1" or "To G2" to send it to the corresponding agent.
    - **Chained Mode**: Type a message and click "Start Chain". The prompt will be sent to Gemini 1, and its response will be sent to Gemini 2.
    - **Debate Mode**: Type an initial topic or question and click "Start Debate". The agents will respond to each other until you click "Stop".
    - **Stop Generation**: You can stop any ongoing generation by clicking the "Stop" button.

## Logging

All conversations from a single run of the application are saved into a single log file in the `logs` directory. The filename is based on the session start time (e.g., `session_20231027_143000.txt`).

## Contributing

Feel free to fork the repository, make improvements, and submit pull requests.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

---

# Gemini 多智能体聊天 GUI (Mandarin)

一个基于 Python 的桌面应用程序，用于与 Google 的 Gemini AI 模型进行交互。该工具提供了一个多智能体聊天环境，用户可以在其中管理两个并发的 Gemini 实例，配置它们的行为，并促进它们之间不同模式的交互。

## v3 版本更新内容

- **全新的 UI 大修**：应用程序现在采用现代化的三栏布局，带有可折叠的侧边栏，用于会话管理和配置，提供了更有条理和直观的用户体验。
- **交互模式**：一个主要的新功能，允许高级的智能体工作流程：
    - **专注模式 (Focus Mode)**：将提示独立发送给两个 Gemini 智能体之一的标准模式。
    - **链式模式 (Chained Mode)**：Gemini 1 的输出自动用作 Gemini 2 的输入提示，创建一个顺序处理链。
    - **辩论模式 (Debate Mode)**：两个智能体根据用户的初始提示，以可配置的延迟时间连续进行相互交互。
- **增强的配置**：`config.json` 文件现在存储默认模型、下拉菜单的偏好模型列表、系统提示以及每个智能体的生成参数。
- **改进的会话管理**：UI 现在包含用于启动新会话、保存单个智能体状态或从文件加载会话的专用按钮。
- **强大的错误处理**：应用程序现在通过等待建议的持续时间并重试请求来自动处理 API 速率限制错误 (429)。

## 功能

- **多智能体界面**：以各种模式同时与两个 Gemini 模型进行交互。
- **灵活的交互模式**：在专注、链式和辩论模式之间进行选择。
- **丰富的配置**：独立配置每个智能体的模型、系统指令、温度等。
- **文件附件**：将本地文件（文本、图像等）附加并发送到模型。
- **会话管理**：将智能体的完整状态（模型、系统提示、历史记录）保存和加载到 JSON 文件。
- **实时令牌计数**：监控每个智能体上一轮和整个会话的令牌使用情况。
- **Markdown 渲染**：响应以基本的 Markdown 格式呈现粗体和斜体文本。
- **对话日志**：所有交互都会自动保存到带时间戳的会话日志文件中。
- **可折叠侧边栏**：通过折叠侧面板，最大化聊天显示区的屏幕空间。

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
    - **左侧边栏 (Studio)**: 包含会话管理控件，如“New Session”、“Save”和“Load”等，用于每个 Gemini 智能体。
    - **中央区域 (Chat)**: 显示对话。在底部，您会找到用户输入框和“交互模式”选择器。
    - **右侧边栏 (Configuration)**: 允许您选择模型，设置链式/辩论模式的自动回复延迟，并配置每个 Gemini 智能体的系统提示和参数。

4.  **配置智能体**:
    - 使用右侧边栏为每个 Gemini 智能体选择一个模型。
    - 展开 “Gemini X Settings” 面板以编写自定义系统指令并调整温度。
    - 点击 “Save & Reset Session” 以应用您的更改。这将为该智能体使用新设置启动一个新会话。

5.  **与智能体交互**:
    - **选择模式**: 从输入框上方的下拉菜单中选择“Focus Mode”、“Chained Mode”或“Debate Mode”。
    - **专注模式**: 输入消息，然后单击“To G1”或“To G2”将其发送到相应的智能体。
    - **链式模式**: 输入消息，然后单击“Start Chain”。提示将发送到 Gemini 1，其响应将发送到 Gemini 2。
    - **辩论模式**: 输入一个初始主题或问题，然后单击“Start Debate”。智能体将相互响应，直到您单击“Stop”。
    - **停止生成**: 您可以随时通过单击“Stop”按钮停止任何正在进行的生成。

## 日志记录

单次运行应用程序的所有对话都保存在 `logs` 目录下的单个日志文件中。文件名基于会话开始时间（例如，`session_20231027_143000.txt`）。

## 贡献

欢迎 fork 存储库，进行改进并提交拉取请求。

## 许可证

该项目根据 MIT 许可证获得许可 - 有关详细信息，请参阅 `LICENSE` 文件。
