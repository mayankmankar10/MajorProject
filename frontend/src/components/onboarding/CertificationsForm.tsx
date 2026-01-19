import React, { useState } from 'react'
import { apiClient } from '@/services/api'
import { X } from 'lucide-react'

interface CertificationsFormProps {
    employeeId: number
    onComplete: () => void
    onCancel: () => void
}

export const CertificationsForm: React.FC<CertificationsFormProps> = ({ employeeId, onComplete, onCancel }) => {
    const [certifications, setCertifications] = useState<string[]>([])
    const [currentCert, setCurrentCert] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const commonCertifications = [
        'Food Safety Certificate',
        'ServSafe Certification',
        'Alcohol Service License',
        'First Aid & CPR',
        'Culinary Arts Diploma',
        'Sommelier Certification',
        'Barista Training Certificate'
    ]

    const handleAddCertification = (cert: string) => {
        const trimmed = cert.trim()
        if (trimmed && !certifications.includes(trimmed)) {
            setCertifications([...certifications, trimmed])
            setCurrentCert('')
        }
    }

    const handleRemoveCertification = (certToRemove: string) => {
        setCertifications(certifications.filter(c => c !== certToRemove))
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault()
            handleAddCertification(currentCert)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsSubmitting(true)
        setError(null)

        try {
            await apiClient.addCertifications(employeeId, {
                certifications: certifications.length > 0 ? certifications : []
            })
            onComplete()
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update certifications')
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    {error}
                </div>
            )}

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Certifications
                </label>
                <p className="text-xs text-gray-500 mb-2">
                    Add any relevant certifications or licenses you hold
                </p>
                <div className="space-y-2">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={currentCert}
                            onChange={(e) => setCurrentCert(e.target.value)}
                            onKeyDown={handleKeyDown}
                            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="e.g., Food Safety Certificate"
                        />
                        <button
                            type="button"
                            onClick={() => handleAddCertification(currentCert)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Add
                        </button>
                    </div>

                    {/* Common certifications quick add */}
                    <div className="flex flex-wrap gap-2">
                        {commonCertifications.map((cert) => (
                            !certifications.includes(cert) && (
                                <button
                                    key={cert}
                                    type="button"
                                    onClick={() => handleAddCertification(cert)}
                                    className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                                >
                                    + {cert}
                                </button>
                            )
                        ))}
                    </div>

                    {certifications.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-3">
                            {certifications.map((cert) => (
                                <span
                                    key={cert}
                                    className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                                >
                                    {cert}
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveCertification(cert)}
                                        className="hover:text-green-900"
                                    >
                                        <X size={14} />
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <div className="flex gap-3 pt-4">
                <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {isSubmitting ? 'Saving...' : certifications.length > 0 ? 'Save Certifications' : 'Skip This Step'}
                </button>
            </div>
        </form>
    )
}
