from langchain_core.tools import tool
from typing import List, Dict, Any
import re
from database import (
    log_mood_entry, 
    get_recent_entries, 
    get_entries_by_count,
    analyze_mood_patterns
)

# Crisis intervention keywords and resources
CRISIS_KEYWORDS = [
    'suicide', 'kill myself', 'end it all', 'no point living', 'want to die',
    'hurt myself', 'self harm', 'self-harm', 'overdose', 'end my life',
    'better off dead', 'can\'t go on', 'nothing matters', 'hopeless',
    'worthless', 'everyone would be better without me'
]

CRISIS_RESOURCES = {
    "US": {
        "National Suicide Prevention Lifeline": "988",
        "Crisis Text Line": "Text HOME to 741741",
        "SAMHSA National Helpline": "1-800-662-4357"
    },
    "International": {
        "International Association for Suicide Prevention": "https://www.iasp.info/resources/Crisis_Centres/",
        "Befrienders Worldwide": "https://www.befrienders.org/"
    }
}

@tool
def mood_logger_tool(mood_label: str, mood_reason: str, problem_category: str = "") -> str:
    """
    Log a user's mood entry into the database.
    
    Args:
        mood_label: The user's current mood (e.g., "Happy", "Sad", "Stressed")
        mood_reason: Detailed description of why the user feels this way
        problem_category: Category of the problem (e.g., "work", "relationships", "health")
    
    Returns:
        Confirmation message of the logged entry
    """
    try:
        entry_id = log_mood_entry(mood_label, mood_reason, problem_category)
        return f"Mood entry logged successfully (ID: {entry_id}). I've recorded that you're feeling {mood_label} because {mood_reason}."
    except Exception as e:
        return f"Error logging mood entry: {str(e)}"

@tool
def query_history_tool(time_period: str = "week") -> str:
    """
    Query historical mood entries based on time period.
    
    Args:
        time_period: "week" for last 7 entries, "month" for last 30 entries, 
                    or specific number like "5" for last 5 entries
    
    Returns:
        Formatted string of historical mood entries
    """
    try:
        # Parse time period
        if time_period.lower() == "week":
            count = 7
        elif time_period.lower() == "month":
            count = 30
        elif time_period.isdigit():
            count = int(time_period)
        else:
            count = 7  # Default to week
        
        entries = get_entries_by_count(count)
        
        if not entries:
            return "No mood entries found in your history."
        
        # Format entries for analysis
        history_text = f"Your last {len(entries)} mood entries:\n"
        for i, entry in enumerate(entries, 1):
            history_text += f"{i}. Mood: {entry[1]}, Reason: {entry[2]}, Category: {entry[4] or 'General'}\n"
        
        return history_text
    except Exception as e:
        return f"Error querying history: {str(e)}"

@tool
def generate_insight_tool(time_period: str = "week") -> str:
    """
    Generate personalized insights based on historical mood data.
    
    Args:
        time_period: Time period to analyze ("week", "month", or number)
    
    Returns:
        Personalized insights and patterns from mood history
    """
    try:
        # Get historical data
        history = query_history_tool(time_period)
        
        if "No mood entries found" in history:
            return "I don't have enough data yet to provide insights. Let's start by talking about how you're feeling today!"
        
        # Analyze patterns using database function
        patterns = analyze_mood_patterns(7 if time_period == "week" else 30)
        
        insight = f"Based on your recent {time_period}, here are some patterns I've noticed:\n\n"
        
        if patterns['most_common_mood']:
            insight += f"• Your most frequent mood has been '{patterns['most_common_mood']}'\n"
        
        if patterns['common_categories']:
            insight += f"• Main areas of concern: {', '.join(patterns['common_categories'])}\n"
        
        if patterns['mood_trend']:
            insight += f"• Overall trend: {patterns['mood_trend']}\n"
        
        # Add personalized recommendations
        insight += "\n💡 Based on these patterns, I'd like to explore some coping strategies with you."
        
        return insight
    except Exception as e:
        return f"Error generating insights: {str(e)}"

@tool
def recommend_support_tool(mood_label: str, problem_category: str = "") -> str:
    """
    Provide tailored support recommendations based on user's mood.
    
    Args:
        mood_label: Current mood of the user
        problem_category: Category of the problem they're facing
    
    Returns:
        Personalized recommendations and coping strategies
    """
    recommendations = []
    mood_lower = mood_label.lower()
    
    # Mood-specific recommendations
    if any(word in mood_lower for word in ['sad', 'depressed', 'down', 'blue']):
        recommendations.extend([
            "Try the 4-7-8 breathing technique: Inhale for 4, hold for 7, exhale for 8",
            "Journal prompt: Write about three small things that brought you comfort recently",
            "Consider a gentle walk outside or some light stretching",
            "Listen to uplifting music or a guided meditation"
        ])
    
    elif any(word in mood_lower for word in ['anxious', 'stressed', 'worried', 'nervous']):
        recommendations.extend([
            "Practice grounding: Name 5 things you see, 4 you hear, 3 you touch, 2 you smell, 1 you taste",
            "Try progressive muscle relaxation starting from your toes",
            "Deep breathing: Breathe in slowly through your nose, out through your mouth",
            "Journal prompt: What are three things within your control right now?"
        ])
    
    elif any(word in mood_lower for word in ['angry', 'frustrated', 'irritated', 'mad']):
        recommendations.extend([
            "Try the STOP technique: Stop, Take a breath, Observe, Proceed mindfully",
            "Physical release: Do jumping jacks, squeeze a stress ball, or punch a pillow",
            "Journal prompt: What triggered this feeling and what would help resolve it?",
            "Cool down strategy: Splash cold water on your face or hold an ice cube"
        ])
    
    elif any(word in mood_lower for word in ['happy', 'joyful', 'excited', 'good']):
        recommendations.extend([
            "Savor this moment: Take a mental snapshot of how you feel right now",
            "Journal prompt: What contributed to this positive feeling?",
            "Share your joy: Consider telling someone about what's making you happy",
            "Practice gratitude: Write down three things you're grateful for today"
        ])
    
    else:
        # Default recommendations
        recommendations.extend([
            "Take a few minutes for mindful breathing",
            "Journal about your current thoughts and feelings",
            "Consider what your body and mind need right now",
            "Practice self-compassion and be gentle with yourself"
        ])
    
    # Category-specific recommendations
    if "work" in problem_category.lower():
        recommendations.append("Work stress tip: Try the Pomodoro technique - 25 minutes focused work, 5 minute break")
    elif "relationship" in problem_category.lower():
        recommendations.append("Relationship tip: Practice 'I feel' statements instead of 'You always/never' statements")
    elif "health" in problem_category.lower():
        recommendations.append("Health anxiety tip: Focus on what you can control - rest, nutrition, and gentle movement")
    
    return "Here are some personalized recommendations for you:\n" + "\n".join([f"• {rec}" for rec in recommendations[:4]])

@tool
def search_content_tool(query: str, mood_context: str = "") -> str:
    """
    Search for relevant mental health content and resources.
    
    Args:
        query: Search query for relevant content
        mood_context: User's current mood context for better results
    
    Returns:
        Curated content suggestions with links
    """
    # Simulated content suggestions (in a real implementation, this would use web search)
    content_library = {
        "anxiety": [
            "10 Minute Guided Meditation for Anxiety - https://example.com/anxiety-meditation",
            "Understanding Anxiety: What Your Body Is Telling You - https://example.com/anxiety-guide",
            "Calming Music Playlist for Stress Relief - https://example.com/calming-music"
        ],
        "depression": [
            "Gentle Yoga for Depression and Low Energy - https://example.com/depression-yoga",
            "The Science of Depression: You're Not Broken - https://example.com/depression-science",
            "Uplifting Podcasts for Mental Health - https://example.com/mental-health-podcasts"
        ],
        "stress": [
            "Quick Stress Relief Techniques That Actually Work - https://example.com/stress-relief",
            "Work-Life Balance: Setting Healthy Boundaries - https://example.com/work-balance",
            "Progressive Muscle Relaxation Guide - https://example.com/muscle-relaxation"
        ],
        "sleep": [
            "Better Sleep Hygiene: A Complete Guide - https://example.com/sleep-hygiene",
            "Sleep Stories and Relaxation Techniques - https://example.com/sleep-stories",
            "Understanding Sleep and Mental Health Connection - https://example.com/sleep-mental-health"
        ]
    }
    
    # Find relevant content based on query and mood
    query_lower = query.lower()
    mood_lower = mood_context.lower()
    
    suggestions = []
    
    for category, links in content_library.items():
        if category in query_lower or category in mood_lower:
            suggestions.extend(links[:2])  # Limit to 2 per category
    
    if not suggestions:
        # Default suggestions
        suggestions = [
            "Mindfulness 101: Getting Started - https://example.com/mindfulness-guide",
            "Self-Care Strategies for Mental Wellness - https://example.com/self-care",
            "Building Emotional Resilience - https://example.com/resilience"
        ]
    
    content_text = "Here are some helpful resources I found for you:\n"
    content_text += "\n".join([f"• {suggestion}" for suggestion in suggestions[:3]])
    content_text += "\n\nRemember, these are supplementary resources. Professional help is always available if you need it."
    
    return content_text

@tool
def crisis_mode_tool(user_message: str) -> str:
    """
    CRITICAL: Immediate crisis intervention tool for detecting and responding to crisis situations.
    
    Args:
        user_message: The user's message to scan for crisis indicators
    
    Returns:
        Crisis intervention response with immediate resources
    """
    message_lower = user_message.lower()
    
    # Check for crisis keywords
    crisis_detected = any(keyword in message_lower for keyword in CRISIS_KEYWORDS)
    
    if crisis_detected:
        crisis_response = """
🚨 IMMEDIATE CRISIS SUPPORT 🚨

I'm very concerned about what you've shared. Your life has value and there are people who want to help you right now.

IMMEDIATE HELP:
• National Suicide Prevention Lifeline: 988 (US)
• Crisis Text Line: Text HOME to 741741
• Emergency Services: 911

INTERNATIONAL:
• International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/
• Befrienders Worldwide: https://www.befrienders.org/

Please reach out to one of these resources immediately. You don't have to go through this alone.

If you're not in immediate danger but need support, consider:
• Calling a trusted friend or family member
• Going to your nearest emergency room
• Contacting your mental health provider

You matter. Your life matters. Help is available.
        """
        return crisis_response.strip()
    
    return "No crisis indicators detected. Continue with normal supportive conversation."