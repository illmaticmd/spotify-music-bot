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
        results = sp.current_user_top_artists(limit=50, time_range='medium_term')
        
        if not results['items']:
            results = sp.current_user_top_artists(limit=50, time_range='long_term')
            
        if not results['items']:
            return ['pop'] # Fallback

        all_genres = []
        for artist in results['items']:
            all_genres.extend(artist['genres'])
            
        # Grab the Top 7 Genres
        genre_counts = Counter(all_genres)
        top_7 = [genre for genre, count in genre_counts.most_common(7)]
        
        print(f"   Your Top 7 Genres: {top_7}")
        return top_7
        
    except Exception as e:
        print(f"   Error analyzing taste: {e}")
        return ['pop']

def scout_vintage_gems(target_genres):
    print(f"\n--- STEP 2: The Time Machine (1980-2010) ---")
    discovered_ids = []
    
    for genre in target_genres:
        print(f"   [Classic Mode] Scouting 80s/90s/00s '{genre}'...")
        
        # STRATEGY 1: Strict Genre Search
        query = f"year:1980-2010 genre:\"{genre}\""
        
        try:
            # Fetch MAX limit (50) to increase odds of finding hits
            results = sp.search(q=query, limit=50, type='track')
            tracks = results['tracks']['items']
            
            # If Strict Search failed (0 results), try STRATEGY 2: Keyword Search
            if not tracks:
                print(f"     Strict search failed. Trying keyword search for '{genre}'...")
                # Search the genre name as a keyword + year range
                query_fallback = f"{genre} year:1980-2010"
                results = sp.search(q=query_fallback, limit=50, type='track')
                tracks = results['tracks']['items']

            # If we found tracks, let's find the "Hits" among them
            if tracks:
                # SORT by popularity (Highest to Lowest)
                sorted_tracks = sorted(tracks, key=lambda x: x['popularity'], reverse=True)
                
                # Take the Top 5 most popular from this batch
                top_hits = sorted_tracks[:5]
                
                for t in top_hits:
                    # Optional: Still ignore things with 0 popularity (broken tracks)
                    if t['popularity'] > 10:
                        discovered_ids.append(t['id'])
                        print(f"     -> Found Hit: {t['name']} - {t['artists'][0]['name']} (Pop: {t['popularity']})")
            else:
                print(f"     No tracks found for {genre} even with fallback.")
                
        except Exception as e:
            print(f"     Error searching {genre}: {e}")
            continue

    # Shuffle to mix genres
    random.shuffle(discovered_ids)
    
    # Remove duplicates
    return list(set(discovered_ids))

def create_vintage_playlist(track_ids):
    if not track_ids:
        print("No tracks found.")
        return

    user_id = sp.me()['id']
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    playlist_name = f"Bot Finds (Golden Era Classics) - {date_str}"
    
    try:
        playlist = sp.user_playlist_create(user_id, playlist_name, description="Popular Oldies (1980-2010) based on your Top 7 Genres.")
        
        # Batch add (Spotify limit is 100 per request)
        for i in range(0, len(track_ids), 100):
            sp.playlist_add_items(playlist['id'], track_ids[i:i+100])
            
        print(f"\n--- SUCCESS! Created '{playlist_name}' with {len(track_ids)} songs. ---")
    except Exception as e:
        print(f"Error creating playlist: {e}")

if __name__ == "__main__":
    my_genres = get_top_genres()
    if my_genres:
        vintage_gems = scout_vintage_gems(my_genres)
        create_vintage_playlist(vintage_gems)