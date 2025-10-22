from fastapi import APIRouter, HTTPException, Query
from youtubesearchpython import VideosSearch
from datetime import datetime
from backend.core.database import sync_music_collection
import re

router = APIRouter()

@router.get("/play-music/")
async def play_music(song_name: str = Query(..., description="Song name to search")):
    """
    Search for a song on YouTube and return the video URL
    """
    try:
        print(f"🎵 Searching for song: {song_name}")
        
        # Search YouTube
        videos_search = VideosSearch(song_name, limit=1)
        results = videos_search.result()
        
        if not results['result']:
            raise HTTPException(status_code=404, detail="No results found")
        
        # Get first result
        video = results['result'][0]
        video_data = {
            'title': video['title'],
            'url': video['link'],
            'duration': video.get('duration', 'Unknown'),
            'thumbnail': video.get('thumbnails', [{}])[0].get('url', ''),
            'channel': video.get('channel', {}).get('name', 'Unknown'),
            'search_query': song_name,
            'played_at': datetime.now()
        }
        
        # Store in MongoDB
        sync_music_collection.insert_one(video_data)
        
        return {
            "success": True,
            "song_title": video_data['title'],
            "youtube_url": video_data['url'],
            "duration": video_data['duration'],
            "channel": video_data['channel'],
            "thumbnail": video_data['thumbnail']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching music: {str(e)}")

@router.get("/recent-music/")
async def get_recent_music(limit: int = 10):
    """
    Get recently played songs
    """
    try:
        recent_songs = list(sync_music_collection.find()
                           .sort('played_at', -1)
                           .limit(limit))
        
        # Convert ObjectId to string
        for song in recent_songs:
            song['_id'] = str(song['_id'])
            song['played_at'] = song['played_at'].isoformat()
        
        return {"songs": recent_songs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent music: {str(e)}")