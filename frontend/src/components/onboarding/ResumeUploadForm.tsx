import React, { useState, useRef } from 'react'
import { apiClient } from '@/services/api'
import { Upload, File, CheckCircle, AlertCircle, Sparkles } from 'lucide-react'

interface ResumeUploadFormProps {
    employeeId: number
    onComplete: () => void
    onCancel: () => void
}

export const ResumeUploadForm: React.FC<ResumeUploadFormProps> = ({ employeeId, onComplete, onCancel }) => {
    const [mode, setMode] = useState<'upload' | 'generate'>('generate') // Default to AI generation
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [isUploading, setIsUploading] = useState(false)
    const [isGenerating, setIsGenerating] = useState(false)
    const [uploadProgress, setUploadProgress] = useState(0)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState(false)
    const [generatedResume, setGeneratedResume] = useState<string | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    ]

    const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt']

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        // Validate file type
        if (!allowedTypes.includes(file.type)) {
            setError('Invalid file type. Please upload PDF, DOC, DOCX, or TXT files only.')
            setSelectedFile(null)
            return
        }

        // Validate file size (max 5MB)
        const maxSize = 5 * 1024 * 1024 // 5MB
        if (file.size > maxSize) {
            setError('File size exceeds 5MB. Please upload a smaller file.')
            setSelectedFile(null)
            return
        }

        setError(null)
        setSelectedFile(file)
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        const file = e.dataTransfer.files?.[0]
        if (file) {
            const input = fileInputRef.current
            if (input) {
                const dataTransfer = new DataTransfer()
                dataTransfer.items.add(file)
                input.files = dataTransfer.files
                handleFileSelect({ target: input } as any)
            }
        }
    }

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault()
    }

    const handleGenerateResume = async () => {
        setIsGenerating(true)
        setError(null)


        try {
            const result = await apiClient.generateResume(employeeId, false, 'text')

            if (result.success) {
                setGeneratedResume(result.resume_content)
                setSuccess(true)
                // Don't auto-complete - let user download PDF and click "Use This Resume"
            } else {
                setError(result.error || 'Failed to generate resume')
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to generate resume')
        } finally {
            setIsGenerating(false)
        }
    }

    const handleUploadResume = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!selectedFile) {
            setError('Please select a file to upload')
            return
        }

        setIsUploading(true)
        setError(null)
        setUploadProgress(0)

        try {
            // Simulate upload progress
            const progressInterval = setInterval(() => {
                setUploadProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval)
                        return 90
                    }
                    return prev + 10
                })
            }, 100)

            await apiClient.uploadEmployeeResume(employeeId, selectedFile)

            clearInterval(progressInterval)
            setUploadProgress(100)
            setSuccess(true)

            // Wait a moment to show success state
            setTimeout(() => {
                onComplete()
            }, 500)
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to upload resume')
            setUploadProgress(0)
        } finally {
            setIsUploading(false)
        }
    }

    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes'
        const k = 1024
        const sizes = ['Bytes', 'KB', 'MB']
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    }

    return (
        <div className="space-y-4">
            {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-start gap-2">
                    <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
                    <span>{error}</span>
                </div>
            )}

            {success && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm flex items-start gap-2">
                    <CheckCircle size={16} className="mt-0.5 flex-shrink-0" />
                    <span>{mode === 'generate' ? 'Resume generated successfully!' : 'Resume uploaded successfully!'}</span>
                </div>
            )}

            {/* Mode Selection */}
            <div className="flex gap-2 p-1 bg-gray-100 rounded-lg">
                <button
                    type="button"
                    onClick={() => setMode('generate')}
                    className={`flex-1 px-4 py-2 rounded-md font-medium text-sm transition-all ${mode === 'generate'
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    <Sparkles className="inline-block w-4 h-4 mr-1" />
                    AI Generate
                </button>
                <button
                    type="button"
                    onClick={() => setMode('upload')}
                    className={`flex-1 px-4 py-2 rounded-md font-medium text-sm transition-all ${mode === 'upload'
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                        }`}
                >
                    <Upload className="inline-block w-4 h-4 mr-1" />
                    Upload File
                </button>
            </div>

            {/* AI Generation Mode */}
            {mode === 'generate' && (
                <div className="space-y-4">
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-start gap-3">
                            <Sparkles className="text-blue-600 mt-1 flex-shrink-0" size={20} />
                            <div>
                                <h4 className="font-medium text-blue-900 mb-1">AI-Powered Resume Generation</h4>
                                <p className="text-sm text-blue-700">
                                    Our AI will create a professional, ATS-optimized resume based on your profile information,
                                    skills, and experience. Perfect for the restaurant and hospitality industry!
                                </p>
                            </div>
                        </div>
                    </div>

                    {generatedResume && (
                        <div className="space-y-3">
                            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg max-h-96 overflow-y-auto">
                                <h4 className="font-medium text-gray-900 mb-2">Generated Resume Preview:</h4>
                                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
                                    {generatedResume}
                                </pre>
                            </div>

                            {/* Action buttons for generated resume */}
                            <div className="flex gap-3">
                                <button
                                    type="button"
                                    onClick={async () => {
                                        try {
                                            const response = await fetch(`http://localhost:8000/api/employee/employees/${employeeId}/resume/download`)
                                            const blob = await response.blob()
                                            const url = window.URL.createObjectURL(blob)
                                            const a = document.createElement('a')
                                            a.href = url
                                            a.download = `resume_${employeeId}.pdf`
                                            document.body.appendChild(a)
                                            a.click()
                                            window.URL.revokeObjectURL(url)
                                            document.body.removeChild(a)
                                        } catch (error) {
                                            console.error('Download failed:', error)
                                        }
                                    }}
                                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center justify-center gap-2"
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    Download PDF
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        // Resume is already saved, just complete the step
                                        onComplete()
                                    }}
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center gap-2"
                                >
                                    <CheckCircle size={18} />
                                    Use This Resume
                                </button>
                            </div>
                        </div>
                    )}

                    {!generatedResume && (
                        <button
                            type="button"
                            onClick={handleGenerateResume}
                            disabled={isGenerating || success}
                            className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium flex items-center justify-center gap-2"
                        >
                            {isGenerating ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                                    Generating Resume...
                                </>
                            ) : (
                                <>
                                    <Sparkles size={18} />
                                    Generate My Resume with AI
                                </>
                            )}
                        </button>
                    )}
                </div>
            )}

            {/* Upload Mode */}
            {mode === 'upload' && (
                <form onSubmit={handleUploadResume} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Upload Resume
                        </label>
                        <div
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors cursor-pointer"
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept={allowedExtensions.join(',')}
                                onChange={handleFileSelect}
                                className="hidden"
                            />

                            {!selectedFile ? (
                                <div className="space-y-2">
                                    <Upload className="mx-auto text-gray-400" size={40} />
                                    <p className="text-sm text-gray-600">
                                        Click to upload or drag and drop
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        PDF, DOC, DOCX, or TXT (max 5MB)
                                    </p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    <File className="mx-auto text-blue-600" size={40} />
                                    <p className="text-sm font-medium text-gray-900">
                                        {selectedFile.name}
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        {formatFileSize(selectedFile.size)}
                                    </p>
                                    {isUploading && (
                                        <div className="mt-3">
                                            <div className="w-full bg-gray-200 rounded-full h-2">
                                                <div
                                                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                                    style={{ width: `${uploadProgress}%` }}
                                                />
                                            </div>
                                            <p className="text-xs text-gray-600 mt-1">
                                                Uploading... {uploadProgress}%
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={!selectedFile || isUploading || success}
                        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {isUploading ? 'Uploading...' : success ? 'Uploaded!' : 'Upload Resume'}
                    </button>
                </form>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-2">
                <button
                    type="button"
                    onClick={onCancel}
                    disabled={isUploading || isGenerating}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    Cancel
                </button>
            </div>
        </div>
    )
}
