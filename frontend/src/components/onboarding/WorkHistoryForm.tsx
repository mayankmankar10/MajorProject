import React, { useState } from 'react'
import { apiClient } from '@/services/api'
import { X, Plus, Briefcase } from 'lucide-react'

interface WorkHistoryEntry {
    employer: string
    position: string
    location: string
    start_date: string  // YYYY-MM
    end_date: string | null  // YYYY-MM or null if current
    is_current: boolean
    achievements: string[]
}

interface WorkHistoryFormProps {
    employeeId: number
    onComplete: () => void
    onCancel: () => void
}

export const WorkHistoryForm: React.FC<WorkHistoryFormProps> = ({ employeeId, onComplete, onCancel }) => {
    const [workHistory, setWorkHistory] = useState<WorkHistoryEntry[]>([{
        employer: '',
        position: '',
        location: '',
        start_date: '',
        end_date: null,
        is_current: false,
        achievements: []
    }])
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleAddEntry = () => {
        setWorkHistory([...workHistory, {
            employer: '',
            position: '',
            location: '',
            start_date: '',
            end_date: null,
            is_current: false,
            achievements: []
        }])
    }

    const handleRemoveEntry = (index: number) => {
        setWorkHistory(workHistory.filter((_, i) => i !== index))
    }

    const handleUpdateEntry = (index: number, field: keyof WorkHistoryEntry, value: any) => {
        const updated = [...workHistory]
        updated[index] = { ...updated[index], [field]: value }

        // If marking as current, clear end_date
        if (field === 'is_current' && value === true) {
            updated[index].end_date = null
        }

        setWorkHistory(updated)
    }

    const handleAddAchievement = (entryIndex: number, achievement: string) => {
        const trimmed = achievement.trim()
        if (trimmed && !workHistory[entryIndex].achievements.includes(trimmed)) {
            const updated = [...workHistory]
            updated[entryIndex].achievements = [...updated[entryIndex].achievements, trimmed]
            setWorkHistory(updated)
        }
    }

    const handleRemoveAchievement = (entryIndex: number, achievementIndex: number) => {
        const updated = [...workHistory]
        updated[entryIndex].achievements = updated[entryIndex].achievements.filter((_, i) => i !== achievementIndex)
        setWorkHistory(updated)
    }

    const validateEntry = (entry: WorkHistoryEntry): boolean => {
        if (!entry.employer.trim() || !entry.position.trim() || !entry.start_date) {
            return false
        }
        // Validate date format YYYY-MM
        const dateRegex = /^\d{4}-\d{2}$/
        if (!dateRegex.test(entry.start_date)) {
            return false
        }
        if (entry.end_date && !dateRegex.test(entry.end_date)) {
            return false
        }
        return true
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        // Filter out empty entries and validate
        const validEntries = workHistory.filter(entry =>
            entry.employer.trim() || entry.position.trim() || entry.start_date
        )

        if (validEntries.length === 0) {
            setError('Please add at least one work experience')
            return
        }

        // Validate all entries
        for (const entry of validEntries) {
            if (!validateEntry(entry)) {
                setError('Please fill in all required fields (Employer, Position, Start Date) with valid dates (YYYY-MM)')
                return
            }
        }

        setIsSubmitting(true)
        setError(null)

        try {
            await apiClient.addWorkHistory(employeeId, { work_history: validEntries })
            onComplete()
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update work history')
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-6 max-h-[70vh] overflow-y-auto pr-2">
            {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    {error}
                </div>
            )}

            <div className="space-y-6">
                {workHistory.map((entry, entryIndex) => (
                    <div key={entryIndex} className="p-4 border-2 border-gray-200 rounded-lg bg-gray-50 relative">
                        {/* Remove button */}
                        {workHistory.length > 1 && (
                            <button
                                type="button"
                                onClick={() => handleRemoveEntry(entryIndex)}
                                className="absolute top-2 right-2 p-1 text-red-600 hover:bg-red-100 rounded transition-colors"
                                title="Remove this entry"
                            >
                                <X size={18} />
                            </button>
                        )}

                        <div className="flex items-center gap-2 mb-4">
                            <Briefcase size={20} className="text-blue-600" />
                            <h4 className="font-semibold text-gray-900">
                                Position {entryIndex + 1}
                            </h4>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Company/Restaurant *
                                </label>
                                <input
                                    type="text"
                                    value={entry.employer}
                                    onChange={(e) => handleUpdateEntry(entryIndex, 'employer', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="e.g., Taj Hotel, Olive Garden"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Position *
                                </label>
                                <input
                                    type="text"
                                    value={entry.position}
                                    onChange={(e) => handleUpdateEntry(entryIndex, 'position', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="e.g., Senior Bartender, Chef"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Location
                                </label>
                                <input
                                    type="text"
                                    value={entry.location}
                                    onChange={(e) => handleUpdateEntry(entryIndex, 'location', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="e.g., Mumbai, Bangalore"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Start Date * (YYYY-MM)
                                </label>
                                <input
                                    type="month"
                                    value={entry.start_date}
                                    onChange={(e) => handleUpdateEntry(entryIndex, 'start_date', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    End Date (YYYY-MM)
                                </label>
                                <input
                                    type="month"
                                    value={entry.end_date || ''}
                                    onChange={(e) => handleUpdateEntry(entryIndex, 'end_date', e.target.value || null)}
                                    disabled={entry.is_current}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-200 disabled:cursor-not-allowed"
                                />
                            </div>

                            <div className="flex items-center">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={entry.is_current}
                                        onChange={(e) => handleUpdateEntry(entryIndex, 'is_current', e.target.checked)}
                                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                    />
                                    <span className="text-sm font-medium text-gray-700">
                                        I currently work here
                                    </span>
                                </label>
                            </div>
                        </div>

                        {/* Achievements Section */}
                        <div className="mt-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Key Achievements & Responsibilities
                            </label>
                            <AchievementsList
                                achievements={entry.achievements}
                                onAdd={(achievement) => handleAddAchievement(entryIndex, achievement)}
                                onRemove={(achievementIndex) => handleRemoveAchievement(entryIndex, achievementIndex)}
                            />
                        </div>
                    </div>
                ))}
            </div>

            {/* Add Another Position Button */}
            <button
                type="button"
                onClick={handleAddEntry}
                className="w-full py-3 border-2 border-dashed border-gray-300 text-gray-600 rounded-lg hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-all flex items-center justify-center gap-2"
            >
                <Plus size={18} />
                Add Another Position
            </button>

            {/* Form Actions */}
            <div className="flex gap-3 pt-4 border-t">
                <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                    Skip for Now
                </button>
                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {isSubmitting ? 'Saving...' : 'Save Work History'}
                </button>
            </div>
        </form>
    )
}

// Achievements sub-component
const AchievementsList: React.FC<{
    achievements: string[]
    onAdd: (achievement: string) => void
    onRemove: (index: number) => void
}> = ({ achievements, onAdd, onRemove }) => {
    const [currentAchievement, setCurrentAchievement] = useState('')

    const handleAdd = () => {
        if (currentAchievement.trim()) {
            onAdd(currentAchievement)
            setCurrentAchievement('')
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault()
            handleAdd()
        }
    }

    return (
        <div className="space-y-2">
            <div className="flex gap-2">
                <input
                    type="text"
                    value={currentAchievement}
                    onChange={(e) => setCurrentAchievement(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    placeholder="e.g., Increased bar revenue by 20%, Trained 5 new staff members"
                />
                <button
                    type="button"
                    onClick={handleAdd}
                    className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                >
                    Add
                </button>
            </div>

            {achievements.length > 0 && (
                <ul className="space-y-2">
                    {achievements.map((achievement, index) => (
                        <li key={index} className="flex items-start gap-2 p-2 bg-white border border-gray-200 rounded-lg group">
                            <span className="flex-1 text-sm text-gray-700">• {achievement}</span>
                            <button
                                type="button"
                                onClick={() => onRemove(index)}
                                className="opacity-0 group-hover:opacity-100 p-1 text-red-600 hover:bg-red-100 rounded transition-all"
                            >
                                <X size={14} />
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}
