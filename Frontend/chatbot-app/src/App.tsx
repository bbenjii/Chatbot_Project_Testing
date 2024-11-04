import { useState } from 'react'
import Sidebar from "./Sidebar.tsx";
// import './App.css'
import ChatbotPage from "./ChatbotPage.tsx";
import Navigation from "./Navigation.tsx";

function App() {
    const [hideSideBar, setHideSideBar] = useState(true);

    const showHideSidebar = () => {
        setHideSideBar(!hideSideBar);
        console.log(hideSideBar);
    };

  return (
      <>
          <div className="antialiased bg-gray-50 dark:bg-gray-900 ">
              <nav>
                  <Navigation hideSideBar={showHideSidebar}/>
                  <Sidebar hidden={hideSideBar} />

              </nav>
              <aside>
              </aside>
              <main className="p-4 md:ml-64 h-full pt-20">
                  <ChatbotPage  />
              </main>
          </div>
      </>
  )
}

export default App
