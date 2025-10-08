import requests
import os
from backend.celery_app import celery_app
from dotenv import load_dotenv

load_dotenv()

# News API configuration
NEWS_API_KEY = os.getenv('NEWS_API_KEY')  # Get from https://newsapi.org/
# GUARDIAN_API_KEY = os.getenv('GUARDIAN_API_KEY')  # Get from https://open-platform.theguardian.com/

@celery_app.task
def execute_news_task(task_args):
    try:
        query = task_args.get('query', '').lower()
        user_input = task_args.get('user_input', '')
        
        # Extract category or topic from query
        category = extract_news_category(query)
        search_query = extract_search_query(query, user_input)
        
        # Try to get real news from APIs
        news_result = get_real_news(category, search_query)
        
        if news_result:
            return news_result
        else:
            return "📰 Unable to fetch current news at the moment. Please try again later."
            
    except Exception as e:
        return f"❌ News task error: {str(e)}"

def get_real_news(category=None, search_query=None):
    """Get real news from NewsAPI or Guardian API"""
    
    # Try NewsAPI first
    newsapi_result = get_news_from_newsapi(category, search_query)
    if newsapi_result:
        return newsapi_result
    
    # Fallback to Guardian API
    guardian_result = get_news_from_guardian(category, search_query)
    if guardian_result:
        return guardian_result
    
    return None

def get_news_from_newsapi(category=None, search_query=None):
    """Get news from NewsAPI"""
    try:
        if not NEWS_API_KEY:
            return None
            
        base_url = "https://newsapi.org/v2/top-headlines"
        params = {
            'apiKey': NEWS_API_KEY,
            'pageSize': 5,
            'language': 'en'
        }
        
        # Add category or search query
        if category and category != 'general':
            params['category'] = category
        elif search_query:
            base_url = "https://newsapi.org/v2/everything"
            params['q'] = search_query
            params['sortBy'] = 'publishedAt'
        else:
            params['country'] = 'us'  # Default to US headlines
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['articles']:
                news_items = []
                for i, article in enumerate(data['articles'][:5], 1):
                    title = article['title'].split(' - ')[0]  # Remove source from title
                    source = article['source']['name']
                    # description = article['description'] or "No description available"
                    
                    news_items.append(f"{i}. **{title}**\n   📰 Source: {source}")
                
                category_display = category.capitalize() if category else "Latest"
                query_display = f" for '{search_query}'" if search_query else ""
                
                return f"📰 {category_display} News{query_display}:\n\n" + "\n\n".join(news_items)
        
        return None
        
    except Exception as e:
        print(f"NewsAPI error: {e}")
        return None

def get_news_from_guardian(category=None, search_query=None):
    """Get news from The Guardian API"""
    try:
        if not GUARDIAN_API_KEY:
            return None
            
        base_url = "https://content.guardianapis.com/search"
        params = {
            'api-key': GUARDIAN_API_KEY,
            'show-fields': 'headline,trailText',
            'page-size': 5,
            'format': 'json'
        }
        
        # Map categories to Guardian sections
        category_mapping = {
            'sports': 'sport',
            'technology': 'technology',
            'business': 'business',
            'science': 'science',
            'entertainment': 'culture',
            'health': 'society',
            'politics': 'politics'
        }
        
        if category and category in category_mapping:
            params['section'] = category_mapping[category]
        elif search_query:
            params['q'] = search_query
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['response']['results']:
                news_items = []
                for i, article in enumerate(data['response']['results'][:5], 1):
                    title = article['webTitle']
                    # trail_text = article['fields']['trailText'] if 'fields' in article else "No description available"
                    
                    news_items.append(f"{i}. **{title}**\n   📰 Source: The Guardian")
                
                category_display = category.capitalize() if category else "Latest"
                query_display = f" for '{search_query}'" if search_query else ""
                
                return f"📰 {category_display} News{query_display}:\n\n" + "\n\n".join(news_items)
        
        return None
        
    except Exception as e:
        print(f"Guardian API error: {e}")
        return None

def extract_news_category(query):
    """Extract news category from query"""
    categories = {
        'sports': ['sports', 'sport', 'football', 'basketball', 'cricket', 'tennis'],
        'technology': ['tech', 'technology', 'ai', 'artificial intelligence', 'computer', 'software'],
        'business': ['business', 'finance', 'market', 'economy', 'stocks'],
        'science': ['science', 'scientific', 'research', 'discovery'],
        'entertainment': ['entertainment', 'movie', 'music', 'celebrity', 'hollywood'],
        'health': ['health', 'medical', 'medicine', 'hospital', 'doctor'],
        'politics': ['politics', 'political', 'government', 'election']
    }
    
    query_lower = query.lower()
    
    for category, keywords in categories.items():
        if any(keyword in query_lower for keyword in keywords):
            return category
    
    return 'general'

def extract_search_query(query, user_input):
    """Extract search query from news request"""
    import re
    
    patterns = [
        r'news about\s+(.+)',
        r'news on\s+(.+)',
        r'latest about\s+(.+)',
        r'headlines for\s+(.+)',
        r'what\'s happening in\s+(.+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query.lower())
        if match:
            search_terms = match.group(1).strip()
            # Clean up the search terms
            search_terms = re.sub(r'[?.!]$', '', search_terms)
            return search_terms
    
    # If no specific search terms, check if it's a general news query
    if any(word in query.lower() for word in ['news', 'headlines', 'latest']):
        return None
    
    return user_input if user_input and user_input != query else None