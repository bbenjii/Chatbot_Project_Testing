// @ts-ignore
import { useState, useEffect } from 'react'
// import './App.css'
import './Chatbot.css'
import MessageBox from './MessageBox';
function Chatbot() {
    const [messages, setMessages] = useState([
        {"sender":"human", "text":"Hello"},
        {"sender": "ai", "text": "Hey, how can I help you"},
        {"sender": "human", "text": "My name is Ben"},
        {"sender": "ai", "text": "Hi Ben, Nice to meet you"},
        {"sender": "human", "text": "Whats the one piece"},
        {"sender": "ai", "text": "The One Piece is a manga by Master Oda"},
        {"sender": "human", "text": "Great, thank you"},
        {"sender": "ai", "text": "No problem, gang"}
])

    const [inputText, setInputText] = useState('');



    return(
        <>
            <div className={"flex w-full "}>
                <div className="chatbot-card">
                    <div className="chatbot-header">
                        <h2>Chatbot</h2>
                    </div>

                    <div className="chatbot-messages">
                        {messages.map((msg, idx) => (
                            <div className={`message ${msg.sender}`}>
                                <MessageBox name={msg.sender} message={msg.text}/>
                            </div>
                            // <div key={idx} className={`message ${msg.sender}`}>
                            //     <div className="message-box">{msg.text}</div>
                            // </div>
                        ))}
                    </div>

                    <div className="chatbot-input">
                        <input
                            type="text"
                            placeholder="Enter your message..."
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                        />
                        <button >Send</button>
                    </div>
                </div>
            </div>
        </>
    )

}

export default Chatbot
