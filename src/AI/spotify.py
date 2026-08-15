import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import spotipy
from spotipy.oauth2 import SpotifyPKCE
from config import SPOTIFY_CLIENT_ID, SPOTIFY_REDIRECT_URI


SCOPES = (
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing"
)


# Function: get_spotify
def get_spotify():
    auth_manager = SpotifyPKCE(
        client_id=SPOTIFY_CLIENT_ID,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPES,
        cache_path=".spotify_cache",
        open_browser=True,
    )

    return spotipy.Spotify(auth_manager=auth_manager)

# Function: spotify_now_playing
def spotify_now_playing() -> str:
    spotify = get_spotify()

    track = spotify.current_user_playing_track()

    if not track or not track.get("item"):
        return "Nothing is currently playing."

    item = track["item"]

    artists = ", ".join(
        artist["name"] for artist in item["artists"]
    )

    return f"Currently playing: {item['name']} by {artists}"

# Function: spotify_search
def spotify_search(query: str) -> str:
    """Searches Spotify for music.
    Use this ONLY when the user explicitly asks to search, find,
    look up, or browse for music. Do not use this before
    spotify_play_song when the user simply asks to play a song.
    """
    if not query:
        return "Please provide something to search for."

    spotify = get_spotify()

    results = spotify.search(
        q=query,
        type="track",
        limit=5,
    )

    tracks = results["tracks"]["items"]

    if not tracks:
        return "No tracks found."

    output = []

    for track in tracks:
        artists = ", ".join(
            artist["name"] for artist in track["artists"]
        )

        output.append(
            f"{track['name']} — {artists}\n"
            f"URI: {track['uri']}"
        )

    return "\n\n".join(output)

# Function: spotify_play
def spotify_play(uri: str) -> str:
    """Starts playback of a Spotify track using its Spotify URI."""
    if not uri:
        return "Please provide a Spotify track URI."

    spotify = get_spotify()

    try:
        spotify.start_playback(uris=[uri])
        return "Playback started."
    except Exception as e:
        return f"Could not start playback: {e}"

# Function: spotify_play_song
def spotify_play_song(query: str) -> str:
    """Plays a specific song requested by the user on Spotify.
    Use this tool directly when the user asks to play a song.
    Pass the user's song title and artist exactly as requested.
    Do not add years, genres, release information, or other guesses.
    Do not use spotify_search before this tool.
    """
    if not query:
        return "Please provide a song to play."

    spotify = get_spotify()
    query = query.strip()

    results = spotify.search(
        q=query,
        type="track",
        limit=10,
    )

    tracks = results["tracks"]["items"]

    if not tracks:
        return f"I couldn't find '{query}' on Spotify."

    words = query.lower().split()

    scored = []

    for track in tracks:
        track_name = track["name"].lower()
        artist_names = [
            artist["name"].lower()
            for artist in track["artists"]
        ]

        score = 0

        if track_name == query.lower():
            score += 100

        for word in words:
            if word in track_name:
                score += 20

            if any(word in artist for artist in artist_names):
                score += 30

        scored.append((score, track))

    scored.sort(key=lambda x: x[0], reverse=True)

    best_score, best_track = scored[0]

    if best_score < 50:
        options = []

        for _, track in scored[:5]:
            artists = ", ".join(
                artist["name"] for artist in track["artists"]
            )

            options.append(
                f'"{track["name"]}" by {artists}'
            )

        return (
            f"I couldn't confidently identify '{query}'.\n"
            + "\n".join(f"- {option}" for option in options)
            + "\nPlease be more specific."
        )

    artists = ", ".join(
        artist["name"] for artist in best_track["artists"]
    )

    try:
        spotify.start_playback(uris=[best_track["uri"]])
    except Exception as e:
        return f"Could not start playback: {e}"

    return f'Playing "{best_track["name"]}" by {artists}.'


# Function: spotify_pause
def spotify_pause() -> str:
    """Pauses the currently playing Spotify track."""
    spotify = get_spotify()

    try:
        spotify.pause_playback()
        return "Spotify playback paused."
    except Exception as e:
        return f"Could not pause Spotify: {e}"


# Function: spotify_resume
def spotify_resume() -> str:
    """Resumes Spotify playback."""
    spotify = get_spotify()

    try:
        spotify.start_playback()
        return "Spotify playback resumed."
    except Exception as e:
        return f"Could not resume Spotify: {e}"


# Function: spotify_next
def spotify_next() -> str:
    """Skips to the next Spotify track."""
    spotify = get_spotify()

    try:
        spotify.next_track()
        return "Skipped to the next track."
    except Exception as e:
        return f"Could not skip track: {e}"


# Function: spotify_previous
def spotify_previous() -> str:
    """Goes back to the previous Spotify track."""
    spotify = get_spotify()

    try:
        spotify.previous_track()
        return "Went back to the previous track."
    except Exception as e:
        return f"Could not go to the previous track: {e}"



# SPOTIFY TOOLS
ALL_SPOTIFY_TOOLS = [
    spotify_now_playing,
    spotify_search,
    spotify_play_song,
    spotify_pause,
    spotify_resume,
    spotify_next,
    spotify_previous,
]

if __name__ == "__main__":
     print(spotify_now_playing())

    # print(spotify_pause())
    # print(spotify_resume())
    # print(spotify_next())
    # print(spotify_previous())


