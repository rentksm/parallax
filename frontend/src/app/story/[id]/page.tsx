import { query } from "@/lib/db";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { ArrowLeft, ExternalLink, Globe, TrendingUp, AlertTriangle } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function StoryPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  const storyId = resolvedParams.id;

  const stories = await query(`SELECT * FROM stories WHERE id = ?`, storyId);
  const story = stories[0];

  if (!story) {
    return <div className="p-8 text-white">Story not found.</div>;
  }

  // Parse structured data if available
  let structured = null;
  if (story.structured_data) {
    try {
      structured = JSON.parse(story.structured_data);
    } catch (e) {
      console.error("Failed to parse structured data", e);
    }
  }

  return (
    <div className="min-h-screen bg-black text-neutral-200 font-sans">
      <header className="border-b border-neutral-800 py-6 px-8 sticky top-0 bg-black/80 backdrop-blur-md z-10 flex items-center gap-6">
        <Link href="/" className="text-neutral-500 hover:text-white transition-colors">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-light text-white">{structured ? structured.story_title : story.title}</h1>
            <span className="text-xs font-medium px-2 py-0.5 bg-neutral-800 text-neutral-300 rounded-sm uppercase tracking-wider">
              {story.topic}
            </span>
          </div>
          <p className="text-neutral-500 text-sm mt-1">
            Started {formatDistanceToNow(new Date(story.created_at), { addSuffix: true })}
          </p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-8 py-12">
        
        {/* Top Metadata Panel */}
        {structured && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="bg-neutral-900/50 border border-neutral-800 p-5 rounded-lg flex items-start gap-4">
              <Globe className="text-blue-400 mt-1" size={24} />
              <div>
                <h4 className="text-xs text-neutral-500 uppercase tracking-wider font-bold mb-1">Spread</h4>
                <p className="text-lg text-white font-medium">{structured.structure.spread_type}</p>
                <p className="text-sm text-neutral-400 mt-1">Sources: {structured.structure.source_distribution ? Object.keys(structured.structure.source_distribution).length : 0}</p>
              </div>
            </div>
            <div className="bg-neutral-900/50 border border-neutral-800 p-5 rounded-lg flex items-start gap-4">
              <AlertTriangle className="text-orange-400 mt-1" size={24} />
              <div>
                <h4 className="text-xs text-neutral-500 uppercase tracking-wider font-bold mb-1">Coverage Bias</h4>
                <p className="text-sm text-white">{structured.interest.coverage_bias}</p>
                <p className="text-xs text-neutral-500 mt-2">
                  Dominant: {structured.interest.dominant_sources?.join(", ")}
                </p>
              </div>
            </div>
            <div className="bg-neutral-900/50 border border-neutral-800 p-5 rounded-lg flex items-start gap-4">
              <TrendingUp className="text-red-400 mt-1" size={24} />
              <div>
                <h4 className="text-xs text-neutral-500 uppercase tracking-wider font-bold mb-1">Contradictions</h4>
                {structured.contradictions && structured.contradictions.length > 0 ? (
                  <ul className="text-sm text-white space-y-1">
                    {structured.contradictions.map((c: string, i: number) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-neutral-500">None detected yet (LLM pending)</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Timeline of Events */}
        {structured && structured.events ? (
          <div className="space-y-16">
            {structured.events.map((ev: any, evIdx: number) => (
              <div key={evIdx}>
                <h2 className="text-2xl font-medium text-white mb-8 pb-4 border-b border-neutral-800">
                  Event: {ev.event_title}
                </h2>
                
                <div className="relative border-l border-neutral-800 ml-4 md:ml-0 md:pl-8 space-y-12">
                  {ev.time_slices.map((slice: any, idx: number) => (
                    <div key={idx} className="relative">
                      {/* Timeline Dot & Phase */}
                      <div className="absolute -left-10 md:-left-12 top-0 bg-black border border-neutral-700 w-6 h-6 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-neutral-400 rounded-full"></div>
                      </div>
                      
                      <div className="mb-4 flex flex-col md:flex-row md:items-center gap-3">
                        <span className={`px-2.5 py-1 rounded-sm text-xs font-bold uppercase tracking-widest border
                          ${slice.phase === 'BREAKING' ? 'bg-red-950 text-red-400 border-red-900/50' : 
                            slice.phase === 'RESPONSE' ? 'bg-blue-950 text-blue-400 border-blue-900/50' : 
                            slice.phase === 'EXPANSION' ? 'bg-purple-950 text-purple-400 border-purple-900/50' : 
                            'bg-neutral-800 text-neutral-300 border-neutral-700'}`}>
                          {slice.phase}
                        </span>
                        <span className="text-neutral-500 text-sm" suppressHydrationWarning>
                          {new Date(slice.timestamp).toLocaleString(undefined, { 
                            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
                          })} ({formatDistanceToNow(new Date(slice.timestamp), { addSuffix: true })})
                        </span>
                        {slice.summary_keywords && slice.summary_keywords.length > 0 && (
                          <span className="text-neutral-600 text-xs hidden md:inline">
                            Keywords: {slice.summary_keywords.join(", ")}
                          </span>
                        )}
                      </div>

                      {/* Articles in this slice */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {slice.articles.map((article: any, aIdx: number) => {
                          return (
                            <div key={aIdx} className="bg-neutral-900/40 border border-neutral-800 p-5 rounded-lg">
                              <div className="text-xs font-bold tracking-wider text-neutral-400 uppercase mb-3">
                                {article.source}
                              </div>
                              <h3 className="text-base font-medium text-white leading-snug mb-4">
                                "{article.title}"
                              </h3>
                              
                              <div className="flex justify-between items-end mt-4">
                                <div className="flex gap-2 flex-wrap">
                                  {article.stance_keywords && article.stance_keywords.map((kw: string, i: number) => (
                                    <span key={i} className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 bg-neutral-800 text-neutral-400 rounded">
                                      {kw}
                                    </span>
                                  ))}
                                </div>
                                {article.url && (
                                  <a href={article.url} target="_blank" rel="noopener noreferrer" className="text-xs text-neutral-500 hover:text-white transition-colors">
                                    Original <ExternalLink size={12} className="inline ml-0.5" />
                                  </a>
                                )}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-neutral-500">Wait for structured data.</div>
        )}
      </main>
    </div>
  );
}
