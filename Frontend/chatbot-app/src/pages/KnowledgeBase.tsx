// import NavBar from "./NavBar.tsx";
import {useEffect, useState} from "react";
// import DocumentPreview from './DocumentPreview';
// import DocumentViewer from './DocumentViewer';
// import UploadDocumentForm from './UploadDocumentForm';
// import { listFilesWithUrls } from '../services/azureStorageService';
import axios from 'axios';
import DocumentViewer from "../components/DocumentViewer.tsx";

const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL, // Updated to use Vite syntax
    timeout: 5000,
    headers: {'Content-Type': 'application/json'}
});



export default function KnowledgeBase() {
    const [documents, setDocuments] = useState([]);
    const [selectedDocument, setSelectedDocument] = useState(null);



    useEffect(() =>{
        fetchDocuments()

    }, [])

    const fetchDocuments = async () => {
        try {
            const response = await axiosInstance.get('/api/storage/files'); // Fix URL here
            setDocuments(response.data);
            setSelectedDocument(response.data[0]);

            console.log(response.data);

        } catch (error) {
            console.error('Error fetching files:', error);
        }
    };


    return (
        <>
            <div className="min-h-full ">
                <main>
                    <div className="flex justify-center">
                        <div className="flex w-full">
                            <div className="knowledge-base-card ">
                                {/*<div className="chatbot-header">*/}
                                {/*    <h2>KNOWLEDGE BASE</h2>*/}
                                {/*</div>*/}
                                <div className={"document-list  border-r dark:bg-gray-800 dark:border-gray-700 "}>

                                    <div
                                        className={"document-list-header pb-10 mb-5 space-y-2 border-b border-gray-200 dark:border-gray-700"}>
                                        <span className="self-center pb-5 text-2xl font-semibold whitespace-nowrap">
                                            DOCUMENTS
                                        </span>
                                    </div>
                                    <div className={""}>
                                        {documents.map((document) => (
                                            <div
                                                className={"flex items-center cursor-pointer p-2 text-base font-medium text-gray-900 rounded-lg dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 group"}
                                                onClick={()=>{setSelectedDocument(document)}}>

                                                {document.name}
                                            </div>
                                        ))}
                                    </div>

                                </div>
                                <div className={"selected-document "}>
                                    <DocumentViewer document={selectedDocument}/>
                                </div>


                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </>
    );
}