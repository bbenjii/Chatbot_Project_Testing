import { useState } from 'react'
import { Routes, Route } from 'react-router-dom';

import Sidebar from "./components/Sidebar.tsx";
import ChatbotPage from "./pages/ChatbotPage.tsx";
import Navigation from "./components/Navigation.tsx";
import KnowledgeBase from "./pages/KnowledgeBase.tsx";

function App() {
    const [hideSideBar, setHideSideBar] = useState(true);

    const showHideSidebar = () => {
        setHideSideBar(!hideSideBar);
        console.log(hideSideBar);
    };

  return (
      <>
          <div className="antialiased bg-gray-50 dark:bg-gray-900 ">
              <div>
                  <Navigation hideSideBar={showHideSidebar}/>
                  <Sidebar hidden={hideSideBar} />
              </div>

              <main className="p-4 md:ml-64 h-full pt-20">
                  <Routes>
                      <Route path={"/"} element={<ChatbotPage/>} />
                      <Route path={"/knowledge-base"} element={<KnowledgeBase />} />
                  </Routes>
              </main>
          </div>
      </>
  )
}

export default App
