# Converse API - Tools Application

This Streamlit application demonstrates the use of the AWS Bedrock Converse API with Claude 3, incorporating tool use capabilities for web search and web scraping.

## Tool Use When Needed

To see `bedrock-conversai-toolbox` in action, check out this image from our demonstration:

![Bedrock Tool Use](assets/bedrock_tool_use.png)

## Prerequisites

- Python 3.9+
- AWS account with access to Bedrock
- Configured AWS credentials

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/madtank/bedrock-conversai-toolbox.git

   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Ensure your AWS credentials are properly configured.

## Running the Application

To run the application, use the following command:

```
streamlit run main.py
```

This will start the Streamlit server and open the application in your default web browser.

## Features

- Interactive chat interface with Claude 3 via AWS Bedrock
- Integration of web search and web scraping tools
- Real-time conversation streaming
- Token usage tracking

## Application Structure

The application now consists of five main files:

1. `main.py`: Contains the Streamlit UI and the main application loop.
2. `src/bedrock_client.py`: Handles interactions with the AWS Bedrock service.
3. `src/conversation_handler.py`: Manages AI response processing and conversation flow.
4. `src/utils.py`: Contains utility functions used across the application.
5. `src/tools.py`: Contains tool-related functions (web search and web scraping) and configurations.

## Customization

To add new tools or modify existing ones, update the `tools.py` file. Ensure to update the `toolConfig` dictionary with any new tools you add.

## Troubleshooting

If you encounter any issues:

1. Verify your AWS credentials are correctly set up.
2. Ensure all dependencies are installed correctly.
3. Check the Streamlit and AWS Bedrock documentation for any service-specific issues.

## Contributing

Contributions to improve the application are welcome. Please follow the standard fork-and-pull request workflow.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.