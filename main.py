import streamlit as st
from stqdm import stqdm
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tidalapi

# Initialize session state
if 'spotify_token' not in st.session_state:
    st.session_state.spotify_token = None
if 'tidal_session' not in st.session_state:
    st.session_state.tidal_session = None
if 'credentials_entered' not in st.session_state:
    st.session_state.credentials_entered = False

# Check for OAuth callback
query_params = st.query_params
code = query_params.get('code', None)

# Show credentials form
if not st.session_state.credentials_entered:
    with st.form("credentials"):
        col1, col2 = st.columns(2)
        
        col1.title("Spotify Credentials")
        spotify_client_id = col1.text_input("Client ID:", "")
        spotify_client_secret = col1.text_input("Secret Token:", "", type="password")
        
        col2.title("Tidal Credentials")
        tidal_username = col2.text_input("Tidal Username:", "")
        tidal_password = col2.text_input("Password:", "", type="password")
        
        connect = st.form_submit_button("Connect")
    
    if connect and all([spotify_client_id, spotify_client_secret, tidal_username, tidal_password]):
        st.session_state.spotify_client_id = spotify_client_id
        st.session_state.spotify_client_secret = spotify_client_secret
        st.session_state.tidal_username = tidal_username
        st.session_state.tidal_password = tidal_password
        st.session_state.credentials_entered = True
        st.rerun()

# Handle Spotify OAuth flow
if st.session_state.credentials_entered and st.session_state.spotify_token is None:
    
    # Set up Spotify OAuth
    sp_oauth = SpotifyOAuth(
        client_id=st.session_state.spotify_client_id,
        client_secret=st.session_state.spotify_client_secret,
        redirect_uri="https://iamreplay.streamlit.app/callback",
        scope="user-library-read playlist-read-private user-follow-read",
        cache_handler=None,  # Don't cache to disk
        show_dialog=True
    )
    
    # If we have a code from OAuth callback, exchange it for a token
    if code:
        try:
            token_info = sp_oauth.get_access_token(code, check_cache=False)
            st.session_state.spotify_token = token_info
            st.success("✅ Spotify authentication successful!")
            st.rerun()
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
    else:
        # Show authorization link
        auth_url = sp_oauth.get_authorize_url()
        st.warning("⚠️ Please authorize with Spotify:")
        st.markdown(f"[Click here to authorize Spotify]({auth_url})")
        st.info("After authorizing, you'll be redirected back to this page.")
        st.stop()

# Connect to Tidal
if st.session_state.credentials_entered and st.session_state.tidal_session is None:
    try:
        with st.spinner("Connecting to Tidal..."):
            session = tidalapi.Session()
            session.login(st.session_state.tidal_username, st.session_state.tidal_password)
            st.session_state.tidal_session = session
            st.success("✅ Tidal authentication successful!")
    except Exception as e:
        st.error(f"Tidal login failed: {str(e)}")
        st.stop()

# Main transfer UI
if st.session_state.spotify_token and st.session_state.tidal_session:
    st.success("✅ Connected to both Spotify and Tidal!")
    
    if st.button("Disconnect"):
        st.session_state.clear()
        st.rerun()
    
    # Create Spotify client
    sp = spotipy.Spotify(auth=st.session_state.spotify_token['access_token'])
    tidal = st.session_state.tidal_session
    
    st.divider()
    st.subheader("Select content to transfer:")
    
    is_transfer_tracks = st.checkbox("Transfer Saved Tracks")
    is_transfer_albums = st.checkbox("Transfer Saved Albums")
    is_transfer_artists = st.checkbox("Transfer Followed Artists")
    is_transfer_playlists = st.checkbox("Transfer Playlists")
    
    if st.button("Transfer", type="primary"):
        if not any([is_transfer_tracks, is_transfer_albums, is_transfer_artists, is_transfer_playlists]):
            st.warning("⚠️ Please select at least one content type to transfer.")
        else:
            # Transfer logic here
            if is_transfer_tracks:
                with st.spinner("Transferring tracks..."):
                    st.info("Track transfer would happen here")
                    # Implement transfer logic
            
            if is_transfer_albums:
                with st.spinner("Transferring albums..."):
                    st.info("Album transfer would happen here")
            
            if is_transfer_artists:
                with st.spinner("Transferring artists..."):
                    st.info("Artist transfer would happen here")
            
            if is_transfer_playlists:
                with st.spinner("Transferring playlists..."):
                    st.info("Playlist transfer would happen here")
            
            st.success("🎉 Transfer complete!")
