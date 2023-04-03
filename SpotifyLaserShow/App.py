import spotipy.util as util
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE, USERNAME
from SpotifyVisualizer import start_visualizer


if __name__ == "__main__":
    token = util.prompt_for_user_token(USERNAME, SCOPE, client_id=CLIENT_ID,
                                       client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI)
    if token:
        start_visualizer(token)
    else:
        print("Unable to obtain token for", USERNAME)