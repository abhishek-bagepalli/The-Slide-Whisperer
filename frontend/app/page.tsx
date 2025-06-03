'use client';

import { useState } from 'react';
import { useDropzone } from 'react-dropzone';

interface LogEntry {
  message: string;
  timestamp: string;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [presentationFilename, setPresentationFilename] = useState<string | null>(null);

  const addLog = (message: string) => {
    setLogs(prev => [...prev, {
      message,
      timestamp: new Date().toLocaleTimeString()
    }]);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setFile(acceptedFiles[0]);
        setPresentationFilename(null); // Reset presentation filename when new file is selected
      }
    }
  });

  const handleProcess = async () => {
    if (!file) return;
    
    setIsProcessing(true);
    setLogs([]);
    setPresentationFilename(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Add initial log
      addLog('Starting file upload...');

      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.status === 'success') {
        addLog('File processed successfully!');
        setPresentationFilename(data.presentation_filename);
        console.log('Presentation data:', data.data);
      } else {
        addLog(`Error: ${data.message}`);
      }
    } catch (error: any) {
      addLog(`Error: ${error.message || 'An unknown error occurred'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = async () => {
    if (!presentationFilename) return;
    
    try {
      addLog('Starting download...');
      const response = await fetch(`http://localhost:8000/download/${presentationFilename}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = presentationFilename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        addLog('Download completed successfully!');
      } else {
        const errorData = await response.json();
        addLog(`Error downloading: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error: any) {
      addLog(`Error downloading: ${error.message}`);
    }
  };

  return (
    <main className="min-h-screen p-12 bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="max-w-4xl mx-auto space-y-12">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            The Slide Whisperer
          </h1>
          <p className="text-lg text-gray-600">
            Transform your documents into beautiful presentations
          </p>
        </div>
        
        {/* File Upload Area */}
        <div 
          {...getRootProps()} 
          className={`border-2 border-dashed rounded-xl p-16 text-center cursor-pointer transition-all duration-200
            ${isDragActive 
              ? 'border-blue-500 bg-blue-50 scale-[1.02]' 
              : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'}`}
        >
          <input {...getInputProps()} />
          <div className="space-y-6">
            <div className="text-7xl mb-6 transform transition-transform duration-200 hover:scale-110">
              {file ? '📄' : '📁'}
            </div>
            {file ? (
              <div className="text-gray-700">
                <p className="font-medium text-lg mb-3">Selected file:</p>
                <p className="text-sm bg-gray-100 inline-block px-6 py-3 rounded-full">
                  {file.name}
                </p>
              </div>
            ) : (
              <div className="text-gray-600 space-y-3">
                <p className="font-medium text-xl">Drag and drop your file here</p>
                <p className="text-base">or click to select a file</p>
                <p className="text-sm text-gray-500">Supported formats: PDF, DOC, DOCX</p>
              </div>
            )}
          </div>
        </div>

        {/* Process Button */}
        <div className="text-center">
          <div className="flex justify-center space-x-6">
            <button
              onClick={handleProcess}
              disabled={!file || isProcessing}
              className={`px-10 py-4 rounded-lg font-medium text-white text-lg transition-all duration-200 transform
                ${!file || isProcessing 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl'}`}
            >
              {isProcessing ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </span>
              ) : (
                'Generate Presentation'
              )}
            </button>

            {/* Download Button */}
            <button
              onClick={handleDownload}
              disabled={!presentationFilename}
              className={`px-10 py-4 rounded-lg font-medium text-white text-lg transition-all duration-200 transform
                ${!presentationFilename
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-green-600 hover:bg-green-700 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl'}`}
            >
              Download Presentation
            </button>
          </div>
        </div>

        {/* Logs Card */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
          <div className="px-8 py-5 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Processing Logs</h2>
              <div className="flex items-center space-x-3">
                <span className={`h-2.5 w-2.5 rounded-full ${isProcessing ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></span>
                <span className="text-sm text-gray-600">{isProcessing ? 'Processing' : 'Ready'}</span>
              </div>
            </div>
          </div>
          <div className="bg-gray-900 p-8 h-96 overflow-y-auto logs-container">
            {logs.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-500 text-sm">No logs to display</p>
              </div>
            ) : (
              <div className="font-mono text-sm text-gray-300 space-y-2">
                {logs.map((log, index) => (
                  <div key={index} className="py-2 border-b border-gray-800 last:border-0">
                    <span className="text-gray-500 mr-3">[{log.timestamp}]</span>
                    {log.message}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
} 