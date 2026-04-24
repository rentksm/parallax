import fs from 'fs';
import path from 'path';

// Construct the absolute path to the backend data.json file
const dataPath = path.resolve(process.cwd(), '../backend/data.json');

export function getData() {
    const fileContents = fs.readFileSync(dataPath, 'utf8');
    return JSON.parse(fileContents);
}

// Emulate the query API for easy refactoring
export async function query<T = any>(sql: string, ...params: any[]): Promise<T[]> {
    const data = getData();
    
    if (sql.includes('GROUP BY s.id')) {
        return data.stories as T[];
    }
    
    if (sql.includes('FROM stories WHERE id = ?')) {
        const storyId = params[0];
        return data.stories.filter((s: any) => s.id === storyId) as T[];
    }
    
    if (sql.includes('FROM events WHERE id = ?')) {
        const eventId = params[0];
        return data.events?.filter((e: any) => e.id === eventId) as T[] || [];
    }
    
    if (sql.includes('FROM articles') && sql.includes('WHERE event_id = ?')) {
        const eventId = params[0];
        return data.articles?.filter((a: any) => a.event_id === eventId) as T[] || [];
    }
    
    return [];
}
