import os
import json
import webbrowser
import socket
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from urllib.parse import urlencode

# Gmail API scope for sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CLIENT_ID = "900054230602-oi3h58bb73fa38k0hs7fl5fe8fn2jqrq.apps.googleusercontent.com"
CLIENT_SECRET = "" # You'll need to add this from your Google Cloud Console

def setup_gmail_credentials():
    """
    Set up Gmail API credentials for the Voice Chatbot.
    This script guides users through the OAuth 2.0 flow.
    """
    print("=== Gmail API Setup for Voice Chatbot ===")
    print("\nThis script will help you set up Gmail API credentials.")
    
    token_path = 'token.json'
    
    # Instructions for developers
    print("\n=== DEVELOPER INSTRUCTIONS ===")
    print("Before running this script, you need to configure your OAuth app in Google Cloud Console:")
    print("1. Go to https://console.cloud.google.com/apis/credentials")
    print("2. Select your project or create a new one")
    print("3. Configure the OAuth consent screen (External)")
    print("4. Add the Gmail API scope: https://www.googleapis.com/auth/gmail.send")
    print("5. Add test users (including your own email)")
    print("6. Create an OAuth client ID (Desktop application)")
    print("7. Add 'http://localhost' and 'http://localhost:8080' to authorized redirect URIs")
    print("8. Note your client ID and client secret\n")
    
    # Check if token.json already exists
    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_info(
                json.loads(open(token_path).read()), SCOPES)
            print("Existing credentials found. Checking validity...")
            
            if creds.valid:
                print("Your credentials are valid and ready to use!")
                return
            
            if creds.expired and creds.refresh_token:
                print("Refreshing expired credentials...")
                creds.refresh(Request())
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
                print("Credentials refreshed successfully!")
                return
        except Exception as e:
            print(f"Error with existing credentials: {e}")
            print("Proceeding with new authentication...")
    
    # No valid credentials available, start OAuth flow
    print("\nStarting authentication flow...")
    
    # Prepare client config
    redirect_uri = 'http://localhost:8080'
    client_config = {
        "installed": {
            "client_id": CLIENT_ID,
            "project_id": "voice-chatbot-gmail",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": CLIENT_SECRET,
            "redirect_uris": [
                "http://localhost",
                "http://localhost:8080",
                "urn:ietf:wg:oauth:2.0:oob"
            ]
        }
    }
    
    try:
        # Check if we have client secret
        if not CLIENT_SECRET:
            # If no client secret, use manual auth flow
            print("\nNo client secret provided. Using manual authentication flow.")
            print("A browser will open. Please authorize the application and copy the authorization code.")
            
            # Build auth URL
            auth_url = "https://accounts.google.com/o/oauth2/auth"
            params = {
                'client_id': CLIENT_ID,
                'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
                'scope': SCOPES[0],
                'response_type': 'code',
                'access_type': 'offline'
            }
            auth_url = f"{auth_url}?{urlencode(params)}"
            
            # Open browser
            print(f"Opening browser to: {auth_url}")
            webbrowser.open(auth_url)
            
            # Get authorization code from user
            auth_code = input("\nEnter the authorization code: ")
            
            # Create a temporary file with client config
            with open('temp_client_config.json', 'w') as f:
                json.dump(client_config, f)
            
            # Use the auth code with flow
            flow = Flow.from_client_secrets_file(
                'temp_client_config.json',
                scopes=SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            # Clean up
            os.remove('temp_client_config.json')
        else:
            # With client secret, use local server flow
            flow = InstalledAppFlow.from_client_config(
                client_config, 
                SCOPES,
                redirect_uri=redirect_uri
            )
            creds = flow.run_local_server(port=8080)
        
        # Save the credentials
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        
        print("\nAuthentication successful!")
        print("Your Gmail credentials are now saved and ready to use.")
        
    except Exception as e:
        print(f"\nError during authentication: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your Google Cloud Project has the Gmail API enabled")
        print("2. Ensure your OAuth consent screen is configured correctly")
        print("3. Verify that your redirect URIs are registered in the OAuth client settings")
        print("4. Try using a different browser if you're having issues with the authentication window")
        print("5. If using manual flow, carefully copy the entire authorization code")

def create_credentials_file():
    """
    Create a credentials.json file with the correct client ID and client secret.
    This is an alternative to the manual configuration.
    """
    client_secret = input("Enter your client secret from Google Cloud Console: ")
    
    client_config = {
        "installed": {
            "client_id": CLIENT_ID,
            "project_id": "voice-chatbot-gmail",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": [
                "http://localhost",
                "http://localhost:8080",
                "urn:ietf:wg:oauth:2.0:oob"
            ]
        }
    }
    
    with open('credentials.json', 'w') as f:
        json.dump(client_config, f)
    
    print("credentials.json file created successfully!")

if __name__ == "__main__":
    print("Select an option:")
    print("1. Set up Gmail credentials")
    print("2. Create credentials.json file")
    
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == "1":
        setup_gmail_credentials()
    elif choice == "2":
        create_credentials_file()
    else:
        print("Invalid choice. Please run the script again.")
