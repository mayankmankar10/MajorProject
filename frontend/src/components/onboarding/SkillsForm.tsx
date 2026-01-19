import React, { useState } from 'react'
import { apiClient } from '@/services/api'
import { X } from 'lucide-react'

interface SkillsFormProps {
    employeeId: number
    onComplete: () => void
    onCancel: () => void
}

export const SkillsForm: React.FC<SkillsFormProps> = ({ employeeId, onComplete, onCancel }) => {
    const [skills, setSkills] = useState<string[]>([])
    const [currentSkill, setCurrentSkill] = useState('')
    const [softSkills, setSoftSkills] = useState<string[]>([])  // NEW: Soft skills
    const [currentSoftSkill, setCurrentSoftSkill] = useState('')  // NEW
    const [experienceYears, setExperienceYears] = useState<number>(0)
    const [yearsInHospitality, setYearsInHospitality] = useState<number>(0)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Common soft skills suggestions
    const COMMON_SOFT_SKILLS = [
        'Customer Service', 'Communication', 'Teamwork', 'Leadership',
        'Problem Solving', 'Time Management', 'Multitasking', 'Attention to Detail',
        'Adaptability', 'Work Ethic', 'Conflict Resolution', 'Patience'
    ]

    const handleAddSkill = () => {
        const trimmed = currentSkill.trim()
        if (trimmed && !skills.includes(trimmed)) {
            setSkills([...skills, trimmed])
            setCurrentSkill('')
        }
    }

    const handleRemoveSkill = (skillToRemove: string) => {
        setSkills(skills.filter(s => s !== skillToRemove))
    }

    const handleAddSoftSkill = (skill?: string) => {
        const trimmed = (skill || currentSoftSkill).trim()
        if (trimmed && !softSkills.includes(trimmed)) {
            setSoftSkills([...softSkills, trimmed])
            setCurrentSoftSkill('')
        }
    }

    const handleRemoveSoftSkill = (skillToRemove: string) => {
        setSoftSkills(softSkills.filter(s => s !== skillToRemove))
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault()
            handleAddSkill()
        }
    }

    const handleSoftSkillKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault()
            handleAddSoftSkill()
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (skills.length === 0) {
            setError('Please add at least one skill')
            return
        }

        setIsSubmitting(true)
        setError(null)

        try {
            await apiClient.addEmployeeSkills(employeeId, {
                skills,
                soft_skills: softSkills,  // NEW: Include soft skills
                experience_years: experienceYears,
                years_in_hospitality: yearsInHospitality
            })
            onComplete()
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update skills')
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
                    Skills *
                </label>
                <div className="space-y-2">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={currentSkill}
                            onChange={(e) => setCurrentSkill(e.target.value)}
                            onKeyDown={handleKeyDown}
                            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="e.g., Customer Service, Cooking, Bartending"
                        />
                        <button
                            type="button"
                            onClick={handleAddSkill}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Add
                        </button>
                    </div>
                    {skills.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                            {skills.map((skill) => (
                                <span
                                    key={skill}
                                    className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                                >
                                    {skill}
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveSkill(skill)}
                                        className="hover:text-blue-900"
                                    >
                                        <X size={14} />
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* NEW: Soft Skills Section */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Soft Skills (optional)
                    <span className="text-xs text-gray-500 ml-2">Communication, teamwork, etc.</span>
                </label>
                <div className="space-y-2">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={currentSoftSkill}
                            onChange={(e) => setCurrentSoftSkill(e.target.value)}
                            onKeyDown={handleSoftSkillKeyDown}
                            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="e.g., Customer Service, Communication"
                        />
                        <button
                            type="button"
                            onClick={() => handleAddSoftSkill()}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        >
                            Add
                        </button>
                    </div>

                    {/* Quick add suggestions */}
                    <div className="flex flex-wrap gap-2">
                        <span className="text-xs text-gray-600 w-full">Suggestions:</span>
                        {COMMON_SOFT_SKILLS.filter(s => !softSkills.includes(s)).slice(0, 6).map((skill) => (
                            <button
                                key={skill}
                                type="button"
                                onClick={() => handleAddSoftSkill(skill)}
                                className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-green-100 hover:text-green-700 transition-colors"
                            >
                                + {skill}
                            </button>
                        ))}
                    </div>

                    {softSkills.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                            {softSkills.map((skill) => (
                                <span
                                    key={skill}
                                    className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                                >
                                    {skill}
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveSoftSkill(skill)}
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

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Total Experience (Years)
                </label>
                <input
                    type="number"
                    min="0"
                    max="50"
                    value={experienceYears}
                    onChange={(e) => setExperienceYears(parseInt(e.target.value) || 0)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    Hospitality Experience (Years)
                </label>
                <input
                    type="number"
                    min="0"
                    max="50"
                    value={yearsInHospitality}
                    onChange={(e) => setYearsInHospitality(parseInt(e.target.value) || 0)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                    disabled={isSubmitting || skills.length === 0}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {isSubmitting ? 'Saving...' : 'Save Skills'}
                </button>
            </div>
        </form>
    )
}
