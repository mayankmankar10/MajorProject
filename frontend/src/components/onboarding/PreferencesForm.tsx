import React, { useState } from 'react'
import { apiClient } from '@/services/api'

interface PreferencesFormProps {
    employeeId: number
    onComplete: () => void
    onCancel: () => void
}

export const PreferencesForm: React.FC<PreferencesFormProps> = ({ employeeId, onComplete, onCancel }) => {
    const [formData, setFormData] = useState({
        preferred_role: '',
        preferred_location: '',
        preferred_shift: '',
        expected_salary_min: '',
        expected_salary_max: ''
    })
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Match backend RestaurantRole enum values (lowercase)
    const roles = [
        { value: 'waiter', label: 'Waiter/Waitress' },
        { value: 'cook', label: 'Cook' },
        { value: 'chef', label: 'Chef' },
        { value: 'bartender', label: 'Bartender' },
        { value: 'host', label: 'Host/Hostess' },
        { value: 'dishwasher', label: 'Dishwasher' }
    ]

    const shifts = [
        'Morning (6 AM - 2 PM)',
        'Afternoon (2 PM - 10 PM)',
        'Evening (6 PM - 12 AM)',
        'Night (10 PM - 6 AM)',
        'Flexible'
    ]

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsSubmitting(true)
        setError(null)

        try {
            // Convert salary strings to numbers for API
            const preferences = {
                preferred_role: formData.preferred_role,
                preferred_location: formData.preferred_location,
                preferred_shift: formData.preferred_shift,
                expected_salary_min: formData.expected_salary_min ? parseInt(formData.expected_salary_min) : undefined,
                expected_salary_max: formData.expected_salary_max ? parseInt(formData.expected_salary_max) : undefined
            }

            await apiClient.updateJobPreferences(employeeId, preferences)
            onComplete()
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update preferences')
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
                    Preferred Role
                </label>
                <select
                    value={formData.preferred_role}
                    onChange={(e) => setFormData({ ...formData, preferred_role: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                    <option value="">Select a role...</option>
                    {roles.map((role) => (
                        <option key={role.value} value={role.value}>
                            {role.label}
                        </option>
                    ))}
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Preferred Location
                </label>
                <input
                    type="text"
                    value={formData.preferred_location}
                    onChange={(e) => setFormData({ ...formData, preferred_location: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., Mumbai, Bangalore"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Preferred Shift
                </label>
                <select
                    value={formData.preferred_shift}
                    onChange={(e) => setFormData({ ...formData, preferred_shift: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                    <option value="">Select a shift...</option>
                    {shifts.map((shift) => (
                        <option key={shift} value={shift}>
                            {shift}
                        </option>
                    ))}
                </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Min Salary (₹/month)
                    </label>
                    <input
                        type="number"
                        min="0"
                        step="1000"
                        value={formData.expected_salary_min}
                        onChange={(e) => setFormData({ ...formData, expected_salary_min: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="15000"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Max Salary (₹/month)
                    </label>
                    <input
                        type="number"
                        min="0"
                        step="1000"
                        value={formData.expected_salary_max}
                        onChange={(e) => setFormData({ ...formData, expected_salary_max: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="30000"
                    />
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
                    {isSubmitting ? 'Saving...' : 'Save Preferences'}
                </button>
            </div>
        </form>
    )
}
