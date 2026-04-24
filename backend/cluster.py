import duckdb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import datetime
import uuid
import pytz
import re

def get_topic(title):
    title_lower = title.lower()
    if re.search(r'\b(war|attack|military|strike|forces|troops|missile|gaza|israel|ukraine|russia)\b', title_lower):
        return 'War'
    if re.search(r'\b(economy|inflation|bank|fed|stocks|market|business|trade)\b', title_lower):
        return 'Economy'
    if re.search(r'\b(ai|tech|apple|google|microsoft|cyber|software|chip)\b', title_lower):
        return 'Tech'
    if re.search(r'\b(election|vote|biden|trump|parliament|congress|minister|policy)\b', title_lower):
        return 'Politics'
    return 'Other'

def is_similar(title1, title2, vectorizer=None):
    if not vectorizer:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
    try:
        X = vectorizer.fit_transform([title1, title2])
        sim = cosine_similarity(X[0:1], X[1:2])[0][0]
        return sim
    except ValueError: # Empty vocabulary etc.
        return 0.0

def cluster_and_save(new_articles, db_path='news.duckdb'):
    conn = duckdb.connect(db_path)
    
    # Load recent articles to match against (last 7 days)
    recent_df = conn.execute('''
        SELECT id, title, published_at, event_id 
        FROM articles 
        WHERE published_at > current_timestamp - interval '7 days'
    ''').df()
    
    # Filter out new_articles that are already in DB by URL
    existing_urls = set(conn.execute('SELECT url FROM articles').df()['url'].tolist())
    
    unique_articles = []
    seen_new_urls = set()
    for a in new_articles:
        if a['url'] not in existing_urls and a['url'] not in seen_new_urls:
            unique_articles.append(a)
            seen_new_urls.add(a['url'])
            
    articles_to_process = unique_articles
    
    if not articles_to_process:
        print("No new articles to process.")
        conn.close()
        return

    print(f"Processing {len(articles_to_process)} new articles...")
    
    new_events = []
    
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2))

    # Helper to convert pandas timestamp to aware datetime
    def ensure_aware(dt):
        if pd.isna(dt):
            return datetime.datetime.now(pytz.utc)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=pytz.utc)
        return dt

    import pandas as pd
    
    for article in articles_to_process:
        assigned_event_id = None
        best_sim = 0.0
        
        # Check against recent_df
        if not recent_df.empty:
            titles = recent_df['title'].tolist()
            titles.append(article['title'])
            
            try:
                X = vectorizer.fit_transform(titles)
                sims = cosine_similarity(X[-1:], X[:-1])[0]
                
                # Find the best match
                for idx, sim in enumerate(sims):
                    if sim > 0.2:
                        db_pub = ensure_aware(recent_df.iloc[idx]['published_at'])
                        art_pub = article['published_at']
                        time_diff = abs((art_pub - db_pub).total_seconds()) / 3600 # hours
                        
                        if time_diff < 24 and sim > best_sim:
                            best_sim = sim
                            assigned_event_id = recent_df.iloc[idx]['event_id']
            except ValueError:
                pass
                
        # If still not assigned, check against newly created events in this run
        if not assigned_event_id and new_events:
            event_titles = [e['title'] for e in new_events]
            event_titles.append(article['title'])
            try:
                X = vectorizer.fit_transform(event_titles)
                sims = cosine_similarity(X[-1:], X[:-1])[0]
                for idx, sim in enumerate(sims):
                    if sim > 0.2:
                        ev_pub = new_events[idx]['created_at']
                        art_pub = article['published_at']
                        time_diff = abs((art_pub - ev_pub).total_seconds()) / 3600
                        if time_diff < 24 and sim > best_sim:
                            best_sim = sim
                            assigned_event_id = new_events[idx]['id']
            except ValueError:
                pass

        if not assigned_event_id:
            # Create new event
            assigned_event_id = str(uuid.uuid4())
            new_event = {
                'id': assigned_event_id,
                'title': article['title'], # For now, use the first article's title as event title
                'topic': get_topic(article['title']),
                'created_at': article['published_at']
            }
            new_events.append(new_event)
            
        article['event_id'] = assigned_event_id
        
        # We can append this article to recent_df to match future articles in this loop
        new_row = pd.DataFrame([{
            'id': article['id'], 
            'title': article['title'], 
            'published_at': article['published_at'], 
            'event_id': assigned_event_id
        }])
        recent_df = pd.concat([recent_df, new_row], ignore_index=True)

    # Cluster events into stories
    new_stories = []
    if new_events:
        existing_stories = conn.execute('SELECT id, title FROM stories').df()
        for ev in new_events:
            assigned_story_id = None
            if not existing_stories.empty:
                titles = existing_stories['title'].tolist()
                titles.append(ev['title'])
                try:
                    X = vectorizer.fit_transform(titles)
                    sims = cosine_similarity(X[-1:], X[:-1])[0]
                    best_sim = 0.1 # Low threshold for long-term thematic grouping
                    for idx, sim in enumerate(sims):
                        if sim > best_sim:
                            best_sim = sim
                            assigned_story_id = existing_stories.iloc[idx]['id']
                except ValueError:
                    pass
                    
            if not assigned_story_id and new_stories:
                titles = [s['title'] for s in new_stories]
                titles.append(ev['title'])
                try:
                    X = vectorizer.fit_transform(titles)
                    sims = cosine_similarity(X[-1:], X[:-1])[0]
                    best_sim = 0.1
                    for idx, sim in enumerate(sims):
                        if sim > best_sim:
                            best_sim = sim
                            assigned_story_id = new_stories[idx]['id']
                except ValueError:
                    pass
                    
            if not assigned_story_id:
                assigned_story_id = str(uuid.uuid4())
                new_stories.append({
                    'id': assigned_story_id,
                    'title': ev['title'],
                    'topic': ev['topic'],
                    'created_at': ev['created_at']
                })
            
            ev['story_id'] = assigned_story_id

    # Insert new stories
    if new_stories:
        print(f"Creating {len(new_stories)} new stories.")
        conn.executemany('''
            INSERT INTO stories (id, title, topic, created_at) VALUES (?, ?, ?, ?)
        ''', [(s['id'], s['title'], s['topic'], s['created_at']) for s in new_stories])

    # Insert new events
    if new_events:
        print(f"Creating {len(new_events)} new events.")
        conn.executemany('''
            INSERT INTO events (id, story_id, title, topic, created_at) VALUES (?, ?, ?, ?, ?)
        ''', [(e['id'], e['story_id'], e['title'], e['topic'], e['created_at']) for e in new_events])
        
    # Insert new articles
    print(f"Inserting {len(articles_to_process)} articles.")
    conn.executemany('''
        INSERT INTO articles (id, title, source, url, published_at, event_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [(a['id'], a['title'], a['source'], a['url'], a['published_at'], a['event_id']) for a in articles_to_process])
    
    conn.close()
