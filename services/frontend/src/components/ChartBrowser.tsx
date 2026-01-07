import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, ImageIcon, Maximize2 } from 'lucide-react';
import { getSessionCharts } from '../lib/api';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import ReactMarkdown from 'react-markdown';


interface ChartBrowserProps {
    sessionId: string | null;
}

export const ChartBrowser: React.FC<ChartBrowserProps> = ({ sessionId }) => {
    const [index, setIndex] = useState(0);

    const { data: allCharts = [] } = useQuery({
        queryKey: ['charts', sessionId],
        queryFn: () => getSessionCharts(sessionId!),
        enabled: !!sessionId,
    });

    if (!sessionId) {
        return <div className="p-4 text-sm text-muted-foreground text-center">Load a session to view charts.</div>;
    }

    if (allCharts.length === 0) {
        return <div className="p-4 text-sm text-muted-foreground text-center">No charts detected in this session.</div>;
    }

    const total = allCharts.length;
    const safeIndex = index >= total ? 0 : index;
    const currentChart = allCharts[safeIndex];

    const handleNext = () => setIndex((prev) => (prev + 1) % total);
    const handlePrev = () => setIndex((prev) => (prev - 1 + total) % total);

    return (
        <div className="flex flex-col h-full">
            {/* Navigation Controls */}
            <div className="flex items-center justify-between p-2 mb-2 bg-muted/40 rounded-lg">
                <Button variant="ghost" size="icon" onClick={handlePrev} className="h-8 w-8">
                    <ChevronLeft className="h-4 w-4" />
                </Button>
                <div className="text-xs font-medium text-center">
                    Chart {safeIndex + 1} / {total}
                </div>
                <Button variant="ghost" size="icon" onClick={handleNext} className="h-8 w-8">
                    <ChevronRight className="h-4 w-4" />
                </Button>
            </div>

            {/* Image Area - UPDATED BG */}
            <Card className="overflow-hidden bg-muted/20 flex items-center justify-center min-h-[200px] max-h-[300px] mb-4 relative group border">
                {currentChart.url ? (
                    <a href={currentChart.url} target="_blank" rel="noopener noreferrer">
                        <img
                            src={currentChart.url}
                            alt="Chart"
                            // Removed bg-white, added p-1
                            className="w-full h-full object-contain"
                        />
                        {/* ... hover icon ... */}
                    </a>
                ) : (
                    <ImageIcon className="h-10 w-10 text-muted-foreground/30" />
                )}
            </Card>

            {/* Metadata */}
            <ScrollArea className="flex-1">
                <div className="space-y-3 px-1">
                    <div>
                        <span className="text-xs font-semibold text-primary">Source Document:</span>
                        <p className="text-xs text-muted-foreground">{currentChart.doc_name} (Page {currentChart.page})</p>
                    </div>

                    <div>
                        <span className="text-xs font-semibold text-primary">AI Description:</span>
                        {/* UPDATED BG */}
                        <div className="mt-1 text-xs text-muted-foreground leading-relaxed bg-muted/40 p-2 rounded border">
                            {currentChart.description || "No description available."}
                        </div>
                    </div>
                </div>
            </ScrollArea>
        </div>
    );
};