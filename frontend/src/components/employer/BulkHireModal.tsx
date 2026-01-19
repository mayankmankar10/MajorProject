import React, { useState, useEffect } from 'react'
import { X, Loader2, CheckCircle2, AlertCircle, Users } from 'lucide-react'
import { bulkHireApi, type BulkHireJob, type JobCandidates, type JobEmployeeSelection } from '@/services/bulkHireApi'
import { useAuthStore } from '@/stores/useAuthStore'

interface BulkHireModalProps {
    isOpen: boolean
    onClose: () => void
    onSuccess: (result: {
        totalHired: number
        resultsByJob: Array<{ jobTitle: string; candidates: Array<{ id: number; name: string; score?: number }> }>
    }) => void
}

type Step = 'select' | 'review' | 'processing' | 'success'

export const BulkHireModal: React.FC<BulkHireModalProps> = ({ isOpen, onClose, onSuccess }) => {
    const { user } = useAuthStore()
    const [step, setStep] = useState<Step>('select')
    const [jobs, setJobs] = useState<BulkHireJob[]>([])
    const [selectedJobs, setSelectedJobs] = useState<Map<number, number>>(new Map()) // job_id -> quantity
    const [matchesByJob, setMatchesByJob] = useState<JobCandidates[]>([])
    const [selectedCandidates, setSelectedCandidates] = useState<Map<number, Set<number>>>(new Map()) // job_id -> Set<employee_id>
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Load jobs when modal opens
    useEffect(() => {
        if (isOpen && user?.id) {
            loadJobs()
        }
    }, [isOpen, user?.id])

    const loadJobs = async () => {
        if (!user?.id) return

        setIsLoading(true)
        setError(null)

        try {
            const response = await bulkHireApi.getJobs(user.id)
            setJobs(response.jobs)
        } catch (err: any) {
            setError(err.message || 'Failed to load jobs')
        } finally {
            setIsLoading(false)
        }
    }

    const toggleJob = (jobId: number, remaining: number) => {
        const newSelected = new Map(selectedJobs)
        if (newSelected.has(jobId)) {
            newSelected.delete(jobId)
        } else {
            newSelected.set(jobId, remaining) // Default to all remaining
        }
        setSelectedJobs(newSelected)
    }

    const updateQuantity = (jobId: number, quantity: number) => {
        const newSelected = new Map(selectedJobs)
        newSelected.set(jobId, quantity)
        setSelectedJobs(newSelected)
    }

    const getTotalPositions = () => {
        return Array.from(selectedJobs.values()).reduce((sum, qty) => sum + qty, 0)
    }

    const handleFindCandidates = async () => {
        if (selectedJobs.size === 0) return

        setIsLoading(true)
        setError(null)

        try {
            const jobSelections = Array.from(selectedJobs.entries()).map(([job_id, quantity]) => ({
                job_id,
                quantity
            }))

            const response = await bulkHireApi.initiateMulti(jobSelections)
            setMatchesByJob(response.matches_by_job)

            // Auto-select top N candidates for each job
            const newSelectedCandidates = new Map<number, Set<number>>()
            response.matches_by_job.forEach(jobMatch => {
                const topCandidates = jobMatch.candidates
                    .slice(0, jobMatch.quantity_requested)
                    .map(c => c.id)
                newSelectedCandidates.set(jobMatch.job_id, new Set(topCandidates))
            })
            setSelectedCandidates(newSelectedCandidates)

            setStep('review')
        } catch (err: any) {
            setError(err.message || 'Failed to find candidates')
        } finally {
            setIsLoading(false)
        }
    }

    const toggleCandidate = (jobId: number, candidateId: number) => {
        const newSelected = new Map(selectedCandidates)
        const jobCandidates = newSelected.get(jobId) || new Set()

        if (jobCandidates.has(candidateId)) {
            jobCandidates.delete(candidateId)
        } else {
            // Check if candidate is already selected for another job
            const isSelectedElsewhere = Array.from(newSelected.entries()).some(
                ([otherJobId, candidates]) => otherJobId !== jobId && candidates.has(candidateId)
            )

            if (isSelectedElsewhere) {
                setError('This candidate is already selected for another position')
                setTimeout(() => setError(null), 3000)
                return
            }

            jobCandidates.add(candidateId)
        }

        newSelected.set(jobId, jobCandidates)
        setSelectedCandidates(newSelected)
    }

    const getTotalSelected = () => {
        return Array.from(selectedCandidates.values()).reduce((sum, set) => sum + set.size, 0)
    }

    const isCandidateSelectedElsewhere = (jobId: number, candidateId: number) => {
        return Array.from(selectedCandidates.entries()).some(
            ([otherJobId, candidates]) => otherJobId !== jobId && candidates.has(candidateId)
        )
    }

    const handleConfirm = async () => {
        if (getTotalSelected() === 0) return

        setStep('processing')
        setError(null)

        try {
            const selections: JobEmployeeSelection[] = Array.from(selectedCandidates.entries())
                .filter(([_, employeeIds]) => employeeIds.size > 0)
                .map(([job_id, employeeIds]) => {
                    // Get the job's candidates to find scores
                    const jobMatch = matchesByJob.find(m => m.job_id === job_id)

                    // Map employee IDs to candidates with scores
                    const candidates = Array.from(employeeIds).map(emp_id => {
                        const candidate = jobMatch?.candidates.find(c => c.id === emp_id)
                        return {
                            employee_id: emp_id,
                            score: candidate?.final_score || 0
                        }
                    })

                    return {
                        job_id,
                        candidates
                    }
                })

            const response = await bulkHireApi.confirmMulti(selections)

            setStep('success')

            // Prepare success data
            const resultsByJob = response.results_by_job.map(result => ({
                jobTitle: result.job_title,
                candidates: result.candidates.map(c => {
                    const jobMatch = matchesByJob.find(m => m.job_id === result.job_id)
                    const candidate = jobMatch?.candidates.find(cand => cand.id === c.id)
                    return {
                        ...c,
                        score: candidate?.final_score
                    }
                })
            }))

            // Notify parent after delay
            setTimeout(() => {
                onSuccess({
                    totalHired: response.total_hired,
                    resultsByJob
                })
                handleClose()
            }, 2000)
        } catch (err: any) {
            setError(err.message || 'Failed to send offers')
            setStep('review')
        }
    }

    const handleClose = () => {
        setStep('select')
        setSelectedJobs(new Map())
        setMatchesByJob([])
        setSelectedCandidates(new Map())
        setError(null)
        onClose()
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary-100 rounded-lg">
                            <Users className="w-6 h-6 text-primary-600" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-900">Bulk Hire Candidates</h2>
                            <p className="text-sm text-gray-500">
                                {step === 'select' && 'Select jobs and quantities'}
                                {step === 'review' && 'Review and select candidates'}
                                {step === 'processing' && 'Sending offers...'}
                                {step === 'success' && 'Success!'}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={handleClose}
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                        disabled={step === 'processing'}
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {error && (
                        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="font-medium text-red-900">Error</p>
                                <p className="text-sm text-red-700">{error}</p>
                            </div>
                        </div>
                    )}

                    {/* Step 1: Multi-Job Selection */}
                    {step === 'select' && (
                        <div className="space-y-4">
                            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                <p className="text-sm text-blue-900">
                                    <strong>Select multiple jobs</strong> to hire for different positions in one session
                                </p>
                            </div>

                            <div className="space-y-3">
                                {jobs.map(job => {
                                    const isSelected = selectedJobs.has(job.id)
                                    const quantity = selectedJobs.get(job.id) || job.remaining

                                    return (
                                        <div
                                            key={job.id}
                                            className={`p-4 border-2 rounded-lg transition-all ${isSelected ? 'border-primary-500 bg-primary-50' : 'border-gray-200'
                                                }`}
                                        >
                                            <div className="flex items-start gap-3">
                                                <input
                                                    type="checkbox"
                                                    checked={isSelected}
                                                    onChange={() => toggleJob(job.id, job.remaining)}
                                                    className="mt-1"
                                                />
                                                <div className="flex-1">
                                                    <h3 className="font-semibold text-gray-900">{job.title}</h3>
                                                    <p className="text-sm text-gray-600">
                                                        {job.location} • {job.shift_type} • {job.cuisine_type}
                                                    </p>
                                                    <p className="text-sm text-gray-500 mt-1">
                                                        {job.remaining} positions remaining
                                                    </p>
                                                </div>
                                                {isSelected && (
                                                    <div className="flex items-center gap-2">
                                                        <label className="text-sm font-medium text-gray-700">Quantity:</label>
                                                        <input
                                                            type="number"
                                                            min={1}
                                                            max={job.remaining}
                                                            value={quantity}
                                                            onChange={(e) => updateQuantity(job.id, parseInt(e.target.value) || 1)}
                                                            className="w-20 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                                                            onClick={(e) => e.stopPropagation()}
                                                        />
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>

                            {selectedJobs.size > 0 && (
                                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                                    <p className="text-sm text-green-900">
                                        <strong>✅ {selectedJobs.size} jobs selected</strong> • Total: {getTotalPositions()} positions
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Step 2: Grouped Candidate Review */}
                    {step === 'review' && (
                        <div className="space-y-6">
                            {matchesByJob.map(jobMatch => {
                                const selectedForJob = selectedCandidates.get(jobMatch.job_id) || new Set()

                                return (
                                    <div key={jobMatch.job_id} className="border border-gray-200 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
                                            <div>
                                                <h3 className="font-bold text-gray-900 text-lg">{jobMatch.job_title}</h3>
                                                <p className="text-sm text-gray-600">
                                                    {jobMatch.quantity_requested} positions • {jobMatch.candidates.length} candidates found
                                                </p>
                                            </div>
                                            <div className="text-sm">
                                                <span className="font-medium text-primary-600">{selectedForJob.size} selected</span>
                                                <span className="text-gray-500"> of {jobMatch.candidates.length}</span>
                                            </div>
                                        </div>

                                        <div className="space-y-2 max-h-64 overflow-y-auto">
                                            {jobMatch.candidates.map(candidate => {
                                                const isSelectedElsewhere = isCandidateSelectedElsewhere(jobMatch.job_id, candidate.id)
                                                const isDisabled = isSelectedElsewhere

                                                return (
                                                    <div
                                                        key={candidate.id}
                                                        className={`p-3 border rounded-lg transition-all ${isDisabled
                                                            ? 'border-gray-200 bg-gray-100 opacity-50 cursor-not-allowed'
                                                            : selectedForJob.has(candidate.id)
                                                                ? 'border-primary-500 bg-primary-50 cursor-pointer'
                                                                : 'border-gray-200 hover:border-gray-300 cursor-pointer'
                                                            }`}
                                                        onClick={() => !isDisabled && toggleCandidate(jobMatch.job_id, candidate.id)}
                                                    >
                                                        <div className="flex items-start gap-3">
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedForJob.has(candidate.id)}
                                                                disabled={isDisabled}
                                                                onChange={() => !isDisabled && toggleCandidate(jobMatch.job_id, candidate.id)}
                                                                className="mt-1"
                                                            />
                                                            <div className="flex-1">
                                                                <div className="flex items-center justify-between">
                                                                    <div>
                                                                        <h4 className="font-semibold text-gray-900">{candidate.name}</h4>
                                                                        {isSelectedElsewhere && (
                                                                            <span className="text-xs text-orange-600 font-medium">Already selected for another job</span>
                                                                        )}
                                                                    </div>
                                                                    <span className="font-bold text-primary-600">{candidate.final_score}/100</span>
                                                                </div>
                                                                <p className="text-sm text-gray-600">
                                                                    {candidate.experience_years} years • {candidate.skills.slice(0, 3).join(', ')}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )
                                            })}
                                        </div>
                                    </div>
                                )
                            })}

                            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                <p className="text-sm text-blue-900">
                                    <strong>✅ Total Selected: {getTotalSelected()} candidates</strong> across {matchesByJob.length} jobs
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Processing */}
                    {step === 'processing' && (
                        <div className="flex flex-col items-center justify-center py-12">
                            <Loader2 className="w-16 h-16 text-primary-600 animate-spin mb-4" />
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">Sending Offers...</h3>
                            <p className="text-sm text-gray-600">Generating documents and notifying candidates</p>
                        </div>
                    )}

                    {/* Step 4: Success */}
                    {step === 'success' && (
                        <div className="flex flex-col items-center justify-center py-12">
                            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                                <CheckCircle2 className="w-10 h-10 text-green-600" />
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">Offers Sent Successfully!</h3>
                            <p className="text-sm text-gray-600">All candidates have been notified</p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between p-6 border-t border-gray-200">
                    {step === 'select' && (
                        <>
                            <button
                                onClick={handleClose}
                                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                                disabled={isLoading}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleFindCandidates}
                                disabled={selectedJobs.size === 0 || isLoading}
                                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Loading...
                                    </>
                                ) : (
                                    <>
                                        Find Candidates for {selectedJobs.size} Jobs →
                                    </>
                                )}
                            </button>
                        </>
                    )}

                    {step === 'review' && (
                        <>
                            <button
                                onClick={() => setStep('select')}
                                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                ← Back
                            </button>
                            <button
                                onClick={handleConfirm}
                                disabled={getTotalSelected() === 0}
                                className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                Send Offers to {getTotalSelected()} Candidates
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
