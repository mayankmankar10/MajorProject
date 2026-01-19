import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Gift,
    CheckCircle2,
    XCircle,
    Star,
    Building2,
    MapPin,
    DollarSign,
    Calendar,
    FileText,
    Clock,
    Briefcase,
    Loader,
    PartyPopper,
    Shield,
    Eye,
    Download,
    X
} from 'lucide-react'
import { Card, Badge, Button } from '@/components'
import { apiClient } from '@/services/api'
import { Link } from 'react-router-dom'
import confetti from 'canvas-confetti'
import jsPDF from 'jspdf'

interface Offer {
    id: number
    application_id: number
    job_id: number
    job_title: string
    company_name: string
    location: string | null
    salary_offered: string | null
    start_date: string | null
    status: string
    offer_letter_preview: string | null
    nda_preview: string | null
    sent_at: string
    expires_at: string | null
    offer_signed: boolean
    nda_signed: boolean
    match_score: number | null
}

interface OfferDetails {
    id: number
    job: {
        id: number
        title: string
        description: string
        location: string
        job_type: string
        shift_type: string
    }
    employer: {
        company_name: string
        industry: string
    }
    offer_details: {
        salary_offered: string
        start_date: string
        additional_terms: any
    }
    documents: {
        offer_letter: string
        nda: string
    }
    status: string
    match_score: number
}

// Helper function to normalize match scores (handles both 0-1 and 0-100 formats)
const normalizeScore = (score: number | null | undefined): number => {
    if (!score) return 0
    // If score is less than 1, it's in decimal format (0.85), multiply by 100
    // If score is >= 1, it's already in percentage format (85)
    return score < 1 ? score * 100 : score
}

export const Offers: React.FC = () => {
    const [offers, setOffers] = useState<Offer[]>([])
    const [loading, setLoading] = useState(true)
    const [selectedOffer, setSelectedOffer] = useState<Offer | null>(null)
    const [offerDetails, setOfferDetails] = useState<OfferDetails | null>(null)
    const [loadingDetails, setLoadingDetails] = useState(false)
    const [actionLoading, setActionLoading] = useState<string | null>(null)
    const [showSuccess, setShowSuccess] = useState(false)
    const [acceptedJob, setAcceptedJob] = useState<string>('')
    const [viewingDocument, setViewingDocument] = useState<{ type: 'offer' | 'nda', content: string } | null>(null)

    useEffect(() => {
        loadOffers()
    }, [])

    const loadOffers = async () => {
        try {
            setLoading(true)
            const data = await apiClient.getOffers()
            setOffers(data || [])
        } catch (error) {
            console.error('Failed to load offers:', error)
            setOffers([])
        } finally {
            setLoading(false)
        }
    }

    const loadOfferDetails = async (offerId: number) => {
        try {
            setLoadingDetails(true)
            const data = await apiClient.getOfferDetails(offerId)
            setOfferDetails(data)
        } catch (error) {
            console.error('Failed to load offer details:', error)
        } finally {
            setLoadingDetails(false)
        }
    }

    const handleAcceptOffer = async (offerId: number, jobTitle: string) => {
        try {
            setActionLoading('accept')
            await apiClient.acceptOffer(offerId, {
                sign_offer: true,
                sign_nda: true,
                confirm_start_date: true
            })

            // Trigger confetti
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 }
            })

            setAcceptedJob(jobTitle)
            setShowSuccess(true)
            setSelectedOffer(null)
            setOfferDetails(null)

            // Reload offers
            await loadOffers()
        } catch (error) {
            console.error('Failed to accept offer:', error)
            alert('Failed to accept offer. Please try again.')
        } finally {
            setActionLoading(null)
        }
    }

    const handleDeclineOffer = async (offerId: number) => {
        if (!confirm('Are you sure you want to decline this offer?')) return

        try {
            setActionLoading('decline')
            await apiClient.declineOffer(offerId, {
                reason: 'Declined via web interface'
            })

            setSelectedOffer(null)
            setOfferDetails(null)
            await loadOffers()
        } catch (error) {
            console.error('Failed to decline offer:', error)
            alert('Failed to decline offer. Please try again.')
        } finally {
            setActionLoading(null)
        }
    }

    const pendingOffers = offers.filter(o => o.status === 'pending')
    const respondedOffers = offers.filter(o => o.status !== 'pending')

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading your offers...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="max-w-4xl mx-auto">
            {/* Success Modal */}
            <AnimatePresence>
                {showSuccess && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
                        onClick={() => setShowSuccess(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.8, opacity: 0 }}
                            className="bg-white rounded-2xl p-8 max-w-md mx-4 text-center"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                                <PartyPopper className="w-10 h-10 text-green-600" />
                            </div>
                            <h2 className="text-2xl font-bold text-gray-900 mb-2">
                                Congratulations! 🎉
                            </h2>
                            <p className="text-gray-600 mb-6">
                                You've accepted the <strong>{acceptedJob}</strong> offer! Your documents have been signed and your onboarding has begun.
                            </p>
                            <div className="space-y-3">
                                <Link to="/employee/dashboard">
                                    <Button variant="primary" size="lg" className="w-full">
                                        Go to Dashboard
                                    </Button>
                                </Link>
                                <Button
                                    variant="outline"
                                    size="md"
                                    className="w-full"
                                    onClick={() => setShowSuccess(false)}
                                >
                                    View Other Offers
                                </Button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8"
            >
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Job Offers</h1>
                <p className="text-gray-600">Review and respond to job offers from employers</p>
            </motion.div>

            {/* Stats */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="grid grid-cols-3 gap-4 mb-8"
            >
                <Card padding="md" className="text-center bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200">
                    <div className="text-3xl font-bold text-yellow-600">{pendingOffers.length}</div>
                    <div className="text-sm text-gray-600">Pending</div>
                </Card>
                <Card padding="md" className="text-center bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
                    <div className="text-3xl font-bold text-green-600">
                        {offers.filter(o => o.status === 'accepted').length}
                    </div>
                    <div className="text-sm text-gray-600">Accepted</div>
                </Card>
                <Card padding="md" className="text-center bg-gradient-to-br from-gray-50 to-slate-50 border-gray-200">
                    <div className="text-3xl font-bold text-gray-600">
                        {offers.filter(o => o.status === 'declined').length}
                    </div>
                    <div className="text-sm text-gray-600">Declined</div>
                </Card>
            </motion.div>

            {/* Pending Offers */}
            {pendingOffers.length > 0 && (
                <div className="mb-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <Gift className="w-5 h-5 text-yellow-600" />
                        Pending Offers
                    </h2>
                    <div className="space-y-4">
                        {pendingOffers.map((offer, idx) => (
                            <motion.div
                                key={offer.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 + idx * 0.1 }}
                            >
                                <Card
                                    padding="lg"
                                    hover
                                    className="cursor-pointer border-2 border-yellow-200 bg-gradient-to-r from-yellow-50/50 to-white"
                                    onClick={() => {
                                        setSelectedOffer(offer)
                                        loadOfferDetails(offer.id)
                                    }}
                                >
                                    <div className="flex items-start gap-4">
                                        <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-yellow-100 flex items-center justify-center">
                                            <Gift className="w-7 h-7 text-yellow-600" />
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between mb-2">
                                                <div>
                                                    <h3 className="text-lg font-semibold text-gray-900">{offer.job_title}</h3>
                                                    <div className="flex items-center gap-3 text-sm text-gray-600">
                                                        <span className="flex items-center gap-1">
                                                            <Building2 className="w-4 h-4" />
                                                            {offer.company_name}
                                                        </span>
                                                        {offer.location && (
                                                            <span className="flex items-center gap-1">
                                                                <MapPin className="w-4 h-4" />
                                                                {offer.location}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                                <Badge variant="warning" className="flex items-center gap-1">
                                                    <Clock className="w-3 h-3" />
                                                    Pending Response
                                                </Badge>
                                            </div>

                                            <div className="flex items-center gap-4 mb-3">
                                                {offer.salary_offered && (
                                                    <div className="flex items-center gap-1 text-sm text-gray-700">
                                                        <DollarSign className="w-4 h-4 text-green-600" />
                                                        {offer.salary_offered}
                                                    </div>
                                                )}
                                                {offer.match_score && (
                                                    <div className="flex items-center gap-1 text-sm">
                                                        <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                                                        <span className="font-semibold">{Math.round(normalizeScore(offer.match_score))}% Match</span>
                                                    </div>
                                                )}
                                                <div className="flex items-center gap-1 text-sm text-gray-500">
                                                    <Calendar className="w-4 h-4" />
                                                    Received {new Date(offer.sent_at).toLocaleDateString()}
                                                </div>
                                            </div>

                                            <div className="flex gap-2">
                                                <Button
                                                    variant="primary"
                                                    size="sm"
                                                    onClick={(e) => {
                                                        e.stopPropagation()
                                                        setSelectedOffer(offer)
                                                        loadOfferDetails(offer.id)
                                                    }}
                                                >
                                                    Review Offer
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                </Card>
                            </motion.div>
                        ))}
                    </div>
                </div>
            )}

            {/* Empty State */}
            {pendingOffers.length === 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <Card padding="lg" className="text-center">
                        <Gift className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Pending Offers</h3>
                        <p className="text-gray-600 mb-6">
                            You'll see new job offers here when employers select you for positions.
                        </p>
                        <Link to="/employee/jobs">
                            <Button variant="primary" size="md">
                                <Briefcase className="w-4 h-4 mr-2" />
                                Browse Jobs
                            </Button>
                        </Link>
                    </Card>
                </motion.div>
            )}

            {/* Past Offers */}
            {respondedOffers.length > 0 && (
                <div className="mt-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Past Offers</h2>
                    <div className="space-y-3">
                        {respondedOffers.map((offer) => (
                            <Card
                                key={offer.id}
                                padding="md"
                                hover
                                className="cursor-pointer"
                                onClick={() => {
                                    setSelectedOffer(offer)
                                    loadOfferDetails(offer.id)
                                }}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${offer.status === 'accepted' ? 'bg-green-100' : 'bg-gray-100'
                                            }`}>
                                            {offer.status === 'accepted' ? (
                                                <CheckCircle2 className="w-5 h-5 text-green-600" />
                                            ) : (
                                                <XCircle className="w-5 h-5 text-gray-400" />
                                            )}
                                        </div>
                                        <div>
                                            <h4 className="font-medium text-gray-900">{offer.job_title}</h4>
                                            <p className="text-sm text-gray-500">{offer.company_name}</p>
                                        </div>
                                    </div>
                                    <Badge variant={offer.status === 'accepted' ? 'success' : 'default'}>
                                        {offer.status === 'accepted' ? 'Accepted' : 'Declined'}
                                    </Badge>
                                </div>
                            </Card>
                        ))}
                    </div>
                </div>
            )}

            {/* Offer Details Modal */}
            <AnimatePresence>
                {selectedOffer && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
                        onClick={() => {
                            setSelectedOffer(null)
                            setOfferDetails(null)
                        }}
                    >
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {loadingDetails ? (
                                <div className="p-8 text-center">
                                    <Loader className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" />
                                    <p className="text-gray-600">Loading offer details...</p>
                                </div>
                            ) : (
                                <div className="p-6">
                                    {/* Header */}
                                    <div className="flex items-start justify-between mb-6">
                                        <div>
                                            <h2 className="text-2xl font-bold text-gray-900 mb-1">
                                                {selectedOffer.job_title}
                                            </h2>
                                            <p className="text-gray-600">{selectedOffer.company_name}</p>
                                        </div>
                                        {selectedOffer.match_score && (
                                            <div className="text-center">
                                                <div className="text-3xl font-bold text-primary-600">
                                                    {Math.round(normalizeScore(selectedOffer.match_score))}%
                                                </div>
                                                <div className="text-xs text-gray-500">Match Score</div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Job Description - only if offerDetails loaded */}
                                    {offerDetails?.job?.description && (
                                        <div className="mb-6">
                                            <h3 className="font-semibold text-gray-900 mb-2">Job Description</h3>
                                            <p className="text-gray-600 text-sm leading-relaxed">
                                                {offerDetails.job.description}
                                            </p>
                                        </div>
                                    )}

                                    {/* Offer Details */}
                                    <div className="grid grid-cols-2 gap-4 mb-6">
                                        {selectedOffer.salary_offered && (
                                            <div className="p-4 bg-green-50 rounded-lg">
                                                <div className="flex items-center gap-2 text-green-600 mb-1">
                                                    <DollarSign className="w-4 h-4" />
                                                    <span className="text-sm font-medium">Salary</span>
                                                </div>
                                                <div className="text-lg font-semibold text-gray-900">
                                                    {selectedOffer.salary_offered}
                                                </div>
                                            </div>
                                        )}
                                        {selectedOffer.location && (
                                            <div className="p-4 bg-blue-50 rounded-lg">
                                                <div className="flex items-center gap-2 text-blue-600 mb-1">
                                                    <MapPin className="w-4 h-4" />
                                                    <span className="text-sm font-medium">Location</span>
                                                </div>
                                                <div className="text-lg font-semibold text-gray-900">
                                                    {selectedOffer.location}
                                                </div>
                                            </div>
                                        )}
                                        {offerDetails?.job?.job_type && (
                                            <div className="p-4 bg-purple-50 rounded-lg">
                                                <div className="flex items-center gap-2 text-purple-600 mb-1">
                                                    <Briefcase className="w-4 h-4" />
                                                    <span className="text-sm font-medium">Job Type</span>
                                                </div>
                                                <div className="text-lg font-semibold text-gray-900 capitalize">
                                                    {offerDetails.job.job_type}
                                                </div>
                                            </div>
                                        )}
                                        {offerDetails?.job?.shift_type && (
                                            <div className="p-4 bg-orange-50 rounded-lg">
                                                <div className="flex items-center gap-2 text-orange-600 mb-1">
                                                    <Clock className="w-4 h-4" />
                                                    <span className="text-sm font-medium">Shift</span>
                                                </div>
                                                <div className="text-lg font-semibold text-gray-900 capitalize">
                                                    {offerDetails.job.shift_type}
                                                </div>
                                            </div>
                                        )}
                                        {offerDetails?.employer?.industry && (
                                            <div className="p-4 bg-indigo-50 rounded-lg">
                                                <div className="flex items-center gap-2 text-indigo-600 mb-1">
                                                    <Building2 className="w-4 h-4" />
                                                    <span className="text-sm font-medium">Industry</span>
                                                </div>
                                                <div className="text-lg font-semibold text-gray-900">
                                                    {offerDetails.employer.industry}
                                                </div>
                                            </div>
                                        )}
                                        {selectedOffer.start_date && (
                                            <div className="p-4 bg-teal-50 rounded-lg">
                                                <div className="flex items-center gap-2 text-teal-600 mb-1">
                                                    <Calendar className="w-4 h-4" />
                                                    <span className="text-sm font-medium">Start Date</span>
                                                </div>
                                                <div className="text-lg font-semibold text-gray-900">
                                                    {new Date(selectedOffer.start_date).toLocaleDateString()}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Documents Section */}
                                    <div className="mb-6">
                                        <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                            <FileText className="w-5 h-5 text-gray-400" />
                                            Documents to Sign
                                        </h3>
                                        <div className="space-y-3">
                                            <div className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-3 flex-1">
                                                        <FileText className="w-5 h-5 text-primary-600" />
                                                        <div className="flex-1">
                                                            <div className="font-medium text-gray-900">Offer Letter</div>
                                                            <div className="text-sm text-gray-500">Employment terms and conditions</div>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        {offerDetails?.documents?.offer_letter && (
                                                            <button
                                                                onClick={() => setViewingDocument({
                                                                    type: 'offer',
                                                                    content: offerDetails.documents.offer_letter
                                                                })}
                                                                className="px-3 py-1.5 text-sm font-medium text-primary-600 hover:bg-primary-50 rounded-lg transition-colors flex items-center gap-1"
                                                            >
                                                                <Eye className="w-4 h-4" />
                                                                View
                                                            </button>
                                                        )}
                                                        <Badge variant={selectedOffer.offer_signed ? 'success' : 'warning'}>
                                                            {selectedOffer.offer_signed ? 'Signed' : 'Pending'}
                                                        </Badge>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="p-4 border border-gray-200 rounded-lg hover:border-purple-300 transition-colors">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-3 flex-1">
                                                        <Shield className="w-5 h-5 text-purple-600" />
                                                        <div className="flex-1">
                                                            <div className="font-medium text-gray-900">NDA</div>
                                                            <div className="text-sm text-gray-500">Non-Disclosure Agreement</div>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        {offerDetails?.documents?.nda && (
                                                            <button
                                                                onClick={() => setViewingDocument({
                                                                    type: 'nda',
                                                                    content: offerDetails.documents.nda
                                                                })}
                                                                className="px-3 py-1.5 text-sm font-medium text-purple-600 hover:bg-purple-50 rounded-lg transition-colors flex items-center gap-1"
                                                            >
                                                                <Eye className="w-4 h-4" />
                                                                View
                                                            </button>
                                                        )}
                                                        <Badge variant={selectedOffer.nda_signed ? 'success' : 'warning'}>
                                                            {selectedOffer.nda_signed ? 'Signed' : 'Pending'}
                                                        </Badge>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Agreement Checkbox and Action Buttons - Only for pending offers */}
                                    {selectedOffer.status === 'pending' && (
                                        <>
                                            {/* Agreement Checkbox */}
                                            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                                                <label className="flex items-start gap-3 cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        className="mt-1 w-5 h-5 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
                                                        defaultChecked
                                                    />
                                                    <span className="text-sm text-gray-700">
                                                        By accepting this offer, I agree to the terms in the Offer Letter and NDA.
                                                        I understand this constitutes a binding agreement.
                                                    </span>
                                                </label>
                                            </div>

                                            {/* Action Buttons */}
                                            <div className="flex gap-3">
                                                <Button
                                                    variant="primary"
                                                    size="lg"
                                                    className="flex-1"
                                                    isLoading={actionLoading === 'accept'}
                                                    disabled={actionLoading !== null}
                                                    onClick={() => handleAcceptOffer(selectedOffer.id, selectedOffer.job_title)}
                                                >
                                                    <CheckCircle2 className="w-5 h-5 mr-2" />
                                                    Accept Offer
                                                </Button>
                                                <Button
                                                    variant="outline"
                                                    size="lg"
                                                    isLoading={actionLoading === 'decline'}
                                                    disabled={actionLoading !== null}
                                                    onClick={() => handleDeclineOffer(selectedOffer.id)}
                                                >
                                                    <XCircle className="w-5 h-5 mr-2" />
                                                    Decline
                                                </Button>
                                            </div>
                                        </>
                                    )}

                                    {/* Status Badge for accepted/declined offers */}
                                    {selectedOffer.status !== 'pending' && (
                                        <div className="p-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border-2 border-green-200">
                                            <div className="flex items-center justify-center gap-3">
                                                <CheckCircle2 className="w-8 h-8 text-green-600" />
                                                <div>
                                                    <h3 className="text-xl font-bold text-green-900">
                                                        {selectedOffer.status === 'accepted' ? 'Offer Accepted!' : 'Offer Declined'}
                                                    </h3>
                                                    <p className="text-sm text-green-700 mt-1">
                                                        {selectedOffer.status === 'accepted'
                                                            ? `You accepted this offer. Your start date is ${selectedOffer.start_date ? new Date(selectedOffer.start_date.split(' ')[0] + 'T00:00:00').toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : 'TBD'}.`
                                                            : 'You have declined this offer.'}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Document Viewer Modal */}
            <AnimatePresence>
                {viewingDocument && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
                        onClick={() => setViewingDocument(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {/* Header */}
                            <div className="p-6 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-primary-50 to-white">
                                <div className="flex items-center gap-3">
                                    {viewingDocument.type === 'offer' ? (
                                        <FileText className="w-6 h-6 text-primary-600" />
                                    ) : (
                                        <Shield className="w-6 h-6 text-purple-600" />
                                    )}
                                    <h2 className="text-2xl font-bold text-gray-900">
                                        {viewingDocument.type === 'offer' ? 'Offer Letter' : 'Non-Disclosure Agreement'}
                                    </h2>
                                </div>
                                <button
                                    onClick={() => setViewingDocument(null)}
                                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                >
                                    <X className="w-6 h-6 text-gray-500" />
                                </button>
                            </div>

                            {/* Document Content */}
                            <div className="flex-1 overflow-y-auto p-6">
                                <div className="prose max-w-none">
                                    <pre className="whitespace-pre-wrap font-sans text-gray-700 leading-relaxed">
                                        {viewingDocument.content}
                                    </pre>
                                </div>
                            </div>

                            {/* Footer */}
                            <div className="p-6 border-t border-gray-200 bg-gray-50 flex gap-3">
                                <Button
                                    variant="outline"
                                    size="md"
                                    onClick={() => {
                                        const doc = new jsPDF()
                                        const pageWidth = doc.internal.pageSize.getWidth()
                                        const pageHeight = doc.internal.pageSize.getHeight()
                                        const margin = 20
                                        const maxWidth = pageWidth - 2 * margin

                                        // Title
                                        doc.setFontSize(18)
                                        doc.setFont('helvetica', 'bold')
                                        const title = viewingDocument.type === 'offer' ? 'OFFER LETTER' : 'NON-DISCLOSURE AGREEMENT'
                                        doc.text(title, pageWidth / 2, margin, { align: 'center' })

                                        // Company info
                                        doc.setFontSize(10)
                                        doc.setFont('helvetica', 'normal')
                                        doc.text(`${selectedOffer?.company_name || ''}`, pageWidth / 2, margin + 10, { align: 'center' })
                                        doc.text(`Date: ${new Date().toLocaleDateString()}`, pageWidth / 2, margin + 16, { align: 'center' })

                                        // Content
                                        doc.setFontSize(11)
                                        const lines = doc.splitTextToSize(viewingDocument.content, maxWidth)

                                        let yPosition = margin + 30
                                        lines.forEach((line: string) => {
                                            if (yPosition > pageHeight - margin) {
                                                doc.addPage()
                                                yPosition = margin
                                            }
                                            doc.text(line, margin, yPosition)
                                            yPosition += 6
                                        })

                                        // Save
                                        const fileName = `${viewingDocument.type === 'offer' ? 'Offer_Letter' : 'NDA'}_${selectedOffer?.job_title.replace(/\s+/g, '_')}.pdf`
                                        doc.save(fileName)
                                    }}
                                    className="flex items-center gap-2"
                                >
                                    <Download className="w-4 h-4" />
                                    Download PDF
                                </Button>
                                <Button
                                    variant="primary"
                                    size="md"
                                    onClick={() => setViewingDocument(null)}
                                    className="flex-1"
                                >
                                    Close
                                </Button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
