import streamlit as st
from stqdm import stqdm
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tidalapi
import threading

# Initialize session state
if 'spotify_token' not in st.session_state:
    st.session_state.spotify_token = None
if 'tidal_session' not in st.session_state:
    st.session_state.tidal_session = None
if 'tidal_oauth_pending' not in st.session_state:
    st.session_state.tidal_oauth_pending = False
if 'credentials_entered' not in st.session_state:
    st.session_state.credentials_entered = False

# Check for OAuth callback
query_params = st.query_params
spotify_code = query_params.get('code', None)

# Show credentials form (only Spotify credentials needed now)
if not st.session_state.credentials_entered:
    st.title("🎵 Spotify to Tidal Transfer")
    st.write("Transfer your music library from Spotify to Tidal")
    
    with st.form("credentials"):
        st.subheader("Spotify API Credentials")
        st.markdown("Get these from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)")
        
        spotify_client_id = st.text_input("Spotify Client ID:", "")
        spotify_client_secret = st.text_input("Spotify Client Secret:", "", type="password")
        
        st.info("💡 No Tidal credentials needed - you'll authenticate with OAuth")
        
        connect = st.form_submit_button("Connect to Spotify & Tidal")
    
    if connect and all([spotify_client_id, spotify_client_secret]):
        st.session_state.spotify_client_id = spotify_client_id
        st.session_state.spotify_client_secret = spotify_client_secret
        st.session_state.credentials_entered = True
        st.rerun()

# Handle Spotify OAuth flow
if st.session_state.credentials_entered and st.session_state.spotify_token is None:
    
    # Set up Spotify OAuth
    sp_oauth = SpotifyOAuth(
        client_id=st.session_state.spotify_client_id,
        client_secret=st.session_state.spotify_client_secret,
        redirect_uri="https://iamreplay.streamlit.app/callback",
        scope="user-library-read playlist-read-private playlist-read-collaborative user-follow-read",
        cache_handler=None,
        show_dialog=True
    )
    
    # If we have a code from OAuth callback, exchange it for a token
    if spotify_code:
        try:
            with st.spinner("Completing Spotify authentication..."):
                token_info = sp_oauth.get_access_token(spotify_code, check_cache=False)
                st.session_state.spotify_token = token_info
                st.success("✅ Spotify authentication successful!")
                st.rerun()
        except Exception as e:
            st.error(f"Spotify authentication failed: {str(e)}")
            if st.button("Try Again"):
                st.session_state.credentials_entered = False
                st.rerun()
    else:
        # Show authorization link
        auth_url = sp_oauth.get_authorize_url()
        st.title("Step 1: Authorize Spotify")
        st.warning("⚠️ Please authorize with Spotify:")
        st.markdown(f"### [Click here to authorize Spotify →]({auth_url})")
        st.info("After authorizing, you'll be redirected back to this page.")
        st.stop()

# Handle Tidal OAuth flow
if st.session_state.spotify_token and st.session_state.tidal_session is None:
    st.title("Step 2: Authorize Tidal")
    
    if not st.session_state.tidal_oauth_pending:
        if st.button("Start Tidal Authorization", type="primary"):
            try:
                with st.spinner("Setting up Tidal authentication..."):
                    session = tidalapi.Session()
                    login, future = session.login_oauth()
                    
                    # Store in session state
                    st.session_state.tidal_login = login
                    st.session_state.tidal_future = future
                    st.session_state.tidal_session_temp = session
                    st.session_state.tidal_oauth_pending = True
                    st.rerun()
            except Exception as e:
                st.error(f"Failed to start Tidal OAuth: {str(e)}")
    else:
        # Show the authorization URL
        login = st.session_state.tidal_login
        st.warning("⚠️ Please authorize with Tidal:")
        st.markdown(f"### [Click here to authorize Tidal →]({login.verification_uri_complete})")
        st.info("Or visit this URL and enter the code:")
        st.code(login.verification_uri)
        st.code(f"User Code: {login.user_code}")
        
        # Check if authorization is complete
        if st.button("I've authorized - Continue"):
            try:
                with st.spinner("Checking Tidal authorization..."):
                    # Check if already done
                    future = st.session_state.tidal_future
                    if future.done():
                        st.session_state.tidal_session = st.session_state.tidal_session_temp
                        st.session_state.tidal_oauth_pending = False
                        st.success("✅ Tidal authentication successful!")
                        st.rerun()
                    else:
                        # Try to complete with timeout
                        try:
                            future.result(timeout=2)
                            st.session_state.tidal_session = st.session_state.tidal_session_temp
                            st.session_state.tidal_oauth_pending = False
                            st.success("✅ Tidal authentication successful!")
                            st.rerun()
                        except:
                            st.warning("Authorization not complete yet. Please authorize on Tidal and try again.")
            except Exception as e:
                st.error(f"Tidal authorization check failed: {str(e)}")

# Main transfer UI
if st.session_state.spotify_token and st.session_state.tidal_session:
    st.title("🎵 Transfer Your Music")
    st.success("✅ Connected to both Spotify and Tidal!")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Disconnect All"):
            st.session_state.clear()
            st.rerun()
    
    # Create clients
    sp = spotipy.Spotify(auth=st.session_state.spotify_token['access_token'])
    tidal = st.session_state.tidal_session
    
    st.divider()
    st.subheader("Select content to transfer:")
    
    col1, col2 = st.columns(2)
    with col1:
        is_transfer_tracks = st.checkbox("📀 Transfer Saved Tracks")
        is_transfer_albums = st.checkbox("💿 Transfer Saved Albums")
    with col2:
        is_transfer_artists = st.checkbox("👤 Transfer Followed Artists")
        is_transfer_playlists = st.checkbox("📝 Transfer Playlists")
    
    if st.button("🚀 Start Transfer", type="primary", use_container_width=True):
        if not any([is_transfer_tracks, is_transfer_albums, is_transfer_artists, is_transfer_playlists]):
            st.warning("⚠️ Please select at least one content type to transfer.")
        else:
            try:
                # Transfer Tracks
                if is_transfer_tracks:
                    st.subheader("📀 Transferring Saved Tracks")
                    with st.spinner("Fetching your saved tracks from Spotify..."):
                        all_tracks = []
                        results = sp.current_user_saved_tracks(limit=50)
                        all_tracks.extend(results['items'])
                        
                        while results['next']:
                            results = sp.next(results)
                            all_tracks.extend(results['items'])
                        
                        st.info(f"Found {len(all_tracks)} saved tracks")
                    
                    progress_bar = st.progress(0)
                    success_count = 0
                    fail_count = 0
                    
                    for idx, item in enumerate(all_tracks):
                        track = item['track']
                        if track:
                            track_name = track['name']
                            artist_name = track['artists'][0]['name']
                            
                            try:
                                # Search on Tidal
                                search_results = tidal.search(f"{artist_name} {track_name}", models=[tidalapi.media.Track])
                                if search_results['tracks']:
                                    tidal_track = search_results['tracks'][0]
                                    tidal.user.favorites.add_track(tidal_track.id)
                                    st.write(f"✓ Added: {track_name} by {artist_name}")
                                    success_count += 1
                                else:
                                    st.write(f"✗ Not found: {track_name} by {artist_name}")
                                    fail_count += 1
                            except Exception as e:
                                st.write(f"✗ Error with: {track_name} - {str(e)}")
                                fail_count += 1
                            
                            progress_bar.progress((idx + 1) / len(all_tracks))
                    
                    st.success(f"✅ Tracks: {success_count} added, {fail_count} failed")
                
                # Transfer Albums
                if is_transfer_albums:
                    st.subheader("💿 Transferring Saved Albums")
                    with st.spinner("Fetching your saved albums from Spotify..."):
                        all_albums = []
                        results = sp.current_user_saved_albums(limit=50)
                        all_albums.extend(results['items'])
                        
                        while results['next']:
                            results = sp.next(results)
                            all_albums.extend(results['items'])
                        
                        st.info(f"Found {len(all_albums)} saved albums")
                    
                    progress_bar = st.progress(0)
                    success_count = 0
                    fail_count = 0
                    
                    for idx, item in enumerate(all_albums):
                        album = item['album']
                        album_name = album['name']
                        artist_name = album['artists'][0]['name']
                        
                        try:
                            search_results = tidal.search(f"{artist_name} {album_name}", models=[tidalapi.media.Album])
                            if search_results['albums']:
                                tidal_album = search_results['albums'][0]
                                tidal.user.favorites.add_album(tidal_album.id)
                                st.write(f"✓ Added: {album_name} by {artist_name}")
                                success_count += 1
                            else:
                                st.write(f"✗ Not found: {album_name} by {artist_name}")
                                fail_count += 1
                        except Exception as e:
                            st.write(f"✗ Error with: {album_name} - {str(e)}")
                            fail_count += 1
                        
                        progress_bar.progress((idx + 1) / len(all_albums))
                    
                    st.success(f"✅ Albums: {success_count} added, {fail_count} failed")
                
                # Transfer Artists
                if is_transfer_artists:
                    st.subheader("👤 Transferring Followed Artists")
                    with st.spinner("Fetching your followed artists from Spotify..."):
                        all_artists = []
                        results = sp.current_user_followed_artists(limit=50)
                        all_artists.extend(results['artists']['items'])
                        
                        while results['artists']['next']:
                            results = sp.next(results['artists'])
                            all_artists.extend(results['artists']['items'])
                        
                        st.info(f"Found {len(all_artists)} followed artists")
                    
                    progress_bar = st.progress(0)
                    success_count = 0
                    fail_count = 0
                    
                    for idx, artist in enumerate(all_artists):
                        artist_name = artist['name']
                        
                        try:
                            search_results = tidal.search(artist_name, models=[tidalapi.media.Artist])
                            if search_results['artists']:
                                tidal_artist = search_results['artists'][0]
                                tidal.user.favorites.add_artist(tidal_artist.id)
                                st.write(f"✓ Added: {artist_name}")
                                success_count += 1
                            else:
                                st.write(f"✗ Not found: {artist_name}")
                                fail_count += 1
                        except Exception as e:
                            st.write(f"✗ Error with: {artist_name} - {str(e)}")
                            fail_count += 1
                        
                        progress_bar.progress((idx + 1) / len(all_artists))
                    
                    st.success(f"✅ Artists: {success_count} added, {fail_count} failed")
                
                # Transfer Playlists
                if is_transfer_playlists:
                    st.subheader("📝 Transferring Playlists")
                    with st.spinner("Fetching your playlists from Spotify..."):
                        playlists = sp.current_user_playlists(limit=50)
                        user_id = sp.me()['id']
                        st.info(f"Found {len(playlists['items'])} playlists")
                    
                    for playlist in playlists['items']:
                        if playlist['owner']['id'] == user_id:  # Only user's own playlists
                            playlist_name = playlist['name']
                            st.write(f"📝 Creating playlist: {playlist_name}")
                            
                            try:
                                # Create playlist on Tidal
                                new_playlist = tidal.user.create_playlist(playlist_name, "")
                                
                                # Get tracks from Spotify playlist
                                tracks_results = sp.playlist_tracks(playlist['id'])
                                track_ids = []
                                
                                for item in tracks_results['items']:
                                    if item['track']:
                                        track = item['track']
                                        try:
                                            search_results = tidal.search(
                                                f"{track['artists'][0]['name']} {track['name']}", 
                                                models=[tidalapi.media.Track]
                                            )
                                            if search_results['tracks']:
                                                track_ids.append(search_results['tracks'][0].id)
                                        except:
                                            pass
                                
                                # Add tracks to Tidal playlist
                                if track_ids:
                                    new_playlist.add(track_ids)
                                    st.write(f"✓ Created: {playlist_name} ({len(track_ids)} tracks)")
                                else:
                                    st.write(f"⚠️ Created: {playlist_name} (no tracks found)")
                            except Exception as e:
                                st.write(f"✗ Failed to create: {playlist_name} - {str(e)}")
                    
                    st.success("✅ Playlists transfer complete!")
                
                st.balloons()
                st.success("🎉 Transfer complete!")
                
            except Exception as e:
                st.error(f"Transfer error: {str(e)}")
                st.exception(e)
