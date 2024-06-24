# Bedrock ConversAI Toolbox

Bedrock ConversAI Toolbox is a Streamlit-based application that leverages AWS Bedrock and Claude AI to provide an interactive chat interface with tool-use capabilities.

## Features

- Interactive chat interface powered by AWS Bedrock and Claude AI
- Dynamic tool use for web searches and web scraping
- Real-time token usage tracking
- Streamlit-based user interface for easy interaction

## Tool Use When Needed

To see `bedrock-conversai-toolbox` in action, check out this image from our demonstration:

![Bedrock Tool Use](assets/bedrock_tool_use.png)

## Prerequisites

Before running the application, ensure you have the following:

- Python 3.7 or higher
- AWS account with Bedrock access
- AWS CLI configured with appropriate credentials

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/madtank/bedrock-conversai-toolbox.git
   cd bedrock-conversai-toolbox
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Ensure your AWS CLI is configured with the correct credentials and region.

2. If necessary, update the `region_name` in the `create_bedrock_client()` function in `main.py` to match your AWS Bedrock endpoint region.

## Running the Application

To run the Bedrock ConversAI Toolbox:

```
streamlit run main.py
```

This will start the Streamlit server and open the application in your default web browser.

## File Structure

The application currently consists of two main files:

- `main.py`: Contains the Streamlit UI, main application logic, and conversation handling.
- `tools.py`: Contains tool-related functions (web search and web scraping) and configurations.

## Usage

1. Once the application is running, you'll see a chat interface.
2. Type your message in the input box and press Enter.
3. The AI will respond, and if necessary, it will use tools to gather additional information.
4. You can start a new chat at any time by clicking the "New Chat" button in the sidebar.
5. Token usage information is displayed in the sidebar after each AI response.

## Future Improvements

- Implement user authentication
- Add more tools and expand tool capabilities
- Create separate files for Bedrock client handling and conversation processing
- Implement error handling and logging
- Add unit tests for key functions

## Contributing

Contributions to Bedrock ConversAI Toolbox are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
