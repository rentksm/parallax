import json
from collections import Counter
from datetime import timedelta
import re

SOURCE_REGIONS = {
    "NYT": "US", "WSJ World": "US", "Bloomberg": "US", "Hacker News": "US",
    "BBC": "Europe", "DW": "Europe", "Reuters World": "Europe",
    "NHK": "Asia", "Yahoo World": "Asia", "SCMP": "Asia", "Straits Times": "Asia", "China Daily": "Asia", "The Hindu": "Asia",
    "Al Jazeera": "Middle East", "Haaretz": "Middle East",
    "RT": "Russia",
    "AllAfrica": "Africa",
    "Aeon": "Global", "The Conversation": "Global"
}

def extract_keywords(title):
    words = re.findall(r'\b[A-Za-z]{4,}\b', title.lower())
    stop_words = {'that', 'with', 'this', 'from', 'have', 'they', 'will', 'says', 'said', 'over', 'after', 'about'}
    return [w for w in words if w not in stop_words]

def analyze_story_rule_based(story, events_data):
    """
    story: dict with id, title, topic
    events_data: list of dicts. each dict represents an event and its articles.
                 {'event': {...}, 'articles': [...]}
    """
    all_articles = []
    events_output = []
    
    for ed in events_data:
        event = ed['event']
        articles = ed['articles']
        if not articles:
            continue
            
        articles = sorted(articles, key=lambda x: x['published_at'])
        start_time = articles[0]['published_at']
        all_articles.extend(articles)

        # 1. Time Slices & Phases for this Event
        slices = {}
        for a in articles:
            hour_diff = (a['published_at'] - start_time).total_seconds() / 3600
            bin_idx = int(hour_diff // 4)
            if bin_idx not in slices:
                slices[bin_idx] = []
            slices[bin_idx].append(a)

        time_slices = []
        sorted_bins = sorted(slices.keys())
        for i, bin_idx in enumerate(sorted_bins):
            slice_articles = slices[bin_idx]
            if i == 0:
                phase = "BREAKING"
            elif i == 1:
                phase = "EXPANSION" if len(slice_articles) >= 2 else "RESPONSE"
            elif i == len(sorted_bins) - 1 and len(sorted_bins) > 2:
                phase = "ANALYSIS"
            else:
                phase = "RESPONSE"

            formatted_articles = []
            slice_keywords = []
            for a in slice_articles:
                kw = extract_keywords(a['title'])
                slice_keywords.extend(kw)
                event_kw = set(extract_keywords(event['title']))
                stance = [w for w in kw if w not in event_kw][:3]
                formatted_articles.append({
                    "source": a['source'],
                    "title": a['title'],
                    "url": a['url'],
                    "stance_keywords": stance
                })
                
            time_slices.append({
                "timestamp": (start_time + timedelta(hours=bin_idx*4)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "phase": phase,
                "articles": formatted_articles,
                "summary_keywords": [k for k, v in Counter(slice_keywords).most_common(5)]
            })

        # Event Evolution
        evolution = {
            "keyword_transitions": [],
            "stance_shift": "N/A"
        }
        if len(time_slices) > 1:
            first_kw = time_slices[0]['summary_keywords'][:2]
            last_kw = time_slices[-1]['summary_keywords'][:2]
            if set(first_kw) != set(last_kw):
                evolution["keyword_transitions"].append(f"{'/'.join(first_kw)} -> {'/'.join(last_kw)}")

        events_output.append({
            "event_id": event['id'],
            "event_title": event['title'],
            "time_slices": time_slices,
            "evolution": evolution
        })

    if not all_articles:
        return "{}"

    # Story-level Structure
    sources = [a['source'] for a in all_articles]
    source_counts = dict(Counter(sources))
    
    regions = [SOURCE_REGIONS.get(s, "Unknown") for s in sources]
    region_counts = dict(Counter(regions))
    
    if len(set(regions)) >= 3:
        spread_type = "GLOBAL"
    elif len(set(regions)) == 2:
        spread_type = "REGIONAL"
    else:
        spread_type = "LOCAL"

    # Story-level Bias
    coverage = Counter(sources)
    top_source, top_count = coverage.most_common(1)[0]
    total = len(all_articles)
    if top_count / total > 0.6 and total >= 3:
        bias = f"Heavily driven by {top_source}"
    elif spread_type == "GLOBAL":
        bias = "Globally balanced coverage"
    else:
        bias = "Regional focus"

    result = {
        "story_id": story['id'],
        "story_title": story['title'],
        "events": events_output,
        "structure": {
            "source_distribution": source_counts,
            "country_distribution": region_counts,
            "spread_type": spread_type
        },
        "interest": {
            "coverage_bias": bias,
            "dominant_sources": [s for s, c in coverage.most_common(3)]
        },
        "timeline_summary": [], # Placeholder for LLM
        "contradictions": [] # Placeholder for LLM
    }

    return json.dumps(result)

def analyze_all_events(db_path='news.duckdb'):
    import duckdb
    conn = duckdb.connect(db_path)
    
    # We now analyze at the STORY level
    stories_df = conn.execute('SELECT id, title, topic, created_at FROM stories WHERE structured_data IS NULL').df()
    stories = stories_df.to_dict(orient='records')
    
    updates = []
    for story in stories:
        events_df = conn.execute('SELECT id, title, topic, created_at FROM events WHERE story_id = ? ORDER BY created_at ASC', [story['id']]).df()
        events = events_df.to_dict(orient='records')
        
        events_data = []
        for event in events:
            articles_df = conn.execute('SELECT source, title, url, published_at FROM articles WHERE event_id = ? ORDER BY published_at ASC', [event['id']]).df()
            events_data.append({
                'event': event,
                'articles': articles_df.to_dict(orient='records')
            })
        
        # Only structure if there are articles
        total_articles = sum(len(ed['articles']) for ed in events_data)
        if total_articles > 0:
            structured_json = analyze_story_rule_based(story, events_data)
            updates.append((structured_json, story['id']))
            
    if updates:
        print(f"Structuring {len(updates)} stories...")
        conn.executemany('UPDATE stories SET structured_data = ? WHERE id = ?', updates)
        
    conn.close()
