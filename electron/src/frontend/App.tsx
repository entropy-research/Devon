
import './globals.css';
import { useEffect } from 'react';
import { Toaster } from '@/components/ui/toaster';
import HeaderSidebar from '@/components/header-sidebar'
import { BackendUrlProvider } from './contexts/BackendUrlContext'
import Page from "./page"


function App() {

  useEffect(() => {
    const handleServerError = (error: unknown) => {
      console.error('Server Error:', error);
      // alert('Server Error: ' + error); // Display as a popup
    };

    // Set up the IPC receive listener
    window.api.receive('server-error', handleServerError);

    // Clean up the listener on unmount
    return () => {
      window.api.removeAllListeners('server-error');
    };
  }, []);

  return (
    <div lang="en" className="dark h-full">
      <div className={` flex h-full flex-col`}>
        <div className="flex w-full h-full overflow-hidden">
          <div className="relative w-full overflow-hidden bg-day transition-colors duration-200 dark:bg-night flex">
            <BackendUrlProvider>
              <HeaderSidebar />
              <main className="mt-[54px] flex flex-row w-full">
                <Page />
                {/* {children} */}
              </main>
            </BackendUrlProvider>
          </div>
        </div>
        <Toaster />
      </div>
    </div>
  )
}

export default App

