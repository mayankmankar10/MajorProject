import React from 'react'
import { X } from 'lucide-react'

interface OnboardingModalProps {
    isOpen: boolean
    onClose: () => void
    title: string
    children: React.ReactNode
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
    isOpen,
    onClose,
    title,
    children
}) => {
    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto m-4 shadow-2xl">
                <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        aria-label="Close"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>
                <div className="p-6">
                    {children}
                </div>
            </div>
        </div>
    )
}
