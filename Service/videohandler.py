import os
import requests
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict
from urllib.parse import urlparse

class WhatsAppVideoHandler:
    def __init__(self, account_sid: str, auth_token: str, upload_folder: str = 'received_videos'):
        """
        Initialize the WhatsApp video handler.
        
        Args:
            account_sid (str): Twilio Account SID
            auth_token (str): Twilio Auth Token
            upload_folder (str): Folder to save videos
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.upload_folder = upload_folder
        self.allowed_extensions = {'mp4', 'avi', 'mov', '3gp'}
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
        # Create upload folder if it doesn't exist
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
    
    def process_video_message(self, webhook_data: Dict) -> Tuple[bool, str, Optional[str]]:
        """
        Process a video message from WhatsApp.
        
        Args:
            webhook_data (dict): The webhook data from Twilio
            
        Returns:
            Tuple[bool, str, Optional[str]]: 
                - Success status
                - Message to send back to user
                - Path where video was saved (if successful)
        """
        try:
            # Extract message details
            num_media = int(webhook_data.get('NumMedia', 0))
            from_number = webhook_data.get('From', '')
            
            if num_media == 0:
                return False, "No media found in the message.", None
            
            # Process the first media item (usually there's only one)
            media_url = webhook_data.get('MediaUrl0')
            content_type = webhook_data.get('MediaContentType0', '').lower()
            
            # Validate media type
            if not any(ext in content_type for ext in ['video', 'mp4', 'avi', 'mov', '3gp']):
                return False, "Please send only video files.", None
            
            # Download and save video
            video_content = self._download_video(media_url)
            if not video_content:
                return False, "Failed to download the video.", None
            
            saved_path = self._save_video(video_content, from_number)
            if not saved_path:
                return False, "Failed to save the video.", None
            
            self.logger.info(f"Video saved successfully at {saved_path}")
            return True, "Video received and saved successfully!", saved_path
            
        except Exception as e:
            self.logger.error(f"Error processing video message: {e}")
            return False, f"Error processing video: {str(e)}", None
    
    def _download_video(self, video_url: str) -> Optional[bytes]:
        """Download video from Twilio's servers"""
        try:
            response = requests.get(
                video_url, 
                auth=(self.account_sid, self.auth_token),
                timeout=30  # 30 seconds timeout
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            self.logger.error(f"Error downloading video: {e}")
            return None
    
    def _save_video(self, video_content: bytes, phone_number: str) -> Optional[str]:
        """Save video content to file"""
        try:
            # Create unique filename using timestamp and phone number
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            clean_phone = ''.join(filter(str.isalnum, phone_number))
            filename = f"{clean_phone}_{timestamp}.mp4"
            filepath = os.path.join(self.upload_folder, filename)
            
            with open(filepath, 'wb') as f:
                f.write(video_content)
            
            return filepath
        except Exception as e:
            self.logger.error(f"Error saving video: {e}")
            return None

# Usage example in your Flask/FastAPI/Django backend:

"""
from flask import Flask, request
app = Flask(__name__)

# Initialize the handler
video_handler = WhatsAppVideoHandler(
    account_sid='your_account_sid',
    auth_token='your_auth_token',
    upload_folder='path/to/videos'
)

@app.route("/webhook", methods=['POST'])
def webhook():
    # Process the video
    success, message, saved_path = video_handler.process_video_message(request.values)
    
    # Do something with the result
    if success:
        # Video was saved successfully at saved_path
        # Add your custom logic here (e.g., store in database, process video, etc.)
        pass
    
    # Return response to Twilio
    resp = MessagingResponse()
    resp.message(message)
    return str(resp)
"""