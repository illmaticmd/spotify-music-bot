import spotipy
from spotipy.oauth2 import SpotifyOAuth
import datetime
from collections import Counter
import random
import os
import json
from dotenv import load_dotenv

load_dotenv()

# --- AUTHENTICATION (Cloud Ready) ---
cache_data = os.environ.get('SPOTIPY_CACHE_DATA')

class MemoryCacheHandler(spotipy.cache_handler.CacheHandler):
    def get_cached_token(self):
        if cache_data:
            return json.loads(cache_data)
        return None
    
    def save_token_to_cache(self, token_info):
        print("New token generated! Update your Env Var with this:")
        print(json.dumps(token_info))

handler = MemoryCacheHandler() if cache_data else None
scope = "user-top-read playlist-modify-public"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, cache_handler=handler))

# --- LOGIC ---

def get_top_genres():
    print("--- STEP 1: Analyzing Your Taste Profile ---")
    try:
        results = sp.current_user_top_artists(limit=20, time_range='short_term')
        if not results['items']:
            results = sp.current_user_top_artists(limit=20, time_range='long_term')
            
        if not results['items']:
            return ['pop'] # Fallback

        all_genres = []
        for artist in results['items']:
            all_genres.extend(artist['genres'])
            
        # Limit to Top 5 Genres to keep the playlist focused (and faster)
        genre_counts = Counter(all_genres)
        top_5 = [genre for genre, count in genre_counts.most_common(5)]
        
        print(f"   Your Top Genres: {top_5}")
        return top_5
        
    except Exception as e:
        print(f"   Error analyzing taste: {e}")
        return ['pop']

def scout_genre_gems(target_genres):
    print(f"\n--- STEP 2: Running Dual-Engine Search ---")
    discovered_ids = []
    
    # ENGINE 1: The Time Machine (1990-2005)
    # Goal: Find "Popular Classics"
    for genre in target_genres:
        print(f"   [Classic Mode] Scouting 90s/00s {genre}...")
        query = f"year:1990-2005 genre:\"{genre}\""
        
        try:
            # We grab 10 candidates per genre
            results = sp.search(q=query, limit=10, type='track')
            tracks = results['tracks']['items']
            
            for t in tracks:
                # FILTER: Only keep tracks that are somewhat popular (>40)
                # This avoids obscure garage demos, giving you actual "Classics"
                if t['popularity'] > 40:
                    discovered_ids.append(t['id'])
                    print(f"     -> Found Classic: {t['name']} ({t['artists'][0]['name']})")
        except:
            continue

    # ENGINE 2: The Future (2024-2026)
    # Goal: Find "Fresh Finds"
    for genre in target_genres:
        print(f"   [Fresh Mode] Scouting new {genre}...")
        query = f"year:2024-2026 genre:\"{genre}\""
        
        try:
            results = sp.search(q=query, limit=10, type='track')
            tracks = results['tracks']['items']
            
            for t in tracks:
                # No popularity filter here - we want new stuff even if it's underground
                discovered_ids.append(t['id'])
                print(f"     -> Found Fresh: {t['name']} ({t['artists'][0]['name']})")
        except:
            continue
            
    # Shuffle the mix so you get a blend of Old vs New
    random.shuffle(discovered_ids)
    
    # Remove duplicates
    return list(set(discovered_ids))

def create_genre_playlist(track_ids):
    if not track_ids:
        print("No tracks found.")
        return

    user_id = sp.me()['id']
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    playlist_name = f"Bot Finds (Fresh & Classic) - {date_str}"
    
    try:
        playlist = sp.user_playlist_create(user_id, playlist_name, description="50% Classics (1990-2005) + 50% New Releases (2024+)")
        
        # Batch add (Spotify limit is 100 per request)
        for i in range(0, len(track_ids), 100):
            sp.playlist_add_items(playlist['id'], track_ids[i:i+100])
            
        print(f"\n--- SUCCESS! Created '{playlist_name}' with {len(track_ids)} songs. ---")
    except Exception as e:
        print(f"Error creating playlist: {e}")

if __name__ == "__main__":
    my_genres = get_top_genres()
    if my_genres:
        new_gems = scout_genre_gems(my_genres)
        create_genre_playlist(new_gems)