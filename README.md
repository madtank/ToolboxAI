# ToolboxAI

ToolboxAI is a Streamlit application that leverages the [AWS Bedrock Converse Stream API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html) with Claude 3 and Claude 3.5, integrating powerful tool use capabilities for web search, web scraping, document analysis, and RSS feed parsing. This versatile AI assistant can process and analyze uploaded images and documents, provide insights and descriptions alongside its text-based interactions, and fetch the latest AI news from RSS feeds.

<img src="assets/icon.png" alt="ToolboxAI Logo" width="200" height="200">

## Key Features:

- Interactive chat interface powered by Claude 3 and Claude 3.5 via AWS Bedrock
- Seamless integration of web search and web scraping tools
- Image and document upload and analysis capabilities
- Real-time conversation streaming
- Token usage tracking for efficient management
- RSS feed parsing for up-to-date AI news
- Support for multiple Claude 3 and 3.5 models (Haiku, Sonnet, Opus)
- Flexible AWS region selection

With ToolboxAI, users can engage in rich, multimodal conversations that combine text-based queries, web information retrieval, visual/document content analysis, and the latest AI news from RSS feeds.

## Tool Use Demonstration

See ToolboxAI in action with this image from our demonstration:

<img src="assets/bedrock_tool_use.png" alt="Bedrock Tool Use" width="600"/>

## Image and Document Upload and Analysis

ToolboxAI supports both image and document uploads, allowing for more diverse and rich interactions with the AI:

- **Seamless File Integration**: Users can upload images and documents directly into the chat interface.
- **AI Content Analysis**: The AI can analyze and comment on uploaded files, providing insights and descriptions.
- **Flexible Format Support**: 
  - Images: PNG, JPG, JPEG, WebP

<img src="assets/image_upload.png" alt="Image Upload Feature" width="600"/>

  - Documents: PDF, CSV, DOC, DOCX, XLS, XLSX, HTML, TXT, MD

<img src="assets/file_upload.png" alt="File Upload Feature" width="600"/>

## RSS Feed Integration

ToolboxAI now includes RSS feed parsing capabilities, allowing users to fetch and interact with the latest AI news:

- **AI News Updates**: The AI can fetch and summarize recent AI news from TechCrunch's AI RSS feed.
- **Contextual Responses**: The AI integrates RSS feed information into its responses, providing up-to-date context for AI-related queries.
- **Expandable Feed Results**: Users can view detailed RSS feed results in an expandable section within the chat interface.

## Memory Management

ToolboxAI now includes a memory management feature using Chroma. This allows the AI to save important information from conversations and recall it later. The AI can use two new tools:

- `save_memory`: Saves important information for future recall.
- `recall_memories`: Retrieves relevant memories based on a query.

These tools enhance the AI's ability to maintain context across conversations and provide more informed responses.

### Note: On the first run, Chroma will download a pre-trained sentence transformer model (approximately 80MB). This is a one-time download and is necessary for the memory management feature to function properly. Subsequent runs will use the cached model.

## Prerequisites

- Python 3.9+
- AWS account with access to Bedrock
- Configured AWS credentials

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/madtank/ToolboxAI.git
   cd ToolboxAI
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Ensure your AWS credentials are properly configured.

## Running the Application

Launch the application with:

```
streamlit run main.py
```

This command starts the Streamlit server and opens the application in your default web browser.

## Using RSS Feed Functionality

To use the RSS feed feature:
1. Ask the AI about recent AI news or developments.
2. The AI will automatically use the RSS feed tool to fetch the latest articles from TechCrunch's AI feed.
3. The AI will summarize the news and provide links to the full articles.
4. You can expand the tool results to see more details about the fetched RSS entries.

## Application Structure

ToolboxAI consists of five main components:

1. `main.py`: Streamlit UI and main application loop
2. `src/bedrock_client.py`: AWS Bedrock service interactions
3. `src/conversation_handler.py`: AI response processing and conversation flow management
4. `src/utils.py`: Utility functions for various application needs, including RSS feed result formatting
5. `src/tools.py`: Tool-related functions and configurations for web search, scraping, and RSS feed parsing

## Customization

Extend ToolboxAI's capabilities by modifying `src/tools.py`. You can add new RSS feeds or other tools by updating the `toolConfig` dictionary and adding corresponding functions.

## Troubleshooting

If you encounter issues:

1. Verify your AWS credentials are correctly set up
2. Ensure all dependencies are properly installed
3. Check that you have the latest version of the code and have run `pip install -r requirements.txt` after any updates
4. Consult the Streamlit and AWS Bedrock documentation for service-specific troubleshooting

## Contributing

We welcome contributions to enhance ToolboxAI. Please follow the standard fork-and-pull request workflow for your submissions.

## License

ToolboxAI is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for full details.
