import React, { useState } from 'react';
import './MessageBox.css';
import ReactMarkdown from 'react-markdown';

interface MessageBoxProps {
    name: string;
    message: string;
}
const MessageBox = ({ name, message }: MessageBoxProps) => {
    const [dropdownOpen, setDropdownOpen] = useState(false);

    const toggleDropdown = () => setDropdownOpen(!dropdownOpen);

    return (
        <div className={`message-box-container ${name}`}>
            {/*<img className="avatar" src={avatarSrc} alt={`${name} avatar`} />*/}

            <div className={`message-content ${name}`}>
                <div className="message-header">
                    <span className="name">{name}</span>
                    {/*<span className="time">{time}</span>*/}
                </div>

                <p className="message-text">
                    <ReactMarkdown>{message}</ReactMarkdown>
                </p>

                {/*<span className="status">{status}</span>*/}
            </div>

            <button
                className="dropdown-button"
                onClick={toggleDropdown}
                aria-label="More options"
            >
                <svg
                    className="dots-icon"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="currentColor"
                    viewBox="0 0 4 15"
                >
                    <path d="M3.5 1.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Zm0 6.041a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Zm0 5.959a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" />
                </svg>
            </button>

            {/*{dropdownOpen && (*/}
            {/*    <div className="dropdown-menu">*/}
            {/*        <ul>*/}
            {/*            <li><button>Reply</button></li>*/}
            {/*            <li><button>Forward</button></li>*/}
            {/*            <li><button>Copy</button></li>*/}
            {/*            <li><button>Report</button></li>*/}
            {/*            <li><button>Delete</button></li>*/}
            {/*        </ul>*/}
            {/*    </div>*/}
            {/*)}*/}
        </div>
    );
};

export default MessageBox;