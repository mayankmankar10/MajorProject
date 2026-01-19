import React, { useState } from 'react'
import { apiClient } from '@/services/api'

interface CompanyProfileFormProps {
    onComplete: () => void
    onCancel: () => void
}

export const CompanyProfileForm: React.FC<CompanyProfileFormProps> = ({ onComplete, onCancel }) => {
    const [formData, setFormData] = useState({
        company_profile: '',
        industry: '',
        location: '',
        website: ''
    })
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const industries = [
        'Restaurant & Food Service',
        'Fine Dining',
        'Casual Dining',
        'Fast Food / QSR',
        'Cloud Kitchen',
        'Catering',
        'Hospitality & Hotels',
        'Café & Bakery',
        'Bar & Nightlife',
        'Other'
    ]

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsSubmitting(true)
        setError(null)

        // Validation
        if (!formData.company_profile || formData.company_profile.length < 50) {
            setError('Company description must be at least 50 characters')
            setIsSubmitting(false)
            return
        }

        if (!formData.industry) {
            setError('Please select an industry')
            setIsSubmitting(false)
            return
        }

        if (!formData.location) {
            setError('Location is required')
            setIsSubmitting(false)
            return
        }

        try {
            await apiClient.updateEmployerProfile(formData)
            onComplete()
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update profile')
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
                    Company Description *
                </label>
                <textarea
                    value={formData.company_profile}
                    onChange={(e) => setFormData({ ...formData, company_profile: e.target.value })}
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Tell candidates about your company, your values, and what makes you a great place to work..."
                    required
                />
                <p className="text-xs text-gray-500 mt-1">
                    {formData.company_profile.length}/500 characters (minimum 50)
                </p>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Industry *
                </label>
                <select
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                >
                    <option value="">Select industry...</option>
                    {industries.map((industry) => (
                        <option key={industry} value={industry}>
                            {industry}
                        </option>
                    ))}
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Main Location *
                </label>
                <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., Mumbai, Maharashtra"
                    required
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Website (Optional)
                </label>
                <input
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="https://www.yourcompany.com"
                />
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
                    {isSubmitting ? 'Saving...' : 'Save Profile'}
                </button>
            </div>
        </form>
    )
}
