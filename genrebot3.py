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
        print(f"   [Classic Mode] Scouting 80s/90s/00s for '{genre}'...")
        
        # We will try up to 2 variations of the genre name
        # Variation 1: The exact genre (e.g., "conscious hip hop")
        # Variation 2: The last word (e.g., "hop") - usually the root genre
        
        # Split genre into parts to create fallbacks
        search_terms = [genre]
        if " " in genre:
            search_terms.append(genre.split()[-1]) # Add the last word (e.g. "Pop" from "Indie Pop")
            
        found_for_this_genre = False
        
        for term in search_terms:
            if found_for_this_genre:
                break # Stop if we already found songs for this genre
                
            query = f"year:1980-2010 genre:\"{term}\""
            # If the simple genre search fails, try keyword search as a last resort
            if term != genre: 
                query = f"year:1980-2010 {term}"
            
            try:
                # print(f"      Debug: Trying query '{query}'...") 
                results = sp.search(q=query, limit=50, type='track')
                tracks = results['tracks']['items']
                
                if tracks:
                    # Sort by Popularity (High to Low) to find the "Hits"
                    # We accept slightly lower popularity (20) for older tracks
                    popular_tracks = [t for t in tracks if t['popularity'] > 20]
                    popular_tracks.sort(key=lambda x: x['popularity'], reverse=True)
                    
                    # Take the top 3
                    for t in popular_tracks[:3]:
                        if t['id'] not in discovered_ids:
                            discovered_ids.append(t['id'])
                            print(f"     -> Found Hit: {t['name']} - {t['artists'][0]['name']} (Pop: {t['popularity']})")
                            found_for_this_genre = True
            except:
                continue
        
        if not found_for_this_genre:
            print(f"     Could not find classic tracks for '{genre}' (It might be too new!)")

    # Shuffle and Return
    random.shuffle(discovered_ids)
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