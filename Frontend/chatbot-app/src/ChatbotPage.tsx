import NavBar from "./NavBar.tsx";
import MessageBox from "./MessageBox.tsx";
import { useState } from "react";
import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL, // Updated to use Vite syntax
    timeout: 5000,
    headers: { 'Content-Type': 'application/json' }
});

export default function ChatbotPage() {
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');

    const sendMessage = async (query: string = inputText) => {
        setMessages((prevMessages) => [...prevMessages, { sender: "human", text: query }]);
        setInputText("");
        const data = { message: query };

        try {
            const response = await axiosInstance.post('/api/chatbot', data);
            console.log(response.data);

            const message = response.data.ai_message;
            setMessages((prevMessages) => [...prevMessages, { sender: "ai", text: message }]);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    return (
        <>
            <div className="min-h-full bg-gray-800">
                <NavBar />
                <header className="bg-white shadow">
                    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Chatbot</h1>
                    </div>
                </header>
                <main>
                    <div className="flex justify-center">
                        <div className="flex w-full">
                            <div className="chatbot-card">
                                <div className="chatbot-header">
                                    <h2>Chatbot</h2>
                                </div>

                                <div className="chatbot-messages">
                                    {messages.map((msg, idx) => (
                                        <div key={idx} className={`message ${msg.sender}`}>
                                            <MessageBox name={msg.sender} message={msg.text} />
                                        </div>
                                    ))}
                                </div>

                                <form
                                    onSubmit={(e) => {
                                        e.preventDefault();
                                        sendMessage();
                                    }}
                                >
                                    <div className="chatbot-input">
                                        <input
                                            type="text"
                                            placeholder="Enter your message..."
                                            value={inputText}
                                            onChange={(e) => setInputText(e.target.value)}
                                        />
                                        <button type="submit">Send</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </>
    );
}