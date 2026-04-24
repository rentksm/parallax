import duckdb
import json

def export_to_json(db_path='news.duckdb', json_path='data.json'):
    conn = duckdb.connect(db_path, read_only=True)
    
    # Export stories
    stories_df = conn.execute('''
        SELECT 
            s.id, 
            s.title, 
            s.topic,
            s.structured_data,
            strftime(s.created_at, '%Y-%m-%dT%H:%M:%S.000Z') as created_at,
            COUNT(DISTINCT e.id) as event_count,
            COUNT(a.id) as article_count,
            COUNT(DISTINCT a.source) as source_count,
            string_agg(DISTINCT a.source, ' / ') as source_names
        FROM stories s
        LEFT JOIN events e ON s.id = e.story_id
        LEFT JOIN articles a ON e.id = a.event_id
        GROUP BY s.id, s.title, s.topic, s.structured_data, s.created_at
        ORDER BY s.created_at DESC
    ''').df()
    
    data = {
        'stories': stories_df.to_dict(orient='records'),
    }
    
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"Exported {len(stories_df)} stories to {json_path}")
    conn.close()

if __name__ == "__main__":
    export_to_json()
