import { useEffect, useState } from "react";
import axios from 'axios';
import DocumentViewer from "../components/DocumentViewer.tsx";
import DocumentPreview from "../components/DocumentPreview.tsx";

const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL, // Updated to use Vite syntax
    timeout: 5000,
    // headers: {'Content-Type': 'application/json'}
});

export default function KnowledgeBase() {
    const [documents, setDocuments] = useState([]);
    const [selectedDocument, setSelectedDocument] = useState(null);

    // New state variables for the upload form
    const [showUploadForm, setShowUploadForm] = useState(false);
    const [uploadFileName, setUploadFileName] = useState('');
    const [uploadFile, setUploadFile] = useState(null);

    useEffect(() => {
        fetchDocuments();
    }, []);

    const fetchDocuments = async () => {
        try {
            const response = await axiosInstance.get('/api/storage/files', {
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            setDocuments(response.data);
            setSelectedDocument(response.data[0]);
            console.log(response.data);
        } catch (error) {
            console.error('Error fetching files:', error);
        }
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!uploadFile || !uploadFileName) {
            alert('Please select a file and enter a file name.');
            return;
        }

        const formData = new FormData();
        formData.append('file', uploadFile);
        formData.append('name', uploadFileName);

        try {
            await axiosInstance.post('/api/storage/files', formData);
            // Refresh the documents list after upload
            fetchDocuments();
            // Reset form states
            setShowUploadForm(false);
            setUploadFileName('');
            setUploadFile(null);
        } catch (error) {
            console.error('Error uploading file:', error);
        }
    };

    return (
        <div className="min-h-full">
            <main>
                <div className="flex justify-center">
                    <div className="flex w-full">
                        <div className="knowledge-base-card">
                            <div className="document-list border-r dark:bg-gray-800 dark:border-gray-700">
                                <div className="document-list-header pb-10 mb-5 space-y-2 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                                    <span className="self-center pb-5 text-2xl font-semibold whitespace-nowrap">
                                        DOCUMENTS
                                    </span>
                                    <button
                                        onClick={() => setShowUploadForm(true)}
                                        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                                    >
                                        Add
                                    </button>
                                </div>

                                {/* Upload Form */}
                                {showUploadForm && (
                                    <form onSubmit={handleUpload} className="p-4 border-b border-gray-200 dark:border-gray-700">
                                        <div className="mb-4">
                                            <label className="block text-gray-700 dark:text-gray-200 text-sm font-bold mb-2">
                                                File
                                            </label>
                                            <input
                                                type="file"
                                                onChange={(e) => setUploadFile(e.target.files[0])}
                                                className="w-full px-3 py-2 border rounded"
                                            />
                                        </div>
                                        <div className="mb-4">
                                            <label className="block text-gray-700 dark:text-gray-200 text-sm font-bold mb-2">
                                                File Name
                                            </label>
                                            <input
                                                type="text"
                                                value={uploadFileName}
                                                onChange={(e) => setUploadFileName(e.target.value)}
                                                placeholder="Enter file name"
                                                className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500"
                                            />
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <button
                                                type="submit"
                                                className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
                                            >
                                                Upload
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setShowUploadForm(false)}
                                                className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </form>
                                )}

                                <div className="scrollable-documents">
                                    {documents.map((document) => (
                                        <div
                                            key={document.name}
                                            className="flex flex-col items-center cursor-pointer p-2 text-base font-medium text-gray-900 rounded-lg dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 group"
                                            onClick={() => {
                                                setSelectedDocument(document);
                                            }}
                                        >
                                            <DocumentPreview document={document} />
                                            <p>{document.name}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div className="selected-document">
                                <DocumentViewer document={selectedDocument} />
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}