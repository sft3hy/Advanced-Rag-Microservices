import React from 'react';
import ReactMarkdown from 'react-markdown';
import { SearchResult, SessionDocument } from '../types';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Card } from '@/components/ui/card';

interface SourceViewerProps {
    sources: SearchResult[];
    documents: SessionDocument[];
}

export const SourceViewer: React.FC<SourceViewerProps> = ({ sources }) => {
    if (!sources || sources.length === 0) return null;

    return (
        <Accordion type="single" collapsible className="w-full mt-2">
            <AccordionItem value="sources" className="border-b-0">
                <AccordionTrigger className="text-sm text-muted-foreground py-2 hover:no-underline hover:text-primary">
                    📚 View Sources & Related Charts
                </AccordionTrigger>
                <AccordionContent>
                    <div className="space-y-4 pt-2">
                        <h5 className="font-semibold text-sm">📄 Text Sources</h5>
                        <div className="grid gap-2">
                            {sources.map((src, idx) => {
                                const score = src.score ? parseFloat(src.score.toString()) : 1;
                                const relevance = (1 / (1 + score)) * 100;
                                const filename = src.source ? src.source.split('/').pop() : 'Unknown';

                                return (
                                    <Card key={idx} className="p-3 text-sm bg-muted/50 border-none shadow-sm">
                                        <div className="font-medium mb-2 text-xs text-blue-500 flex justify-between">
                                            <span>Source {idx + 1} (from {filename} - Page {src.page || 'N/A'})</span>
                                            <span>Relevance: {relevance.toFixed(1)}%</span>
                                        </div>
                                        <div className="text-muted-foreground text-xs leading-relaxed">
                                            {/* Safe Markdown usage */}
                                            <ReactMarkdown
                                                components={{
                                                    p: ({ node, ...props }) => <p className="mb-1 last:mb-0" {...props} />,
                                                    strong: ({ node, ...props }) => <span className="font-semibold text-foreground" {...props} />,
                                                }}
                                            >
                                                {src.text}
                                            </ReactMarkdown>
                                        </div>
                                    </Card>
                                );
                            })}
                        </div>
                    </div>
                </AccordionContent>
            </AccordionItem>
        </Accordion>
    );
};