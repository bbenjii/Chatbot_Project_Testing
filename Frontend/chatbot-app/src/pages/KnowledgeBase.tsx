// import NavBar from "./NavBar.tsx";
import MessageBox from "../components/MessageBox.tsx";
import {useEffect, useState} from "react";
import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL, // Updated to use Vite syntax
    timeout: 5000,
    headers: {'Content-Type': 'application/json'}
});

// Define a type for the message objects
interface Message {
    sender: string;
    text: string;
}

export default function KnowledgeBase() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState('');
    const [loading, setLoading] = useState(false);


    useEffect(() =>{
        setMessages([]);
        setInputText("");
        setLoading(false)
    }, [])
    const sendMessage = async (query: string = inputText) => {
        setLoading(true);
        setMessages((prevMessages) => [...prevMessages, { sender: "human", text: query }]);
        setInputText("");
        const data = {message: query};

        try {
            const response = await axiosInstance.post('/api/chatbot', data);
            console.log(response.data);
            const message = response.data.ai_message;
            setMessages((prevMessages) => [...prevMessages, { sender: "ai", text: message }]);
        } catch (error) {
            console.error('Error:', error);
            setMessages((prevMessages) => [...prevMessages, { sender: "system", text: "Sorry, something went wrong. Please try again later." }]);
        } finally {
            setLoading(false)
        }

    };

    return (
        <>
            <div className="min-h-full ">
                {/*<NavBar/>*/}
                {/*<header className="bg-white shadow">*/}
                {/*    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">*/}
                {/*        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Chatbot</h1>*/}
                {/*    </div>*/}
                {/*</header>*/}
                <main>
                    <div className="flex justify-center">
                        <div className="flex w-full">
                            <div className="chatbot-card">
                                <div className="chatbot-header">
                                    <h2>KNOWLEDGE BASE</h2>
                                </div>


                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </>
    );
}