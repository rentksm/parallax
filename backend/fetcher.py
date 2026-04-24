import feedparser
import datetime
import uuid
import pytz

FEEDS = [
    # 既存
    {"source": "NYT", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"},
    {"source": "BBC", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"source": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"source": "NHK", "url": "https://www.nhk.or.jp/rss/news/cat0.xml"},
    {"source": "Yahoo World", "url": "https://news.yahoo.co.jp/rss/topics/world.xml"},
    {"source": "Hacker News", "url": "https://hnrss.org/frontpage"},

    # 追加（経済）
    {"source": "Reuters World", "url": "https://feeds.reuters.com/Reuters/worldNews"},
    {"source": "Bloomberg", "url": "https://feeds.bloomberg.com/markets/news.rss"},

    # 追加（別視点）
    {"source": "WSJ World", "url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml"},

    # 追加（アジア）
    {"source": "SCMP", "url": "https://www.scmp.com/rss/91/feed"},
    {"source": "Straits Times", "url": "https://www.straitstimes.com/news/world/rss.xml"},

    # 追加（思想）
    {"source": "Aeon", "url": "https://aeon.co/feed.rss"},
    {"source": "The Conversation", "url": "https://theconversation.com/global/rss"},

    # 地政学追加
    {"source": "DW", "url": "https://rss.dw.com/xml/rss-en-all"},
    {"source": "RT", "url": "https://www.rt.com/rss/news/"},
    {"source": "China Daily", "url": "http://www.chinadaily.com.cn/rss/world_rss.xml"},
    {"source": "The Hindu", "url": "https://www.thehindu.com/news/international/feeder/default.rss"},
    {"source": "AllAfrica", "url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf"},
    {"source": "Haaretz", "url": "https://www.haaretz.com/cmlink/1.628752"}
]

def fetch_articles():
    articles = []
    print("Fetching articles from RSS feeds...")
    for feed in FEEDS:
        print(f"  - {feed['source']}")
        try:
            parsed = feedparser.parse(feed["url"])
            for entry in parsed.entries:
                pub_date = entry.get('published_parsed')
                if pub_date:
                    dt = datetime.datetime(*pub_date[:6], tzinfo=pytz.utc)
                else:
                    dt = datetime.datetime.now(pytz.utc)
                
                # Basic string cleaning
                title = entry.title.strip()
                
                articles.append({
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "source": feed["source"],
                    "url": entry.link,
                    "published_at": dt
                })
        except Exception as e:
            print(f"Error fetching from {feed['source']}: {e}")
            
    print(f"Fetched {len(articles)} articles total.")
    return articles
