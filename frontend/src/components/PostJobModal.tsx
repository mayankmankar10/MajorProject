import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Modal, Button, Input } from '@/components'
import { Briefcase, MapPin, DollarSign, Users, Clock, Award, ChefHat } from 'lucide-react'
import { apiClient } from '@/services/api'

interface PostJobModalProps {
    isOpen: boolean
    onClose: () => void
    onSuccess: () => void
}

interface JobFormData {
    title: string
    skills: string[]
    location: string
    job_type: string
    salary_min: number
    salary_max: number
    shift_type: string
    min_hospitality_experience: number
    job_category: string
    cuisine_type: string
    quantity_needed: number
}

const initialFormData: JobFormData = {
    title: '',
    skills: [],
    location: '',
    job_type: 'full_time',
    salary_min: 15000,
    salary_max: 30000,
    shift_type: 'morning',
    min_hospitality_experience: 0,
    job_category: '',
    cuisine_type: '',
    quantity_needed: 1,
}

export const PostJobModal: React.FC<PostJobModalProps> = ({ isOpen, onClose, onSuccess }) => {
    const [formData, setFormData] = useState<JobFormData>(initialFormData)
    const [skillInput, setSkillInput] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [errors, setErrors] = useState<Record<string, string>>({})

    const jobCategories = [
        { value: 'waiter', label: 'Waiter/Server' },
        { value: 'cook', label: 'Cook' },
        { value: 'chef', label: 'Chef' },
        { value: 'bartender', label: 'Bartender' },
        { value: 'host', label: 'Host/Hostess' },
        { value: 'dishwasher', label: 'Dishwasher' },
        { value: 'other', label: 'Other' },
    ]

    const jobTypes = [
        { value: 'full_time', label: 'Full Time' },
        { value: 'part_time', label: 'Part Time' },
        { value: 'contract', label: 'Contract' },
    ]

    const shiftTypes = [
        { value: 'morning', label: 'Morning (6 AM - 2 PM)' },
        { value: 'afternoon', label: 'Afternoon (2 PM - 10 PM)' },
        { value: 'evening', label: 'Evening (6 PM - 12 AM)' },
        { value: 'night', label: 'Night (10 PM - 6 AM)' },
    ]

    const cuisineTypes = [
        { value: 'italian', label: 'Italian' },
        { value: 'chinese', label: 'Chinese' },
        { value: 'indian', label: 'Indian' },
        { value: 'mexican', label: 'Mexican' },
        { value: 'french', label: 'French' },
        { value: 'japanese', label: 'Japanese' },
        { value: 'thai', label: 'Thai' },
        { value: 'mediterranean', label: 'Mediterranean' },
        { value: 'american', label: 'American' },
        { value: 'other', label: 'Other' },
    ]

    const handleInputChange = (field: keyof JobFormData, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        // Clear error for this field
        if (errors[field]) {
            setErrors(prev => {
                const newErrors = { ...prev }
                delete newErrors[field]
                return newErrors
            })
        }
    }

    const handleAddSkill = () => {
        if (skillInput.trim() && !formData.skills.includes(skillInput.trim())) {
            setFormData(prev => ({
                ...prev,
                skills: [...prev.skills, skillInput.trim()]
            }))
            setSkillInput('')
        }
    }

    const handleRemoveSkill = (skill: string) => {
        setFormData(prev => ({
            ...prev,
            skills: prev.skills.filter(s => s !== skill)
        }))
    }

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault()
            handleAddSkill()
        }
    }

    const validate = (): boolean => {
        const newErrors: Record<string, string> = {}

        if (!formData.title.trim()) {
            newErrors.title = 'Job title is required'
        }

        if (formData.skills.length === 0) {
            newErrors.skills = 'At least one skill is required'
        }

        if (!formData.location.trim()) {
            newErrors.location = 'Location is required'
        }

        if (!formData.job_category) {
            newErrors.job_category = 'Job category is required'
        }

        if (formData.salary_min <= 0) {
            newErrors.salary_min = 'Minimum salary must be greater than 0'
        }

        if (formData.salary_max <= 0) {
            newErrors.salary_max = 'Maximum salary must be greater than 0'
        }

        if (formData.salary_max < formData.salary_min) {
            newErrors.salary_max = 'Maximum salary must be greater than or equal to minimum salary'
        }

        if (formData.min_hospitality_experience < 0) {
            newErrors.min_hospitality_experience = 'Experience cannot be negative'
        }

        if (formData.quantity_needed < 1) {
            newErrors.quantity_needed = 'At least 1 position is required'
        }

        // Cuisine type required for cook/chef
        if ((formData.job_category === 'cook' || formData.job_category === 'chef') && !formData.cuisine_type) {
            newErrors.cuisine_type = 'Cuisine type is required for cook/chef positions'
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)

        if (!validate()) {
            return
        }

        setIsSubmitting(true)

        try {
            // Call the API to create the job
            await apiClient.createJob(formData)

            // Reset form
            setFormData(initialFormData)
            setSkillInput('')

            // Notify success
            onSuccess()
            onClose()
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to post job. Please try again.')
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleClose = () => {
        if (!isSubmitting) {
            setFormData(initialFormData)
            setSkillInput('')
            setError(null)
            setErrors({})
            onClose()
        }
    }

    const isCookOrChef = formData.job_category === 'cook' || formData.job_category === 'chef'

    return (
        <Modal
            isOpen={isOpen}
            onClose={handleClose}
            title="Post New Job"
            size="xl"
            closeOnOverlayClick={!isSubmitting}
        >
            <form onSubmit={handleSubmit} className="space-y-6">
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm"
                    >
                        {error}
                    </motion.div>
                )}

                {/* Job Title */}
                <div>
                    <Input
                        label="Job Title"
                        placeholder="e.g., Senior Chef"
                        value={formData.title}
                        onChange={(e) => handleInputChange('title', e.target.value)}
                        error={errors.title}
                        leftIcon={<Briefcase className="w-5 h-5" />}
                        required
                        fullWidth
                    />
                </div>

                {/* Job Category */}
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                        Job Category <span className="text-danger-600 ml-1">*</span>
                    </label>
                    <select
                        value={formData.job_category}
                        onChange={(e) => handleInputChange('job_category', e.target.value)}
                        className={`w-full px-4 py-2 text-base rounded-lg border-2 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-10 ${errors.job_category
                            ? 'border-danger-500 focus:border-danger-500'
                            : 'border-slate-300 focus:border-primary-500'
                            }`}
                        required
                    >
                        <option value="">Select a category...</option>
                        {jobCategories.map((cat) => (
                            <option key={cat.value} value={cat.value}>
                                {cat.label}
                            </option>
                        ))}
                    </select>
                    {errors.job_category && (
                        <motion.p
                            initial={{ opacity: 0, y: -4 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-sm text-danger-600 mt-1"
                        >
                            {errors.job_category}
                        </motion.p>
                    )}
                </div>

                {/* Cuisine Type (Conditional) */}
                {isCookOrChef && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                    >
                        <label className="block text-sm font-medium text-slate-700 mb-1.5">
                            Cuisine Type <span className="text-danger-600 ml-1">*</span>
                        </label>
                        <div className="relative">
                            <ChefHat className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                            <select
                                value={formData.cuisine_type}
                                onChange={(e) => handleInputChange('cuisine_type', e.target.value)}
                                className={`w-full pl-10 pr-4 py-2 text-base rounded-lg border-2 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-10 ${errors.cuisine_type
                                    ? 'border-danger-500 focus:border-danger-500'
                                    : 'border-slate-300 focus:border-primary-500'
                                    }`}
                                required
                            >
                                <option value="">Select a cuisine...</option>
                                {cuisineTypes.map((cuisine) => (
                                    <option key={cuisine.value} value={cuisine.value}>
                                        {cuisine.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                        {errors.cuisine_type && (
                            <motion.p
                                initial={{ opacity: 0, y: -4 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="text-sm text-danger-600 mt-1"
                            >
                                {errors.cuisine_type}
                            </motion.p>
                        )}
                    </motion.div>
                )}

                {/* Skills Input */}
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                        Required Skills <span className="text-danger-600 ml-1">*</span>
                    </label>
                    <div className="flex gap-2">
                        <Input
                            placeholder="Type a skill and press Enter"
                            value={skillInput}
                            onChange={(e) => setSkillInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            leftIcon={<Award className="w-5 h-5" />}
                            fullWidth
                        />
                        <Button
                            type="button"
                            variant="secondary"
                            size="md"
                            onClick={handleAddSkill}
                            disabled={!skillInput.trim()}
                        >
                            Add
                        </Button>
                    </div>
                    {errors.skills && (
                        <motion.p
                            initial={{ opacity: 0, y: -4 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-sm text-danger-600 mt-1"
                        >
                            {errors.skills}
                        </motion.p>
                    )}
                    {formData.skills.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-3">
                            {formData.skills.map((skill) => (
                                <motion.span
                                    key={skill}
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium flex items-center gap-2"
                                >
                                    {skill}
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveSkill(skill)}
                                        className="hover:text-primary-900"
                                    >
                                        ×
                                    </button>
                                </motion.span>
                            ))}
                        </div>
                    )}
                </div>

                {/* Location */}
                <div>
                    <Input
                        label="Location"
                        placeholder="e.g., Bandra, Mumbai"
                        value={formData.location}
                        onChange={(e) => handleInputChange('location', e.target.value)}
                        error={errors.location}
                        leftIcon={<MapPin className="w-5 h-5" />}
                        required
                        fullWidth
                    />
                </div>

                {/* Grid Layout for smaller fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Job Type */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1.5">
                            Job Type <span className="text-danger-600 ml-1">*</span>
                        </label>
                        <select
                            value={formData.job_type}
                            onChange={(e) => handleInputChange('job_type', e.target.value)}
                            className="w-full px-4 py-2 text-base rounded-lg border-2 border-slate-300 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-10"
                            required
                        >
                            {jobTypes.map((type) => (
                                <option key={type.value} value={type.value}>
                                    {type.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Shift Type */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1.5">
                            Shift Type <span className="text-danger-600 ml-1">*</span>
                        </label>
                        <select
                            value={formData.shift_type}
                            onChange={(e) => handleInputChange('shift_type', e.target.value)}
                            className="w-full px-4 py-2 text-base rounded-lg border-2 border-slate-300 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-10"
                            required
                        >
                            {shiftTypes.map((shift) => (
                                <option key={shift.value} value={shift.value}>
                                    {shift.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Salary Range */}
                    <div>
                        <Input
                            label="Minimum Salary (₹/month)"
                            type="number"
                            min="0"
                            step="1000"
                            value={formData.salary_min}
                            onChange={(e) => handleInputChange('salary_min', parseInt(e.target.value) || 0)}
                            error={errors.salary_min}
                            leftIcon={<DollarSign className="w-5 h-5" />}
                            required
                            fullWidth
                        />
                    </div>

                    <div>
                        <Input
                            label="Maximum Salary (₹/month)"
                            type="number"
                            min="0"
                            step="1000"
                            value={formData.salary_max}
                            onChange={(e) => handleInputChange('salary_max', parseInt(e.target.value) || 0)}
                            error={errors.salary_max}
                            leftIcon={<DollarSign className="w-5 h-5" />}
                            required
                            fullWidth
                        />
                    </div>

                    {/* Hospitality Experience */}
                    <div>
                        <Input
                            label="Minimum Hospitality Experience (years)"
                            type="number"
                            min="0"
                            value={formData.min_hospitality_experience}
                            onChange={(e) => handleInputChange('min_hospitality_experience', parseInt(e.target.value) || 0)}
                            error={errors.min_hospitality_experience}
                            leftIcon={<Clock className="w-5 h-5" />}
                            required
                            fullWidth
                        />
                    </div>

                    {/* Quantity Needed */}
                    <div>
                        <Input
                            label="Number of Positions"
                            type="number"
                            min="1"
                            value={formData.quantity_needed}
                            onChange={(e) => handleInputChange('quantity_needed', parseInt(e.target.value) || 1)}
                            error={errors.quantity_needed}
                            leftIcon={<Users className="w-5 h-5" />}
                            required
                            fullWidth
                        />
                    </div>
                </div>

                {/* Footer Buttons */}
                <div className="flex gap-3 pt-4 border-t border-slate-200">
                    <Button
                        type="button"
                        variant="secondary"
                        size="md"
                        onClick={handleClose}
                        disabled={isSubmitting}
                        className="flex-1"
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        variant="primary"
                        size="md"
                        disabled={isSubmitting}
                        className="flex-1"
                    >
                        {isSubmitting ? 'Posting Job...' : 'Post Job'}
                    </Button>
                </div>
            </form>
        </Modal>
    )
}
