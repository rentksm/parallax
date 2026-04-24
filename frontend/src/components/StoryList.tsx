'use client';

import { useState } from 'react';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';

type Story = {
  id: string;
  title: string;
  topic: string;
  created_at: string;
  event_count: number;
  article_count: number;
  source_count: number;
  source_names: string;
};

export default function StoryList({ stories }: { stories: Story[] }) {
  const [filter, setFilter] = useState('All');
  const topics = ['All', 'Politics', 'Tech', 'Economy', 'War', 'Other'];

  const filteredStories = filter === 'All' 
    ? stories 
    : stories.filter(s => s.topic === filter);

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-8">
        {topics.map(topic => (
          <button
            key={topic}
            onClick={() => setFilter(topic)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              filter === topic 
                ? 'bg-white text-black' 
                : 'bg-neutral-900 text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200 border border-neutral-800'
            }`}
          >
            {topic}
          </button>
        ))}
      </div>

      {/* Stories List */}
      <div className="flex flex-col gap-5">
        {filteredStories.map((story) => {
          const isHot = story.event_count >= 2 || story.source_count >= 3; 
          
          return (
            <Link key={story.id} href={`/story/${story.id}`}>
              <div className="group block border border-neutral-800 p-6 rounded-xl hover:border-neutral-500 transition-colors bg-neutral-900/30 hover:bg-neutral-900/60 relative overflow-hidden">
                
                {/* Topic & Status Badges */}
                <div className="flex items-center gap-3 mb-3">
                  {isHot && (
                    <span className="text-xs font-bold px-2 py-0.5 bg-red-950 text-red-400 rounded-sm border border-red-900/50 flex items-center gap-1 tracking-wider uppercase">
                      🔥 Hot Story
                    </span>
                  )}
                  <span className="text-xs font-medium px-2 py-0.5 bg-neutral-800 text-neutral-300 rounded-sm uppercase tracking-wider">
                    {story.topic}
                  </span>
                </div>

                {/* Title */}
                <h3 className="text-xl font-medium text-white mb-4 group-hover:text-blue-400 transition-colors">
                  {story.title}
                </h3>

                {/* Meta Info */}
                <div className="flex flex-wrap justify-between items-center text-sm text-neutral-500 border-t border-neutral-800 pt-4 mt-2">
                  <div className="flex items-center gap-4">
                    <span className="text-white font-medium flex items-center gap-1.5">
                      ⏳ {story.event_count} Events
                    </span>
                    <span className="text-neutral-400 flex items-center gap-1.5">
                      📰 {story.article_count} Articles
                    </span>
                    <span className="text-neutral-500 hidden sm:flex items-center gap-1.5">
                      🏢 {story.source_names}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>Started {formatDistanceToNow(new Date(story.created_at), { addSuffix: true })}</span>
                  </div>
                </div>
              </div>
            </Link>
          );
        })}
        {filteredStories.length === 0 && (
          <p className="text-neutral-500 py-10 text-center border border-dashed border-neutral-800 rounded-lg">
            No stories found in this category.
          </p>
        )}
      </div>
    </div>
  );
}
