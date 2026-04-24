from init_db import init_db
from fetcher import fetch_articles
from cluster import cluster_and_save
from analyzer import analyze_all_events
from export import export_to_json

def main():
    print("--- Starting Parallax News Agent ---")
    # Initialize DB if not exists
    init_db()
    
    # Fetch RSS feeds
    articles = fetch_articles()
    
    # Cluster and save
    cluster_and_save(articles)
    
    # Analyze and structure
    analyze_all_events()
    
    # Export to JSON for frontend
    export_to_json()
    
    print("--- Finished ---")

if __name__ == "__main__":
    main()
