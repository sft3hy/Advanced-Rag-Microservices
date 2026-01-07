export interface SessionDocument {
    id?: string;
    original_filename: string;
    vision_model_used?: string;
    chart_dir?: string;
    chart_descriptions?: string | Record<string, string>;
    chart_descriptions_json?: string | Record<string, string>;
}

export interface SearchResult {
    text: string;
    source: string;
    page?: number;
    score?: number;
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    sources?: SearchResult[];
}

export interface QueryResponse {
    response: string;
    results: SearchResult[];
    error?: string;
}