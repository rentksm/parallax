import { query } from "@/lib/db";
import StoryList from "@/components/StoryList";

export const dynamic = "force-dynamic";

export default async function Home() {
  const stories = await query(`
    SELECT s.id
    GROUP BY s.id
  `); 

  return (
    <div className="min-h-screen bg-black text-neutral-200 font-sans">
      <header className="border-b border-neutral-800 py-6 px-8 sticky top-0 bg-black/80 backdrop-blur-md z-10">
        <h1 className="text-2xl font-light tracking-widest text-white">ARENDT</h1>
        <p className="text-neutral-500 text-sm mt-1">Structure of the News (Stories)</p>
      </header>

      <main className="max-w-4xl mx-auto px-8 py-12">
        <StoryList stories={stories} />
      </main>
    </div>
  );
}
