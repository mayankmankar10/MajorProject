import React, { useState } from 'react'
import { Trash2, Plus } from 'lucide-react'
import { apiClient } from '@/services/api'

interface HiringPreference {
    role: string
    positions: number
    location: string
    shift: string
    salary_min: number
    salary_max: number
}

interface HiringPreferencesFormProps {
    onComplete: () => void
    onCancel: () => void
}

export const HiringPreferencesForm: React.FC<HiringPreferencesFormProps> = ({ onComplete, onCancel }) => {
    const [preferences, setPreferences] = useState<HiringPreference[]>([
        {
            role: '',
            positions: 1,
            location: '',
            shift: '',
            salary_min: 15000,
            salary_max: 30000
        }
    ])
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const roles = [
        { value: 'waiter', label: 'Waiter/Waitress' },
        { value: 'cook', label: 'Cook' },
        { value: 'chef', label: 'Chef' },
        { value: 'bartender', label: 'Bartender' },
        { value: 'host', label: 'Host/Hostess' },
        { value: 'dishwasher', label: 'Dishwasher' }
    ]

    const shifts = [
        { value: 'morning', label: 'Morning (6 AM - 2 PM)' },
        { value: 'afternoon', label: 'Afternoon (2 PM - 10 PM)' },
        { value: 'evening', label: 'Evening (6 PM - 12 AM)' },
        { value: 'night', label: 'Night (10 PM - 6 AM)' },
        { value: 'flexible', label: 'Flexible' }
    ]

    const addPreference = () => {
        setPreferences([
            ...preferences,
            {
                role: '',
                positions: 1,
                location: '',
                shift: '',
                salary_min: 15000,
                salary_max: 30000
            }
        ])
    }

    const removePreference = (index: number) => {
        if (preferences.length === 1) {
            setError('At least one job type is required')
            return
        }
        setPreferences(preferences.filter((_, i) => i !== index))
    }

    const updatePreference = (index: number, field: keyof HiringPreference, value: any) => {
        const updated = [...preferences]
        updated[index] = { ...updated[index], [field]: value }
        setPreferences(updated)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsSubmitting(true)
        setError(null)

        // Validation
        for (let i = 0; i < preferences.length; i++) {
            const pref = preferences[i]

            if (!pref.role) {
                setError(`Job role is required for preference ${i + 1}`)
                setIsSubmitting(false)
                return
            }

            if (!pref.location) {
                setError(`Location is required for ${pref.role}`)
                setIsSubmitting(false)
                return
            }

            if (!pref.shift) {
                setError(`Shift is required for ${pref.role}`)
                setIsSubmitting(false)
                return
            }

            if (pref.salary_max < pref.salary_min) {
                setError(`Max salary must be >= min salary for ${pref.role}`)
                setIsSubmitting(false)
                return
            }

            if (pref.positions < 1) {
                setError(`Positions must be at least 1 for ${pref.role}`)
                setIsSubmitting(false)
                return
            }
        }

        // Check for duplicate roles
        const roleSet = new Set(preferences.map(p => p.role))
        if (roleSet.size !== preferences.length) {
            setError('Duplicate roles are not allowed. Each role can only be added once.')
            setIsSubmitting(false)
            return
        }

        try {
            await apiClient.updateEmployerHiringPreferences({ preferences })
            onComplete()
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to save hiring preferences')
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    {error}
                </div>
            )}

            <div className="space-y-4">
                {preferences.map((pref, index) => (
                    <div key={index} className="p-4 border border-gray-200 rounded-lg bg-gray-50 space-y-3">
                        <div className="flex items-center justify-between mb-3">
                            <h4 className="font-medium text-gray-900">Job Type #{index + 1}</h4>
                            {preferences.length > 1 && (
                                <button
                                    type="button"
                                    onClick={() => removePreference(index)}
                                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                    title="Remove"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            )}
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div className="col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Job Role *
                                </label>
                                <select
                                    value={pref.role}
                                    onChange={(e) => updatePreference(index, 'role', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    required
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
                                    Positions Needed *
                                </label>
                                <input
                                    type="number"
                                    min="1"
                                    value={pref.positions}
                                    onChange={(e) => updatePreference(index, 'positions', parseInt(e.target.value))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Preferred Shift *
                                </label>
                                <select
                                    value={pref.shift}
                                    onChange={(e) => updatePreference(index, 'shift', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    required
                                >
                                    <option value="">Select a shift...</option>
                                    {shifts.map((shift) => (
                                        <option key={shift.value} value={shift.value}>
                                            {shift.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Location *
                                </label>
                                <input
                                    type="text"
                                    value={pref.location}
                                    onChange={(e) => updatePreference(index, 'location', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="e.g., Bandra, Mumbai"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Min Salary (₹/month) *
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    step="1000"
                                    value={pref.salary_min}
                                    onChange={(e) => updatePreference(index, 'salary_min', parseInt(e.target.value))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Max Salary (₹/month) *
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    step="1000"
                                    value={pref.salary_max}
                                    onChange={(e) => updatePreference(index, 'salary_max', parseInt(e.target.value))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    required
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <button
                type="button"
                onClick={addPreference}
                className="w-full px-4 py-2 border-2 border-dashed border-gray-300 text-gray-600 rounded-lg hover:border-blue-500 hover:text-blue-600 transition-colors flex items-center justify-center gap-2"
            >
                <Plus className="w-5 h-5" />
                <span>Add Another Job Type</span>
            </button>

            <div className="flex gap-3 pt-4 border-t">
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
