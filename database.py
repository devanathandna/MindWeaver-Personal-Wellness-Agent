import sqlite3
import os
from typing import List, Tuple, Dict, Any
from datetime import datetime

DATABASE_NAME = "mood_data.db"

def init_database():
    """Initialize the SQLite database with the mood_logs table."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Create mood_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mood_label TEXT NOT NULL,
            mood_reason TEXT NOT NULL,
            agent_response TEXT DEFAULT '',
            problem_category TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_NAME}' initialized successfully.")

def log_mood_entry(mood_label: str, mood_reason: str, problem_category: str = "", agent_response: str = "") -> int:
    """
    Log a new mood entry to the database.
    
    Args:
        mood_label: The user's mood (e.g., "Happy", "Sad", "Stressed")
        mood_reason: Description of why they feel this way
        problem_category: Category of the problem (e.g., "work", "relationships")
        agent_response: The agent's response to this entry
    
    Returns:
        The ID of the newly created entry
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO mood_logs (mood_label, mood_reason, agent_response, problem_category)
        VALUES (?, ?, ?, ?)
    ''', (mood_label, mood_reason, agent_response, problem_category))
    
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return entry_id

def get_recent_entries(days: int = 7) -> List[Tuple]:
    """
    Get mood entries from the last N days.
    
    Args:
        days: Number of days to look back
    
    Returns:
        List of tuples containing mood entry data
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, mood_label, mood_reason, agent_response, problem_category, created_at
        FROM mood_logs
        WHERE created_at >= datetime('now', '-{} days')
        ORDER BY created_at DESC
    '''.format(days))
    
    entries = cursor.fetchall()
    conn.close()
    
    return entries

def get_entries_by_count(count: int = 10) -> List[Tuple]:
    """
    Get the most recent N mood entries.
    
    Args:
        count: Number of entries to retrieve
    
    Returns:
        List of tuples containing mood entry data
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, mood_label, mood_reason, agent_response, problem_category, created_at
        FROM mood_logs
        ORDER BY id DESC
        LIMIT ?
    ''', (count,))
    
    entries = cursor.fetchall()
    conn.close()
    
    return entries

def get_all_entries() -> List[Tuple]:
    """
    Get all mood entries from the database.
    
    Returns:
        List of tuples containing all mood entry data
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, mood_label, mood_reason, agent_response, problem_category, created_at
        FROM mood_logs
        ORDER BY created_at DESC
    ''')
    
    entries = cursor.fetchall()
    conn.close()
    
    return entries

def update_agent_response(entry_id: int, agent_response: str) -> bool:
    """
    Update the agent response for a specific mood entry.
    
    Args:
        entry_id: ID of the mood entry to update
        agent_response: The agent's response to store
    
    Returns:
        True if update was successful, False otherwise
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE mood_logs
        SET agent_response = ?
        WHERE id = ?
    ''', (agent_response, entry_id))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def analyze_mood_patterns(entry_count: int = 7) -> Dict[str, Any]:
    """
    Analyze mood patterns from recent entries.
    
    Args:
        entry_count: Number of recent entries to analyze
    
    Returns:
        Dictionary containing mood pattern analysis
    """
    entries = get_entries_by_count(entry_count)
    
    if not entries:
        return {
            'most_common_mood': None,
            'common_categories': [],
            'mood_trend': 'No data available',
            'total_entries': 0
        }
    
    # Extract mood labels and categories
    mood_labels = [entry[1] for entry in entries]
    categories = [entry[4] for entry in entries if entry[4]]
    
    # Find most common mood
    mood_counts = {}
    for mood in mood_labels:
        mood_counts[mood] = mood_counts.get(mood, 0) + 1
    
    most_common_mood = max(mood_counts, key=mood_counts.get) if mood_counts else None
    
    # Find common categories
    category_counts = {}
    for category in categories:
        if category:
            category_counts[category] = category_counts.get(category, 0) + 1
    
    common_categories = sorted(category_counts.keys(), key=lambda x: category_counts[x], reverse=True)[:3]
    
    # Simple trend analysis (based on mood positivity)
    positive_moods = ['happy', 'joyful', 'excited', 'content', 'peaceful', 'grateful']
    negative_moods = ['sad', 'depressed', 'anxious', 'stressed', 'angry', 'frustrated', 'worried']
    
    recent_moods = mood_labels[:3]  # Last 3 entries
    older_moods = mood_labels[3:6] if len(mood_labels) > 3 else []
    
    def mood_score(moods):
        score = 0
        for mood in moods:
            mood_lower = mood.lower()
            if any(pos in mood_lower for pos in positive_moods):
                score += 1
            elif any(neg in mood_lower for neg in negative_moods):
                score -= 1
        return score
    
    recent_score = mood_score(recent_moods)
    older_score = mood_score(older_moods) if older_moods else 0
    
    if recent_score > older_score:
        trend = "improving"
    elif recent_score < older_score:
        trend = "concerning - may need additional support"
    else:
        trend = "stable"
    
    return {
        'most_common_mood': most_common_mood,
        'common_categories': common_categories,
        'mood_trend': trend,
        'total_entries': len(entries),
        'mood_distribution': mood_counts,
        'category_distribution': category_counts
    }

def search_entries_by_mood(mood_label: str) -> List[Tuple]:
    """
    Search for entries with a specific mood label.
    
    Args:
        mood_label: The mood to search for
    
    Returns:
        List of matching mood entries
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, mood_label, mood_reason, agent_response, problem_category, created_at
        FROM mood_logs
        WHERE mood_label LIKE ?
        ORDER BY created_at DESC
    ''', (f'%{mood_label}%',))
    
    entries = cursor.fetchall()
    conn.close()
    
    return entries

def search_entries_by_category(category: str) -> List[Tuple]:
    """
    Search for entries with a specific problem category.
    
    Args:
        category: The category to search for
    
    Returns:
        List of matching mood entries
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, mood_label, mood_reason, agent_response, problem_category, created_at
        FROM mood_logs
        WHERE problem_category LIKE ?
        ORDER BY created_at DESC
    ''', (f'%{category}%',))
    
    entries = cursor.fetchall()
    conn.close()
    
    return entries

def get_database_stats() -> Dict[str, Any]:
    """
    Get statistics about the mood database.
    
    Returns:
        Dictionary containing database statistics
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Total entries
    cursor.execute('SELECT COUNT(*) FROM mood_logs')
    total_entries = cursor.fetchone()[0]
    
    # Most recent entry
    cursor.execute('SELECT created_at FROM mood_logs ORDER BY created_at DESC LIMIT 1')
    latest_entry = cursor.fetchone()
    latest_date = latest_entry[0] if latest_entry else None
    
    # Mood distribution
    cursor.execute('SELECT mood_label, COUNT(*) FROM mood_logs GROUP BY mood_label ORDER BY COUNT(*) DESC')
    mood_stats = cursor.fetchall()
    
    # Category distribution
    cursor.execute('SELECT problem_category, COUNT(*) FROM mood_logs WHERE problem_category != "" GROUP BY problem_category ORDER BY COUNT(*) DESC')
    category_stats = cursor.fetchall()
    
    conn.close()
    
    return {
        'total_entries': total_entries,
        'latest_entry_date': latest_date,
        'mood_distribution': dict(mood_stats),
        'category_distribution': dict(category_stats)
    }

def delete_entry(entry_id: int) -> bool:
    """
    Delete a specific mood entry.
    
    Args:
        entry_id: ID of the entry to delete
    
    Returns:
        True if deletion was successful, False otherwise
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM mood_logs WHERE id = ?', (entry_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def clear_all_entries() -> int:
    """
    Clear all mood entries from the database.
    
    Returns:
        Number of entries deleted
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM mood_logs')
    count = cursor.fetchone()[0]
    
    cursor.execute('DELETE FROM mood_logs')
    conn.commit()
    conn.close()
    
    return count

# Utility functions for database maintenance
def backup_database(backup_filename: str = None) -> str:
    """
    Create a backup of the mood database.
    
    Args:
        backup_filename: Optional custom filename for backup
    
    Returns:
        Path to the backup file
    """
    if backup_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"mood_data_backup_{timestamp}.db"
    
    import shutil
    shutil.copy2(DATABASE_NAME, backup_filename)
    
    return backup_filename

def restore_database(backup_filename: str) -> bool:
    """
    Restore database from a backup file.
    
    Args:
        backup_filename: Path to the backup file
    
    Returns:
        True if restoration was successful, False otherwise
    """
    try:
        import shutil
        if os.path.exists(backup_filename):
            shutil.copy2(backup_filename, DATABASE_NAME)
            return True
        return False
    except Exception:
        return False

def export_to_csv(filename: str = None) -> str:
    """
    Export mood data to CSV format.
    
    Args:
        filename: Optional custom filename for export
    
    Returns:
        Path to the exported CSV file
    """
    import csv
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mood_export_{timestamp}.csv"
    
    entries = get_all_entries()
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['ID', 'Mood Label', 'Mood Reason', 'Agent Response', 'Problem Category', 'Created At'])
        
        # Write data
        for entry in entries:
            writer.writerow(entry)
    
    return filename

def import_from_csv(filename: str) -> int:
    """
    Import mood data from CSV format.
    
    Args:
        filename: Path to the CSV file to import
    
    Returns:
        Number of entries imported
    """
    import csv
    
    if not os.path.exists(filename):
        return 0
    
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    imported_count = 0
    
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            try:
                cursor.execute('''
                    INSERT INTO mood_logs (mood_label, mood_reason, agent_response, problem_category)
                    VALUES (?, ?, ?, ?)
                ''', (
                    row.get('Mood Label', ''),
                    row.get('Mood Reason', ''),
                    row.get('Agent Response', ''),
                    row.get('Problem Category', '')
                ))
                imported_count += 1
            except sqlite3.Error:
                continue  # Skip invalid rows
    
    conn.commit()
    conn.close()
    
    return imported_count

# Test functions for development
def populate_sample_data():
    """Populate database with sample data for testing."""
    sample_entries = [
        ("Happy", "Had a great day at work and finished my project", "work"),
        ("Stressed", "Too many deadlines coming up and feeling overwhelmed", "work"),
        ("Sad", "Missing my family who live far away", "relationships"),
        ("Anxious", "Worried about my health after reading medical articles online", "health"),
        ("Content", "Enjoyed a peaceful evening reading a good book", "leisure"),
        ("Frustrated", "Traffic was terrible and made me late for everything", "daily_life"),
        ("Grateful", "Had dinner with good friends and felt very supported", "relationships"),
        ("Tired", "Haven't been sleeping well due to work stress", "sleep"),
        ("Excited", "Got accepted for a course I really wanted to take", "personal_growth"),
        ("Lonely", "Spending too much time alone and missing social connections", "relationships")
    ]
    
    for mood, reason, category in sample_entries:
        log_mood_entry(mood, reason, category)
    
    print(f"Added {len(sample_entries)} sample entries to the database.")

if __name__ == "__main__":
    # Initialize database and run basic tests
    init_database()
    
    # Test basic functionality
    print("Testing database functionality...")
    
    # Add a test entry
    test_id = log_mood_entry("Test Mood", "This is a test entry", "testing")
    print(f"Test entry created with ID: {test_id}")
    
    # Retrieve recent entries
    recent = get_recent_entries(1)
    print(f"Recent entries: {len(recent)}")
    
    # Get database stats
    stats = get_database_stats()
    print(f"Database stats: {stats}")
    
    # Clean up test entry
    delete_entry(test_id)
    print("Test entry deleted.")
    
    print("Database functionality test completed successfully!")