import React, { useEffect, useRef } from "react";
import { pdfjs } from "react-pdf";
import workerSrc from "pdfjs-dist/build/pdf.worker.min.js?url";

pdfjs.GlobalWorkerOptions.workerSrc = workerSrc;

type DocumentPreviewProps = {
    document: {
        url: string;
        name: string;
        content_type: string;
    };
};

const DocumentPreview: React.FC<DocumentPreviewProps> = ({ document }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const renderPdfPreview = async () => {
            if (document.content_type === "application/pdf" && canvasRef.current) {
                try {
                    // Load the PDF document
                    const pdf = await pdfjs.getDocument(document.url).promise;

                    // Get the first page of the PDF
                    const page = await pdf.getPage(1);

                    const viewport = page.getViewport({ scale: 1.5 }); // Increase scale for better quality
                    const canvas = canvasRef.current;
                    const context = canvas.getContext("2d");

                    if (context) {
                        canvas.style.width = `${viewport.width}px`;
                        canvas.style.height = `${viewport.height}px`;
                        canvas.width = viewport.width * window.devicePixelRatio; // Account for device pixel ratio
                        canvas.height = viewport.height * window.devicePixelRatio;

                        const renderContext = {
                            canvasContext: context,
                            viewport,
                            transform: [window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0], // Scale with device pixel ratio
                        };

                        await page.render(renderContext).promise;
                    }
                } catch (error) {
                    console.error("Error rendering PDF preview:", error);
                }
            }
        };

        renderPdfPreview();
    }, [document]);

    if (document.content_type.includes("image/")) {
        return <img src={document.url} alt={document.name} className="preview-image" />;
    }

    if (document.content_type === "application/pdf") {
        return <canvas ref={canvasRef} className="preview-pdf" />;
    }

    return <p>Unsupported file type</p>;
};

export default DocumentPreview;