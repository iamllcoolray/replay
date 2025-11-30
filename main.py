import os
import streamlit as st
from stqdm import stqdm
from dotenv import load_dotenv
from spotify2tidal import Spotify2Tidal

if "connected" not in st.session_state:
    st.session_state.connected = False

if not st.session_state.connected:
    with st.form("credentials"):
        col1, col2 = st.columns(2)

        col1.title("""
        Spotify Credentials
        """)
        spotify_username = col1.text_input("Spotify Username:", "")
        spotify_client_id = col1.text_input("Client ID:", "")
        spotify_client_secret = col1.text_input("Secret Token:", "")

        col2.title("""
        Tidal Credentials
        """)
        tidal_username = col2.text_input("Tidal Username:", "")
        tidal_password = col2.text_input("Password:", "")
        
        connect = st.form_submit_button("connect")

    if connect and all([spotify_username, spotify_client_id, spotify_client_secret, tidal_username, tidal_password]):
        st.session_state.spotify_username = spotify_username
        st.session_state.spotify_client_id = spotify_client_id
        st.session_state.spotify_client_secret = spotify_client_secret
        st.session_state.tidal_username = tidal_username
        st.session_state.tidal_password = tidal_password
        st.session_state.connected = True
        st.rerun()        

if st.session_state.connected:
    st.success("Connected!")

    if st.button("disconnect"):
        st.session_state.connected = False
        st.rerun()

    content_transfer = Spotify2Tidal(
        tidal_username=st.session_state.tidal_username,
        tidal_password=st.session_state.tidal_password,
        spotify_username=st.session_state.spotify_username,
        spotify_client_id=st.session_state.spotify_client_id,
        spotify_client_secret=st.session_state.spotify_client_secret,
        spotify_redirect_uri="https://iamreplay.streamlit.app/callback",
        spotify_discover_weekly_id=None,
    )

    is_transfer_tracks = st.checkbox("Transfer Tracks")
    is_transfer_albums = st.checkbox("Transfer Albums")
    is_transfer_artists = st.checkbox("Transfer Artists")
    is_transfer_playlists = st.checkbox("Transfer Playlists")

    is_transfer = st.button("transfer")

    if is_transfer:
        tasks = []
        if is_transfer_tracks:
            tasks.append(("Tracks", content_transfer.copy_all_saved_spotify_tracks()))
        if is_transfer_albums:
            tasks.append(("Albums", content_transfer.copy_all_saved_spotify_albums))
        if is_transfer_artists:
            tasks.append(("Artists", content_transfer.copy_all_saved_spotify_artists))
        if is_transfer_playlists:
            tasks.append(("Playlists", content_transfer.copy_all_spotify_playlists))

        for name, task_func in stqdm(tasks, desc="Transferring..."):
            st.write(f"Copying {name}...")
            task_func()

        st.success(f"Transfer complete!")
