
import './globals.css';
import { Toaster } from '@/components/ui/toaster';
import HeaderSidebar from '@/components/header-sidebar'
import { BackendUrlProvider } from './contexts/BackendUrlContext'
import Page from "./page"

function App() {

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

