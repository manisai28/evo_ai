import yt_dlp
import re
import webbrowser
from backend.core.celery_app import celery_app
import logging
import threading

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='backend.tasks.music_tasks.play_music_task')
def play_music_task(self, task_args):
    """
    Music task that automatically opens YouTube and plays music
    """
    try:
        query = task_args.get('query', '')
        user_id = task_args.get('user_id', '')
        
        # Extract song name
        song_name = extract_song_name(query)
        if not song_name:
            return "🎵 Please specify a song name."
        
        logger.info(f"🔍 Searching for: {song_name}")
        
        # Search for the song
        result = simple_youtube_search(song_name)
        
        if result:
            video_id, title, youtube_url = result
            
            # Create auto-play URL
            autoplay_url = f"{youtube_url}&autoplay=1"
            
            # AUTO-OPEN YouTube in browser
            open_youtube_autoplay(autoplay_url)
            
            response = f"🎵 **Now Playing: {title}**\n\n✅ YouTube opened with '{title}' - enjoy the music! 🎧"
            return response
        else:
            return f"❌ Could not find '{song_name}'. Try: 'Shape of You', 'Blinding Lights', etc."
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

def open_youtube_autoplay(url):
    """
    Automatically open YouTube in default browser
    """
    try:
        # Open in background thread to avoid blocking
        def open_browser():
            try:
                webbrowser.open(url, new=2)  # new=2 opens in new tab
                logger.info(f"✅ YouTube opened: {url}")
            except Exception as e:
                logger.error(f"❌ Failed to open browser: {e}")
        
        # Start in separate thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
    except Exception as e:
        logger.error(f"❌ Browser open error: {e}")

def simple_youtube_search(song_name):
    """
    Simple YouTube search using yt-dlp
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch1:{song_name}", download=False)
            
            if result and 'entries' in result and result['entries']:
                video = result['entries'][0]
                video_id = extract_video_id(video['url'])
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                return video_id, video['title'], youtube_url
                
        return None
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return None

def extract_song_name(query):
    """Extract song name from query"""
    if not query:
        return None
    
    # Simple extraction - just remove "play" and clean up
    words = query.lower().split()
    if 'play' in words:
        words.remove('play')
    
    return ' '.join(words).strip().title()

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    try:
        if 'youtube.com/watch?v=' in url:
            return url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
        return None
    except:
        return None