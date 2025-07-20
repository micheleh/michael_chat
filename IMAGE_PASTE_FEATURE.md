# Image Paste Feature

## Overview

Michael's Chat now supports pasting images from the clipboard directly into the chat interface! This feature is automatically enabled for configurations that support image processing.

## How It Works

### For Users
1. **Copy an image** to your clipboard (from anywhere - screenshots, image files, web pages, etc.)
2. **Navigate to the chat interface** in Michael's Chat
3. **Paste the image** using `Ctrl+V` (Windows/Linux) or `Cmd+V` (Mac)
4. **See the image thumbnail** appear above the input field
5. **Add a text message** (optional) and click **Send**

### Features
- **Multiple images**: Paste multiple images at once
- **Image thumbnails**: See previews of your images before sending
- **Remove images**: Click the ❌ button to remove unwanted images
- **Automatic detection**: Only works with models that support images
- **File size display**: Shows the size of each image
- **Smart naming**: Automatically names pasted images

## Technical Details

### Frontend Changes
- Added `ImageThumbnail` component for displaying image previews
- Updated `Chat` component to handle clipboard paste events
- Added image state management with URL.createObjectURL()
- Converted images to base64 data URLs before sending to backend
- Updated CSS with thumbnail styles and input form layout

### Backend Changes
- Modified `/api/chat` endpoint to handle image data
- Added support for multimodal API requests (text + images)
- Updated conversation history to include image data
- Enhanced OpenAI-compatible format for image messages

### Configuration
- Image support is automatically detected when testing API configurations
- The feature only appears for models that support images
- Image support status is stored in the configuration database

## Supported Image Formats

The feature supports all common image formats:
- PNG
- JPEG/JPG
- GIF
- WebP
- SVG
- BMP

## Usage Examples

### Basic Usage
1. Copy an image (screenshot, saved image, etc.)
2. Go to chat and paste with Ctrl+V/Cmd+V
3. Type a message like "What's in this image?"
4. Click Send

### Multiple Images
1. Copy and paste first image
2. Copy and paste second image
3. Both thumbnails will appear
4. Send them together with your message

### Image-Only Messages
- You can send images without any text
- Just paste the image(s) and click Send
- The AI will analyze the image(s)

## Browser Compatibility

This feature works in all modern browsers that support:
- Clipboard API
- File API
- Canvas API (for image processing)

## Security Notes

- Images are processed locally in the browser
- Base64 data is sent to the backend for API calls
- No images are stored permanently on the server
- Object URLs are properly cleaned up to prevent memory leaks

## Troubleshooting

**Images not appearing after paste:**
- Check that your configuration supports images
- Ensure you're using a model that supports multimodal input
- Try copying the image again

**Thumbnails not showing:**
- Make sure you're on the chat screen
- Check browser console for any errors
- Verify the image format is supported

**Send button disabled:**
- Either add text or paste an image
- Make sure you're not currently sending a message
- Check that the configuration is properly set up
