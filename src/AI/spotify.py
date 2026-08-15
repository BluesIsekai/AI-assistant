import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import spotipy
from spotipy.oauth2 import SpotifyPKCE
from config import SPOTIFY_CLIENT_ID, SPOTIFY_REDIRECT_URI


SCOPES = (
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "playlist-read-private "
    "playlist-read-collaborative"
)

_spotify_client = None


# Function: get_spotify
def get_spotify():
    global _spotify_client

    if _spotify_client is not None:
        return _spotify_client

    auth_manager = SpotifyPKCE(
        client_id=SPOTIFY_CLIENT_ID,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPES,
        cache_path=".spotify_cache",
        open_browser=True,
    )

    _spotify_client = spotipy.Spotify(auth_manager=auth_manager)
    return _spotify_client


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


def spotify_find_playlist(query: str) -> str:
    """Finds and displays the user's Spotify playlists.

    ONLY use this tool when the user wants to FIND, SEARCH FOR,
    LIST, or IDENTIFY a playlist.

    Do NOT use this tool when the user asks to play a playlist.
    For playback, use spotify_play_playlist instead.
    """
    if not query:
        return "Please provide a playlist name."

    spotify = get_spotify()
    query = query.lower().strip()

    playlists = []
    offset = 0

    while True:
        results = spotify.current_user_playlists(
            limit=50,
            offset=offset
        )

        items = results["items"]

        if not items:
            break

        playlists.extend(items)

        if not results["next"]:
            break

        offset += 50

    exact_matches = [
        playlist
        for playlist in playlists
        if playlist["name"].lower() == query
    ]

    partial_matches = [
        playlist
        for playlist in playlists
        if query in playlist["name"].lower()
        and playlist["name"].lower() != query
    ]

    matches = exact_matches + partial_matches

    if not matches:
        return f"I couldn't find a playlist matching '{query}'."

    output = []

    for playlist in matches[:10]:
        output.append(
            f'{playlist["name"]} — {playlist["items"]["total"]} tracks\n'
            f'URI: {playlist["uri"]}'
        )

    return "\n\n".join(output)


def spotify_play_playlist(query: str) -> str:
    """Plays one of the user's Spotify playlists.

    ALWAYS use this tool when the user asks to:
    - play a playlist
    - start a playlist
    - put on a playlist
    - listen to a playlist
    - play my playlist
    - play [playlist name]

    The query should contain ONLY the playlist name.
    Remove phrases like "play", "my", and "playlist" from the query.

    Examples:
    "play my Songs playlist" -> query="Songs"
    "play Songs playlist" -> query="Songs"
    "play my chill playlist" -> query="chill"
    "start my Gym playlist" -> query="Gym"

    Do NOT use spotify_find_playlist when the user wants to PLAY a playlist.
    """
    if not query:
        return "Please provide a playlist name."

    spotify = get_spotify()
    query = query.strip().lower()

    if query.endswith(" playlist"):
        query = query[:-9].strip()

    playlists = []
    offset = 0

    while True:
        results = spotify.current_user_playlists(
            limit=50,
            offset=offset
        )

        items = results["items"]

        if not items:
            break

        playlists.extend(items)

        if not results["next"]:
            break

        offset += 50

    exact_matches = [
        playlist
        for playlist in playlists
        if playlist["name"].lower() == query
    ]

    if len(exact_matches) == 1:
        playlist = exact_matches[0]

    else:
        matches = [
            playlist
            for playlist in playlists
            if query in playlist["name"].lower()
        ]

        if not matches:
            return f"I couldn't find a playlist matching '{query}'."

        if len(matches) > 1:
            output = []

            for playlist in matches[:10]:
                output.append(
                    f'{playlist["name"]} — {playlist["items"]["total"]} tracks'
                )

            return (
                f"I found multiple playlists matching '{query}':\n"
                + "\n".join(f"- {item}" for item in output)
                + "\nWhich one did you mean?"
            )

        playlist = matches[0]

    try:
        spotify.start_playback(
            context_uri=playlist["uri"]
        )
    except Exception as e:
        return f"Could not start playlist playback: {e}"

    return (
        f'Playing playlist "{playlist["name"]}" '
        f'with {playlist["items"]["total"]} tracks.'
    )



# SPOTIFY TOOLS
ALL_SPOTIFY_TOOLS = [
    spotify_now_playing,
    spotify_search,
    spotify_play_song,
    spotify_pause,
    spotify_resume,
    spotify_next,
    spotify_previous,
    spotify_find_playlist,
    spotify_play_playlist,
]

if __name__ == "__main__":
    # print(spotify_now_playing())  
    print(spotify_play_playlist("Songs"))

    # print(spotify_pause())
    # print(spotify_resume())
    # print(spotify_next())
    # print(spotify_previous())


