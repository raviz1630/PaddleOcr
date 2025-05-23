import React, { useState, useCallback, useRef } from 'react';
import { Upload, FileText, Image, Download, Eye, CheckCircle, Clock, AlertCircle, Play, Trash2, RefreshCw, X, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';

const DocumentTranslationApp = () => {
  const [files, setFiles] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [selectedView, setSelectedView] = useState('upload');
  const [previewFile, setPreviewFile] = useState(null);
  const [previewZoom, setPreviewZoom] = useState(1);
  const fileInputRef = useRef(null);

  // Enhanced file processing with more realistic timing and error handling
  const processFile = useCallback((fileId) => {
    setFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, status: 'processing', stage: 'uploading', progress: 0, startTime: Date.now() }
        : file
    ));

    // Simulate uploading stage
    setTimeout(() => {
      setFiles(prev => prev.map(file => 
        file.id === fileId 
          ? { ...file, stage: 'uploading', progress: 15 }
          : file
      ));
    }, 500);

    // Simulate OCR stage
    setTimeout(() => {
      setFiles(prev => prev.map(file => 
        file.id === fileId 
          ? { ...file, stage: 'ocr', progress: 35 }
          : file
      ));
    }, 2000);

    // Simulate Translation stage
    setTimeout(() => {
      setFiles(prev => prev.map(file => 
        file.id === fileId 
          ? { ...file, stage: 'translation', progress: 65 }
          : file
      ));
    }, 4500);

    // Simulate Visual Overlay stage
    setTimeout(() => {
      setFiles(prev => prev.map(file => 
        file.id === fileId 
          ? { ...file, stage: 'overlay', progress: 85 }
          : file
      ));
    }, 7000);

    // Complete with mock result
    setTimeout(() => {
      setFiles(prev => prev.map(file => 
        file.id === fileId 
          ? { 
              ...file, 
              status: 'completed', 
              stage: 'completed', 
              progress: 100,
              completedAt: new Date(),
              processingTime: Date.now() - file.startTime,
              resultUrl: `data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==`,
              originalPages: file.type.includes('pdf') ? Math.floor(Math.random() * 5) + 1 : 1,
              translatedPages: file.type.includes('pdf') ? Math.floor(Math.random() * 5) + 1 : 1
            }
          : file
      ));
    }, 9000);
  }, []);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  }, []);

  const validateFile = (file) => {
    const maxSize = 50 * 1024 * 1024; // 50MB
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff', 'image/gif'];
    
    if (file.size > maxSize) {
      return { valid: false, error: 'File size exceeds 50MB limit' };
    }
    
    if (!allowedTypes.includes(file.type)) {
      return { valid: false, error: 'Unsupported file format' };
    }
    
    return { valid: true };
  };

  const handleFiles = useCallback((fileList) => {
    const newFiles = Array.from(fileList).map(file => {
      const validation = validateFile(file);
      return {
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        type: file.type,
        file: file,
        status: validation.valid ? 'pending' : 'error',
        stage: validation.valid ? 'waiting' : 'error',
        progress: 0,
        uploadedAt: new Date(),
        error: validation.error || null
      };
    });
    
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const handleFileInput = (e) => {
    handleFiles(e.target.files);
  };

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const clearAllFiles = () => {
    setFiles([]);
  };

  const retryFile = (fileId) => {
    setFiles(prev => prev.map(file => 
      file.id === fileId 
        ? { ...file, status: 'pending', stage: 'waiting', progress: 0, error: null }
        : file
    ));
  };

  const getStageIcon = (stage) => {
    switch (stage) {
      case 'uploading': return <Upload className="w-4 h-4" />;
      case 'ocr': return <FileText className="w-4 h-4" />;
      case 'translation': return <RefreshCw className="w-4 h-4 animate-spin" />;
      case 'overlay': return <Image className="w-4 h-4" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'processing': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'error': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatProcessingTime = (ms) => {
    if (!ms) return '';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  const openPreview = (file) => {
    setPreviewFile(file);
    setPreviewZoom(1);
  };

  const closePreview = () => {
    setPreviewFile(null);
    setPreviewZoom(1);
  };

  // Statistics
  const stats = {
    total: files.length,
    pending: files.filter(f => f.status === 'pending').length,
    processing: files.filter(f => f.status === 'processing').length,
    completed: files.filter(f => f.status === 'completed').length,
    error: files.filter(f => f.status === 'error').length
  };

  const UploadArea = () => (
    <div className="w-full max-w-4xl mx-auto">
      <div
        className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
          dragActive 
            ? 'border-blue-500 bg-blue-50 scale-105' 
            : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50/50 bg-white'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className={`transition-all duration-300 ${dragActive ? 'scale-110' : ''}`}>
          <Upload className="w-16 h-16 mx-auto mb-4 text-blue-500" />
          <h3 className="text-2xl font-bold text-gray-800 mb-2">
            {dragActive ? 'Drop files here!' : 'Upload Arabic Documents'}
          </h3>
          <p className="text-gray-600 mb-8 max-w-md mx-auto">
            Drag and drop your documents or click to browse. Supports PDF, JPG, PNG, and other image formats up to 50MB.
          </p>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 font-medium shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            Browse Files
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.gif"
          onChange={handleFileInput}
          className="hidden"
        />
      </div>
    </div>
  );

  const FileList = () => (
    <div className="w-full max-w-6xl mx-auto space-y-4">
      {files.length > 0 && (
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Files ({files.length})</h3>
          <button
            onClick={clearAllFiles}
            className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-200 flex items-center space-x-2"
          >
            <Trash2 className="w-4 h-4" />
            <span>Clear All</span>
          </button>
        </div>
      )}
      
      {files.map(file => (
        <div key={file.id} className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow duration-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                file.status === 'error' ? 'bg-red-100' : 
                file.status === 'completed' ? 'bg-green-100' : 'bg-blue-100'
              }`}>
                {file.type.includes('pdf') ? 
                  <FileText className={`w-6 h-6 ${
                    file.status === 'error' ? 'text-red-600' : 
                    file.status === 'completed' ? 'text-green-600' : 'text-blue-600'
                  }`} /> : 
                  <Image className={`w-6 h-6 ${
                    file.status === 'error' ? 'text-red-600' : 
                    file.status === 'completed' ? 'text-green-600' : 'text-blue-600'
                  }`} />
                }
              </div>
              <div>
                <h4 className="font-medium text-gray-900">{file.name}</h4>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <span>{formatFileSize(file.size)}</span>
                  <span>•</span>
                  <span>Uploaded {file.uploadedAt.toLocaleTimeString()}</span>
                  {file.completedAt && (
                    <>
                      <span>•</span>
                      <span className="text-green-600">Completed in {formatProcessingTime(file.processingTime)}</span>
                    </>
                  )}
                </div>
                {file.error && (
                  <p className="text-sm text-red-600 mt-1">{file.error}</p>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(file.status)}`}>
                {file.status.charAt(0).toUpperCase() + file.status.slice(1)}
              </span>
              
              {file.status === 'pending' && (
                <button
                  onClick={() => processFile(file.id)}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200 flex items-center space-x-2"
                >
                  <Play className="w-4 h-4" />
                  <span>Start</span>
                </button>
              )}
              
              {file.status === 'error' && (
                <button
                  onClick={() => retryFile(file.id)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 flex items-center space-x-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Retry</span>
                </button>
              )}
              
              {file.status === 'completed' && (
                <div className="flex space-x-2">
                  <button 
                    onClick={() => openPreview(file)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 flex items-center space-x-2"
                  >
                    <Eye className="w-4 h-4" />
                    <span>Preview</span>
                  </button>
                  <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200 flex items-center space-x-2">
                    <Download className="w-4 h-4" />
                    <span>Download</span>
                  </button>
                </div>
              )}
              
              <button
                onClick={() => removeFile(file.id)}
                className="p-2 text-gray-400 hover:text-red-500 transition-colors duration-200"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          {file.status === 'processing' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStageIcon(file.stage)}
                  <span className="text-sm font-medium text-gray-700">
                    {file.stage === 'uploading' && 'Uploading to cloud storage...'}
                    {file.stage === 'ocr' && 'Extracting text with OCR...'}
                    {file.stage === 'translation' && 'Translating Arabic to English...'}
                    {file.stage === 'overlay' && 'Creating visual overlays...'}
                  </span>
                </div>
                <span className="text-sm text-gray-500">{file.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${file.progress}%` }}
                />
              </div>
            </div>
          )}
          
          {file.status === 'completed' && file.originalPages && (
            <div className="flex items-center space-x-6 text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
              <span>📄 {file.originalPages} page{file.originalPages !== 1 ? 's' : ''} processed</span>
              <span>🌍 {file.translatedPages} page{file.translatedPages !== 1 ? 's' : ''} translated</span>
              <span>⏱️ Processing time: {formatProcessingTime(file.processingTime)}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );

  const StatsCards = () => (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
      {[
        { label: 'Total', value: stats.total, color: 'bg-gray-100 text-gray-800', icon: FileText },
        { label: 'Pending', value: stats.pending, color: 'bg-yellow-100 text-yellow-800', icon: Clock },
        { label: 'Processing', value: stats.processing, color: 'bg-blue-100 text-blue-800', icon: RefreshCw },
        { label: 'Completed', value: stats.completed, color: 'bg-green-100 text-green-800', icon: CheckCircle },
        { label: 'Errors', value: stats.error, color: 'bg-red-100 text-red-800', icon: AlertCircle }
      ].map((stat, index) => {
        const Icon = stat.icon;
        return (
          <div key={index} className="bg-white rounded-lg border border-gray-200 p-4 text-center">
            <Icon className="w-6 h-6 mx-auto mb-2 text-gray-600" />
            <div className={`text-2xl font-bold ${stat.color.split(' ')[1]}`}>
              {stat.value}
            </div>
            <div className="text-sm text-gray-600">{stat.label}</div>
          </div>
        );
      })}
    </div>
  );

  // Preview Modal
  const PreviewModal = ({ file, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-4xl max-h-full overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{file.name}</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPreviewZoom(Math.max(0.5, previewZoom - 0.25))}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-sm text-gray-600">{Math.round(previewZoom * 100)}%</span>
            <button
              onClick={() => setPreviewZoom(Math.min(3, previewZoom + 0.25))}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
        <div className="p-4 max-h-96 overflow-auto">
          <div 
            className="mx-auto"
            style={{ transform: `scale(${previewZoom})`, transformOrigin: 'top center' }}
          >
            <img 
              src={file.resultUrl} 
              alt={`Preview of ${file.name}`}
              className="max-w-full h-auto border border-gray-200 rounded"
            />
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Document Translator</h1>
                <p className="text-sm text-gray-500">Arabic to English Translation Pipeline</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                <span className="font-medium">{stats.completed}</span> of <span className="font-medium">{stats.total}</span> completed
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex space-x-8">
            {[
              { id: 'upload', label: 'Upload', icon: Upload, count: stats.total },
              { id: 'processing', label: 'Processing', icon: RefreshCw, count: stats.processing + stats.pending },
              { id: 'results', label: 'Results', icon: CheckCircle, count: stats.completed }
            ].map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setSelectedView(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium text-sm transition-colors duration-200 ${
                    selectedView === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                  {tab.count > 0 && (
                    <span className="bg-gray-200 text-gray-700 text-xs rounded-full px-2 py-1 min-w-[20px] text-center">
                      {tab.count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <StatsCards />
        
        {selectedView === 'upload' && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Upload Documents</h2>
              <p className="text-gray-600 text-lg">Start by uploading your Arabic documents for translation</p>
            </div>
            <UploadArea />
            {files.length > 0 && <FileList />}
          </div>
        )}

        {selectedView === 'processing' && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Processing Queue</h2>
              <p className="text-gray-600 text-lg">Monitor your document translation progress</p>
            </div>
            {stats.processing + stats.pending > 0 ? (
              <FileList />
            ) : (
              <div className="text-center py-16">
                <Clock className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                <h3 className="text-xl font-medium text-gray-900 mb-2">No files processing</h3>
                <p className="text-gray-500 text-lg">Upload documents to start the translation process</p>
                <button
                  onClick={() => setSelectedView('upload')}
                  className="mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
                >
                  Upload Documents
                </button>
              </div>
            )}
          </div>
        )}

        {selectedView === 'results' && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Translation Results</h2>
              <p className="text-gray-600 text-lg">Download and view your translated documents</p>
            </div>
            {stats.completed > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {files.filter(f => f.status === 'completed').map(file => (
                  <div key={file.id} className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow duration-200">
                    <div className="flex items-center space-x-3 mb-4">
                      <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                        <CheckCircle className="w-6 h-6 text-green-600" />
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">{file.name}</h4>
                        <p className="text-sm text-gray-500">
                          Completed {file.completedAt?.toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    {file.originalPages && (
                      <div className="mb-4 text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
                        <div className="flex justify-between">
                          <span>Pages: {file.originalPages}</span>
                          <span>Time: {formatProcessingTime(file.processingTime)}</span>
                        </div>
                      </div>
                    )}
                    
                    <div className="space-y-3">
                      <button 
                        onClick={() => openPreview(file)}
                        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 flex items-center justify-center space-x-2"
                      >
                        <Eye className="w-4 h-4" />
                        <span>Preview</span>
                      </button>
                      <button className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200 flex items-center justify-center space-x-2">
                        <Download className="w-4 h-4" />
                        <span>Download</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <CheckCircle className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                <h3 className="text-xl font-medium text-gray-900 mb-2">No completed translations</h3>
                <p className="text-gray-500 text-lg">Translated documents will appear here when ready</p>
                <button
                  onClick={() => setSelectedView('upload')}
                  className="mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
                >
                  Upload Documents
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Preview Modal */}
      {previewFile && (
        <PreviewModal file={previewFile} onClose={closePreview} />
      )}
    </div>
  );
};

export default DocumentTranslationApp; 