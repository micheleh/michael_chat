# Michael's Chat

A ChatGPT-like single-page application (SPA) with a Python backend that serves a React frontend. The application provides a modern chat interface with configuration options for different AI APIs.

## Features

- 🤖 ChatGPT-like chat interface
- ⚙️ Configuration screen for API settings
- 🔒 Local storage for API keys (browser-only)
- 🔄 Python backend proxy for API calls
- 📱 Responsive design
- 🎨 Modern UI with clear user/AI message distinction

## Project Structure

```
michael_chat/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore file
├── backend/
│   └── app.py               # Python Flask server
└── frontend/
    ├── package.json         # Node.js dependencies
    ├── tsconfig.json        # TypeScript configuration
    ├── public/
    │   └── index.html       # HTML template
    └── src/
        ├── index.tsx        # React entry point
        ├── index.css        # Basic styles
        ├── App.tsx          # Main App component
        ├── App.css          # Main styles
        ├── types/
        │   └── types.ts     # TypeScript types
        └── components/
            ├── Chat.tsx     # Chat interface component
            └── Configuration.tsx # Configuration component
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

### Installation

1. **Navigate to the project directory:**
   ```bash
   cd michael_chat
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies:**
   ```bash
   cd frontend
   npm install
   ```

4. **Build the React frontend:**
   ```bash
   npm run build
   ```

5. **Return to the project root:**
   ```bash
   cd ..
   ```

### Running the Application

1. **Start the Python server:**
   ```bash
   python3 backend/app.py
   ```

2. **Open your web browser and navigate to:**
   ```
   http://localhost:8000
   ```

## Usage

### Initial Setup

1. When you first open the application, you'll be prompted to configure your API settings.
2. Click on "Configuration" in the navigation bar.
3. Enter your API endpoint URL (default: `https://api.openai.com/v1/chat/completions`)
4. Enter your API key
5. Click "Save Configuration"

### Chat Interface

1. After configuration, click "Chat" to start using the application.
2. Type your message in the input field and click "Send" or press Enter.
3. The AI response will appear in the chat window.
4. Use "Clear Chat" to start a new conversation.

### Configuration Options

- **API Endpoint URL**: The complete URL for your chat API service
- **API Key**: Your authentication key for the API
- **Test Backend Connection**: Verify that the Python backend is running
- **Reset to Defaults**: Restore default OpenAI API settings

## API Compatibility

The application is designed to work with OpenAI-compatible APIs. The default configuration works with:

- OpenAI GPT-3.5-turbo
- OpenAI GPT-4
- Other OpenAI-compatible APIs

## Development

### Frontend Development

To run the React frontend in development mode:

```bash
cd frontend
npm start
```

This will start the development server on `http://localhost:3000` with hot reloading.

### Backend Development

The Python backend includes debug mode enabled by default. Any changes to `backend/app.py` will automatically restart the server.

### Building for Production

1. Build the React frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. The built files will be in `frontend/build/` and will be served by the Python backend.

## Troubleshooting

### Common Issues

1. **"Build directory not found" error:**
   - Make sure you've run `npm run build` in the frontend directory
   - Check that `frontend/build/` exists

2. **API connection errors:**
   - Verify your API endpoint URL is correct
   - Check that your API key is valid
   - Use the "Test Backend Connection" button to verify the backend is running

3. **CORS errors:**
   - The backend includes CORS configuration for local development
   - For production, you may need to adjust CORS settings

### Development Tips

- Configuration is stored in browser localStorage
- API keys are never sent to or stored on the server
- The Python backend proxies API calls to protect your API key
- Use browser developer tools to debug frontend issues

## Security Notes

- API keys are stored locally in your browser only
- All API calls are proxied through the Python backend
- API keys are never logged or stored on the server
- Use HTTPS in production for secure API key transmission

## License

This project is provided as-is for development and learning purposes.

## Contributing

Feel free to fork and modify this project for your own use. The code is structured to be easily customizable and extensible.
