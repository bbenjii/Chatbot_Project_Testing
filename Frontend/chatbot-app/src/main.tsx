import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
// import App from './App.tsx'
import Chatbot from './Chatbot'
import ChatbotPage from "./ChatbotPage.tsx";
import App from "./App.tsx";

createRoot(document.getElementById('root')!).render(
  <StrictMode>
      <ChatbotPage/>
      {/*<App/>*/}
      {/*<Chatbot />*/}
  </StrictMode>,
)
