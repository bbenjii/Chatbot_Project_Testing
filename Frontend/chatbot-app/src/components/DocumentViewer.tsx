import React from 'react';


type DocumentViewerProps = {
    document: {
        url: string;
        name: string;
        content_type: string;
    };
};
const DocumentViewer: React.FC<DocumentViewerProps> = ({ document }) => {
    if (!document) return <div>Select a document to view</div>;

    return (
        <div className="document-viewer">
            {/* Render PDF files */}
            {document.content_type === "application/pdf" && (
                <div className="pdf-container">
                    <iframe src={document.url} title={document.name} width="100%" height="1000px"></iframe>
                </div>
            )}

            {/* Render Images */}
            {document.content_type.includes("image/") && (
                <img src={document.url} title={document.name} width="100%" height="1000px" alt={document.name}/>
            )}

            {/* Render Text Files */}
            {(document.content_type === "text/plain" || document.content_type === "text/csv") && (
                <iframe src={document.url} title={document.name} width="100%" height="1000px"></iframe>
            )}

            {/* Render Videos */}
            {document.content_type.includes("video/") && (
                <video controls width="100%" height="auto">
                    <source src={document.url} type={document.content_type}/>
                    Your browser does not support the video tag.
                </video>
            )}

            {/* Render Audio */}
            {document.content_type.includes("audio/") && (
                <audio controls>
                    <source src={document.url} type={document.content_type}/>
                    Your browser does not support the audio tag.
                </audio>
            )}

            {/* Fallback for Unsupported File Types */}
            {!["application/pdf", "text/plain", "text/csv"].includes(document.content_type) &&
                !document.content_type.includes("image/") &&
                !document.content_type.includes("video/") &&
                !document.content_type.includes("audio/") && (
                    <div>
                        <p>
                            Unable to preview this file type: <strong>{document.content_type}</strong>
                        </p>
                        <a href={document.url} download>
                            Click here to download the file.
                        </a>
                    </div>
                )}
        </div>
    );
};

export default DocumentViewer;