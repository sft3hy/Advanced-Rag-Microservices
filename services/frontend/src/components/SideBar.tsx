import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2, Upload, LayoutGrid, FileText } from 'lucide-react';

import { getSessions, checkBackendHealth, uploadAndProcessDocument, createSession } from '../lib/api';
import { VisionModel } from '../types';
import { cn } from '@/lib/utils';
import { ChartBrowser } from './ChartBrowser';

// UI Components
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface SidebarProps {
    currentSessionId: string | null;
    onSessionChange: (id: string | null) => void;
    className?: string;
}

const VISION_MODELS: { value: VisionModel; label: string; desc: string }[] = [
    { value: "Moondream2", label: "Moondream2 (1.6B)", desc: "Fast - Recommended" },
    { value: "Qwen3-VL-2B", label: "Qwen3-VL (2B)", desc: "Balanced - High Accuracy" },
    { value: "InternVL3.5-1B", label: "InternVL 3.5 (1B)", desc: "Precise - Doc Optimized" },
];

export const Sidebar: React.FC<SidebarProps> = ({ currentSessionId, onSessionChange, className }) => {
    const queryClient = useQueryClient();
    const [selectedModel, setSelectedModel] = useState<VisionModel>("Moondream2");
    const [isProcessing, setIsProcessing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState("");

    const { data: isBackendOnline } = useQuery({
        queryKey: ['health'],
        queryFn: checkBackendHealth,
        refetchInterval: 10000,
    });

    const { data: sessions = [] } = useQuery({
        queryKey: ['sessions'],
        queryFn: getSessions,
        enabled: !!isBackendOnline,
    });

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (!event.target.files || event.target.files.length === 0) return;
        const files = Array.from(event.target.files);

        setIsProcessing(true);
        setStatusMessage("Creating session...");
        setProgress(5);

        try {
            const newSessionId = await createSession(files.map(f => f.name));
            onSessionChange(newSessionId);

            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const percent = ((i) / files.length) * 100;
                setProgress(Math.max(10, percent));
                setStatusMessage(`Processing ${file.name}...`);
                await uploadAndProcessDocument(newSessionId, file, selectedModel);
            }

            setProgress(100);
            setStatusMessage("Done!");
            queryClient.invalidateQueries({ queryKey: ['sessions'] });
            queryClient.invalidateQueries({ queryKey: ['documents', newSessionId] });
            queryClient.invalidateQueries({ queryKey: ['charts', newSessionId] });

            setTimeout(() => {
                setIsProcessing(false);
                setStatusMessage("");
                setProgress(0);
                event.target.value = "";
            }, 1500);

        } catch (error) {
            console.error(error);
            setStatusMessage("Error during processing.");
            setIsProcessing(false);
        }
    };

    return (
        // FIX IS HERE: No fixed width (w-[320px]), use w-full h-full
        <div className={cn("flex flex-col h-full w-full bg-muted/10 border-r", className)}>
            <div className="p-4 border-b bg-background flex justify-between items-center shrink-0">
                <h2 className="text-lg font-bold flex items-center gap-2">
                    🧠 Smart RAG
                    <div className={`h-2 w-2 rounded-full ${isBackendOnline ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`} />
                </h2>
            </div>

            <Tabs defaultValue="files" className="flex-1 flex flex-col min-h-0">
                <div className="px-4 py-2 shrink-0">
                    <TabsList className="grid w-full grid-cols-2">
                        <TabsTrigger value="files" className="flex gap-2"><FileText className="w-4 h-4" /> Files</TabsTrigger>
                        <TabsTrigger value="charts" className="flex gap-2"><LayoutGrid className="w-4 h-4" /> Charts</TabsTrigger>
                    </TabsList>
                </div>

                {/* --- FILES TAB --- */}
                <TabsContent value="files" className="flex-1 flex flex-col min-h-0 data-[state=active]:flex">
                    <ScrollArea className="flex-1 px-4 py-2">
                        <div className="space-y-6 pb-6">
                            <div className="space-y-2">
                                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Session</h3>
                                <Select
                                    value={currentSessionId || "new"}
                                    onValueChange={(val) => onSessionChange(val === "new" ? null : val)}
                                >
                                    <SelectTrigger className="w-full bg-background text-foreground border-border">
                                        <SelectValue placeholder="Select Session" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-popover text-popover-foreground border-border">
                                        <SelectItem
                                            value="new"
                                            className="text-primary font-medium focus:bg-accent focus:text-accent-foreground"
                                        >
                                            ✨ Start New Session
                                        </SelectItem>
                                        {sessions.map((sess) => (
                                            <SelectItem
                                                key={sess.id}
                                                value={String(sess.id)}
                                                className="focus:bg-accent focus:text-accent-foreground"
                                            >
                                                {sess.name.substring(0, 20)}{sess.name.length > 20 && "..."} ({sess.docs})
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <Separator />

                            {!currentSessionId && (
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium">Vision Model</label>
                                        <Select value={selectedModel} onValueChange={(v) => setSelectedModel(v as VisionModel)}>
                                            <SelectTrigger><SelectValue /></SelectTrigger>
                                            <SelectContent>
                                                {VISION_MODELS.map((m) => (
                                                    <SelectItem key={m.value} value={m.value}>
                                                        <div className="flex flex-col items-start">
                                                            <span className="bg-popover text-popover-foreground border-border">{m.label}</span>
                                                            <span className="text-xs text-muted-foreground">{m.desc}</span>
                                                        </div>
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <Card className="p-4 border-dashed border-2 flex flex-col items-center gap-2 text-center hover:bg-muted/50 transition-colors relative">
                                        <input
                                            type="file"
                                            multiple
                                            accept=".pdf,.docx,.pptx"
                                            className="absolute inset-0 opacity-0 cursor-pointer"
                                            onChange={handleFileUpload}
                                            disabled={isProcessing}
                                        />
                                        <Upload className="h-8 w-8 text-muted-foreground" />
                                        <div className="text-sm font-medium">Click to Upload</div>
                                    </Card>

                                    {isProcessing && (
                                        <div className="space-y-2">
                                            <div className="flex justify-between text-xs">
                                                <span>{statusMessage}</span>
                                                <span>{Math.round(progress)}%</span>
                                            </div>
                                            <Progress value={progress} className="h-2" />
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </ScrollArea>
                </TabsContent>

                {/* --- CHARTS TAB --- */}
                <TabsContent value="charts" className="flex-1 flex flex-col min-h-0 data-[state=active]:flex overflow-hidden">
                    <div className="flex-1 px-4 py-2 min-h-0">
                        <ChartBrowser sessionId={currentSessionId} />
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
};