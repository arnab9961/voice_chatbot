import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Gmail API scope for sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def setup_gmail_credentials():
    """
    Set up Gmail API credentials for the Voice Chatbot.
    This script guides users through the OAuth 2.0 flow.
    """
    print("=== Gmail API Setup for Voice Chatbot ===")
    print("\nThis script will help you set up Gmail API credentials.")
    
    credentials_path = 'credentials.json'
    token_path = 'token.json'
    
    # Check if credentials.json exists
    if not os.path.exists(credentials_path):
        print("\nERROR: credentials.json file not found!")
        print("Please follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project")
        print("3. Enable the Gmail API")
        print("4. Create OAuth 2.0 Client ID credentials")
        print("5. Download the credentials JSON file")
        print("6. Save it as 'credentials.json' in this directory")
        print("\nAfter completing these steps, run this script again.")
        return
    
    # Check if token.json already exists
    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_info(
                json.loads(open(token_path).read()), SCOPES)
        except:
            pass
    
    # If no valid credentials available, prompt login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("\nAuthenticating with Google...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    print("\nSetup complete! Your Gmail credentials are now ready to use.")
    print("You can now use the Voice Chatbot to send emails.")

if __name__ == "__main__":
    setup_gmail_credentials()
