import requests
import os
from backend.core.celery_app import celery_app
from dotenv import load_dotenv

load_dotenv()

# You can add API keys for enhanced search in .env
GOOGLE_SEARCH_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
GOOGLE_SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

@celery_app.task
def execute_search_task(task_args):
    try:
        query = task_args.get('query', '')
        user_input = task_args.get('user_input', '')
        
        # Extract search query
        search_terms = extract_search_terms(query, user_input)
        
        if not search_terms or search_terms.strip() == "":
            return "🔍 Please specify what you'd like me to search for. Example: 'search for AI trends' or 'find information about Python'"
        
        # Try to get real search results
        search_results = get_real_search_results(search_terms)
        
        if search_results:
            return search_results
        else:
            # Fallback to enhanced mock results with actual information
            return get_enhanced_search_results(search_terms)
        
    except Exception as e:
        return f"❌ Search task error: {str(e)}"

def get_real_search_results(search_terms):
    """Get real search results using Google Custom Search API"""
    try:
        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return None
            
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_SEARCH_API_KEY,
            'cx': GOOGLE_SEARCH_ENGINE_ID,
            'q': search_terms,
            'num': 5  # Get 5 results
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data and data['items']:
                results = []
                for i, item in enumerate(data['items'][:3], 1):  # Show top 3 results
                    title = item.get('title', 'No title')
                    link = item.get('link', '')
                    snippet = item.get('snippet', 'No description available')
                    
                    results.append(f"{i}. **{title}**\n   📝 {snippet}\n   🔗 {link}")
                
                return f"🔍 Search results for '{search_terms}':\n\n" + "\n\n".join(results)
        
        return None
        
    except Exception as e:
        print(f"Search API error: {e}")
        return None

def get_enhanced_search_results(search_terms):
    """Enhanced mock search results with actual information for common topics"""
    
    # Knowledge base for common topics
    knowledge_base = {
        # Technology
        "python": {
            "description": "Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, AI, and automation.",
            "key_points": [
                "Created by Guido van Rossum in 1991",
                "Uses indentation for code blocks",
                "Large ecosystem with libraries like NumPy, Pandas, Django",
                "Popular for machine learning and data analysis"
            ]
        },
        "artificial intelligence": {
            "description": "AI refers to machines that can perform tasks that typically require human intelligence, including learning, problem-solving, and pattern recognition.",
            "key_points": [
                "Includes machine learning, deep learning, and neural networks",
                "Used in voice assistants, recommendation systems, and autonomous vehicles",
                "Major companies: Google, OpenAI, Microsoft, Tesla",
                "Ethical considerations around bias and job displacement"
            ]
        },
        "machine learning": {
            "description": "Machine learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed.",
            "key_points": [
                "Three main types: supervised, unsupervised, and reinforcement learning",
                "Common algorithms: linear regression, decision trees, neural networks",
                "Applications: spam detection, image recognition, predictive analytics",
                "Frameworks: TensorFlow, PyTorch, Scikit-learn"
            ]
        },
        
        # Science
        "climate change": {
            "description": "Climate change refers to long-term shifts in temperatures and weather patterns, primarily caused by human activities like burning fossil fuels.",
            "key_points": [
                "Global temperatures rising due to greenhouse gases",
                "Effects: sea level rise, extreme weather, biodiversity loss",
                "Paris Agreement aims to limit warming to 1.5°C",
                "Renewable energy and conservation are key solutions"
            ]
        },
        "space exploration": {
            "description": "Space exploration involves discovering celestial structures in outer space through evolving space technology.",
            "key_points": [
                "Major agencies: NASA, ESA, ISRO, SpaceX",
                "Recent achievements: Mars rovers, James Webb Telescope, commercial spaceflight",
                "Future goals: Moon base, Mars colonization, asteroid mining",
                "International Space Station has been continuously occupied since 2000"
            ]
        },
        
        # Health
        "meditation": {
            "description": "Meditation is a practice where an individual uses techniques to focus attention and achieve a mentally clear and emotionally calm state.",
            "key_points": [
                "Reduces stress and anxiety",
                "Improves concentration and emotional well-being",
                "Various types: mindfulness, transcendental, loving-kindness",
                "Can be practiced anywhere, requires no equipment"
            ]
        },
        
        # General Knowledge
        "renaissance": {
            "description": "The Renaissance was a period in European history marking the transition from the Middle Ages to modernity, covering the 15th and 16th centuries.",
            "key_points": [
                "Began in Italy and spread throughout Europe",
                "Revival of classical learning and wisdom",
                "Key figures: Leonardo da Vinci, Michelangelo, Shakespeare",
                "Major developments in art, science, and philosophy"
            ]
        }
    }
    
    # Check if we have information about the search terms
    search_lower = search_terms.lower()
    
    for topic, info in knowledge_base.items():
        if topic in search_lower:
            key_points = "\n".join([f"   • {point}" for point in info['key_points']])
            return f"""🔍 Information about '{search_terms.title()}':

📖 {info['description']}

💡 Key Points:
{key_points}

💡 Try searching for: {get_related_topics(topic)}"""
    
    # General search response for unknown topics
    return f"""🔍 Search results for '{search_terms}':

1. **Wikipedia: {search_terms.title()}**
   📝 Comprehensive information about {search_terms} with history, key facts, and related topics
   🔗 https://en.wikipedia.org/wiki/{search_terms.replace(' ', '_')}

2. **Latest News about {search_terms.title()}**
   📝 Current articles and recent developments related to {search_terms}
   🔗 https://news.google.com/search?q={search_terms.replace(' ', '+')}

3. **Academic Research on {search_terms.title()}**
   📝 Scholarly papers and scientific studies about {search_terms}
   🔗 https://scholar.google.com/scholar?q={search_terms.replace(' ', '+')}

💡 Tip: For more specific results, try being more detailed in your search query."""

def get_related_topics(topic):
    """Get related topics for suggestions"""
    related_map = {
        "python": "Django, Flask, data science, automation",
        "artificial intelligence": "machine learning, neural networks, robotics, computer vision",
        "machine learning": "deep learning, AI algorithms, data mining, predictive analytics",
        "climate change": "global warming, renewable energy, sustainability, carbon footprint",
        "space exploration": "NASA, SpaceX, astronomy, astrophysics",
        "meditation": "mindfulness, yoga, mental health, stress relief",
        "renaissance": "art history, Leonardo da Vinci, Michelangelo, humanism"
    }
    return related_map.get(topic, "related topics and recent developments")

def extract_search_terms(query, user_input):
    """Extract search terms from query with improved patterns"""
    import re
    
    patterns = [
        r'search for\s+(.+)',
        r'find\s+(.+)',
        r'look up\s+(.+)',
        r'information about\s+(.+)',
        r'what is\s+(.+)',
        r'who is\s+(.+)',
        r'how to\s+(.+)',
        r'explain\s+(.+)',
        r'tell me about\s+(.+)',
        r'can you find\s+(.+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query.lower())
        if match:
            terms = match.group(1).strip()
            # Clean up the terms
            terms = re.sub(r'[?.!]$', '', terms)
            return terms
    
    # If no pattern matched but it's clearly a search query
    if any(word in query.lower() for word in ['search', 'find', 'look up', 'information', 'what is', 'who is']):
        return user_input
    
    return user_input