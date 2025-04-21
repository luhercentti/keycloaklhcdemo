# app.py
from flask import Flask, redirect, url_for, session, render_template_string, request
from authlib.integrations.flask_client import OAuth
import json
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')

# Load client secrets from file
with open('client_secrets.json', 'r') as f:
    client_config = json.load(f)

oauth = OAuth(app)

# Configure Keycloak from the client secrets file
oauth.register(
    name='keycloak',
    server_metadata_url=f"{client_config['web']['issuer']}/.well-known/openid-configuration",
    client_id=client_config['web']['client_id'],
    client_secret=client_config['web']['client_secret'],
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Create a home page template
HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Keycloak Python Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .container { max-width: 800px; margin: 0 auto; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 5px; }
        .button { display: inline-block; padding: 10px 15px; background: #4CAF50; color: white; 
                 text-decoration: none; border-radius: 5px; margin-right: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Keycloak Authentication Test</h1>
        
        {% if user_info %}
            <h2>You are logged in!</h2>
            <h3>User Info:</h3>
            <pre>{{ user_info }}</pre>
            <a href="/logout" class="button">Log Out</a>
        {% else %}
            <p>You are not logged in.</p>
            <a href="/login" class="button">Log In</a>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    user_info = session.get('user_info')
    return render_template_string(HOME_PAGE, user_info=json.dumps(user_info, indent=4) if user_info else None)

@app.route('/login')
def login():
    # Generate and store a nonce value in the session
    nonce = secrets.token_urlsafe(16)
    session['nonce'] = nonce
    
    redirect_uri = url_for('callback', _external=True)
    return oauth.keycloak.authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/callback')
def callback():
    # Get the token
    token = oauth.keycloak.authorize_access_token()
    
    # Get the nonce from the session
    nonce = session.pop('nonce', None)
    
    # Simply use the userinfo endpoint instead of parsing id_token
    userinfo = token.get('userinfo')
    if not userinfo:
        # If userinfo is not available in the token, fetch it separately
        userinfo = oauth.keycloak.userinfo()
    
    session['user_info'] = userinfo
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user_info', None)
    # For a complete logout from Keycloak
    logout_url = f"{client_config['web']['issuer']}/protocol/openid-connect/logout"
    return redirect(logout_url + f"?redirect_uri={url_for('home', _external=True)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)