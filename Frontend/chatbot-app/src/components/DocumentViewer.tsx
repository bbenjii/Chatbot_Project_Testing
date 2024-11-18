import React from 'react';

const DocumentViewer = ({ document }) => {
    if (!document) return <div>Select a document to view</div>;

    return (
        <div className="document-viewer">
            <iframe src={document.url} title={document.name} width="100%" height="1000px"></iframe>
        </div>
    );
};

export default DocumentViewer;