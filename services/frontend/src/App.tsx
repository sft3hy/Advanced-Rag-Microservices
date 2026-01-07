import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MainContent } from './MainContent';
import { Sidebar } from './components/Sidebar';
import { useState } from 'react';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup
} from "@/components/ui/resizable";

const queryClient = new QueryClient();

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  return (
    <QueryClientProvider client={queryClient}>
      <div className="h-screen w-full overflow-hidden bg-background">
        <ResizablePanelGroup direction="horizontal">

          <ResizablePanel
            defaultSize={25}   // 25% width
            minSize={15}       // 15% width
            maxSize={45}       // 45% width
            className="bg-muted/10 min-w-[280px]"
          >
            <Sidebar
              currentSessionId={sessionId}
              onSessionChange={setSessionId}
            />
          </ResizablePanel>

          <ResizableHandle withHandle />

          <ResizablePanel defaultSize={75}>
            <MainContent sessionId={sessionId} />
          </ResizablePanel>

        </ResizablePanelGroup>
      </div>
    </QueryClientProvider>
  );
}

export default App;