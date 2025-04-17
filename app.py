# app.py
from flask import Flask, redirect, url_for, session, render_template_string, request
from authlib.integrations.flask_client import OAuth
import json
import os
import secrets
import logging
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Support for running behind proxy/ingress
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Load client secrets from file
client_secrets_path = os.environ.get('CLIENT_SECRETS_PATH', '/app/client_secrets.json')
try:
    with open(client_secrets_path, 'r') as f:
        client_config = json.load(f)
    logger.info("Successfully loaded client secrets")
    
    # Set Flask secret key from the same config file
    app.secret_key = client_config['web']['flask_secret_key']
    
except Exception as e:
    logger.error(f"Error loading secrets from {client_secrets_path}: {e}")
    client_config = {"web": {}}
    app.secret_key = 'fallback-dev-key'  # Only for development!
    logger.warning("Using fallback secret key - not secure for production!")
oauth = OAuth(app)

# Configure Keycloak from the client secrets file
try:
    oauth.register(
        name='keycloak',
        server_metadata_url=f"{client_config['web']['issuer']}/.well-known/openid-configuration",
        client_id=client_config['web']['client_id'],
        client_secret=client_config['web']['client_secret'],
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    logger.info("Successfully registered Keycloak OAuth client")
except Exception as e:
    logger.error(f"Error registering Keycloak OAuth client: {e}")

# Home page template with improved styling and error handling
HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Keycloak Python Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
        .button { display: inline-block; padding: 10px 15px; background: #4CAF50; color: white; 
                 text-decoration: none; border-radius: 5px; margin-right: 10px; }
        .error { color: #D32F2F; background: #FFEBEE; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Keycloak Authentication Test</h1>
        
        {% if error %}
            <div class="error">
                <h3>Error:</h3>
                <p>{{ error }}</p>
            </div>
        {% endif %}
        
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
    error = session.get('error')
    if error:
        session.pop('error', None)
    return render_template_string(HOME_PAGE, 
                                  user_info=json.dumps(user_info, indent=4) if user_info else None,
                                  error=error)

@app.route('/login')
def login():
    # Generate and store a nonce value in the session
    nonce = secrets.token_urlsafe(16)
    session['nonce'] = nonce
    
    redirect_uri = url_for('callback', _external=True)
    try:
        return oauth.keycloak.authorize_redirect(redirect_uri, nonce=nonce)
    except Exception as e:
        logger.error(f"Login redirect error: {e}")
        session['error'] = f"Authentication error: {str(e)}"
        return redirect('/')

@app.route('/callback')
def callback():
    try:
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
        logger.info("Successfully authenticated user")
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        session['error'] = f"Authentication error: {str(e)}"
        
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user_info', None)
    # For a complete logout from Keycloak
    try:
        logout_url = f"{client_config['web']['issuer']}/protocol/openid-connect/logout"
        return redirect(logout_url + f"?redirect_uri={url_for('home', _external=True)}")
    except Exception as e:
        logger.error(f"Logout error: {e}")
        session['error'] = f"Logout error: {str(e)}"
        return redirect('/')

@app.route('/health')
def health():
    # Check if we can access Keycloak configuration
    healthy = 'issuer' in client_config.get('web', {})
    status_code = 200 if healthy else 500
    return {"status": "healthy" if healthy else "unhealthy"}, status_code

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)