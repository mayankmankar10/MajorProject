import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { User, Mail, Phone, MapPin, Briefcase, GraduationCap, Award, Save } from 'lucide-react'
import { Input, Button, Card, Badge } from '@/components'

export const Profile: React.FC = () => {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    name: 'John Doe',
    email: 'john.doe@example.com',
    phone: '+1 (555) 123-4567',
    location: 'San Francisco, CA',
    title: 'Senior Frontend Developer',
    bio: 'Passionate developer with 5+ years of experience in building modern web applications.',
    experience: '5+ years',
    education: 'BS Computer Science',
    skills: ['React', 'TypeScript', 'Node.js', 'Tailwind CSS', 'GraphQL']
  })

  const handleSave = () => {
    console.log('Saving profile:', formData)
    setIsEditing(false)
    // TODO: Implement save logic
  }

  return (
    <div>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 flex justify-between items-center"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My Profile</h1>
          <p className="text-gray-600">Manage your personal information and preferences</p>
        </div>
        {!isEditing && (
          <Button variant="primary" size="md" onClick={() => setIsEditing(true)}>
            Edit Profile
          </Button>
        )}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Profile Card */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-1"
        >
          <Card padding="lg">
            <div className="text-center">
              <div className="w-24 h-24 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-3xl mx-auto mb-4">
                {formData.name.split(' ').map(n => n[0]).join('')}
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-1">{formData.name}</h2>
              <p className="text-gray-600 mb-4">{formData.title}</p>
              <Badge variant="success" dot>Active</Badge>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-200 space-y-3">
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <Mail className="w-4 h-4" />
                <span>{formData.email}</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <Phone className="w-4 h-4" />
                <span>{formData.phone}</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <MapPin className="w- 4 h-4" />
                <span>{formData.location}</span>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="text-sm font-medium text-gray-700 mb-2">Profile Completion</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: '85%' }}></div>
              </div>
              <div className="text-xs text-gray-500">85% Complete</div>
            </div>
          </Card>
        </motion.div>

        {/* Right Column - Details */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2 space-y-6"
        >
          {/* Basic Information */}
          <Card padding="lg">
            <Card.Header title="Basic Information" />
            <Card.Body>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Full Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  disabled={!isEditing}
                  leftIcon={<User className="w-5 h-5" />}
                />
                <Input
                  label="Email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={!isEditing}
                  leftIcon={<Mail className="w-5 h-5" />}
                />
                <Input
                  label="Phone"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  disabled={!isEditing}
                  leftIcon={<Phone className="w-5 h-5" />}
                />
                <Input
                  label="Location"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  disabled={!isEditing}
                  leftIcon={<MapPin className="w-5 h-5" />}
                />
              </div>
              <div className="mt-4">
                <Input
                  label="Job Title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  disabled={!isEditing}
                  leftIcon={<Briefcase className="w-5 h-5" />}
                />
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Bio</label>
                <textarea
                  value={formData.bio}
                  onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                  disabled={!isEditing}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                />
              </div>
            </Card.Body>
          </Card>

          {/* Professional Details */}
          <Card padding="lg">
            <Card.Header title="Professional Details" />
            <Card.Body>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Experience"
                  value={formData.experience}
                  onChange={(e) => setFormData({ ...formData, experience: e.target.value })}
                  disabled={!isEditing}
                  leftIcon={<Briefcase className="w-5 h-5" />}
                />
                <Input
                  label="Education"
                  value={formData.education}
                  onChange={(e) => setFormData({ ...formData, education: e.target.value })}
                  disabled={!isEditing}
                  leftIcon={<GraduationCap className="w-5 h-5" />}
                />
              </div>
            </Card.Body>
          </Card>

          {/* Skills */}
          <Card padding="lg">
            <Card.Header title="Skills" />
            <Card.Body>
              <div className="flex flex-wrap gap-2">
                {formData.skills.map((skill, idx) => (
                  <Badge key={idx} variant="primary">
                    {skill}
                  </Badge>
                ))}
                {isEditing && (
                  <Button variant="ghost" size="sm">
                    + Add Skill
                  </Button>
                )}
              </div>
            </Card.Body>
          </Card>

          {/* AI Resume Generation */}
          <Card padding="lg" className="bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200">
            <Card.Header
              title="🤖 AI-Generated Resume"
              subtitle="Let AI create a professional resume from your profile"
            />
            <Card.Body>
              <div className="space-y-4">
                <p className="text-sm text-gray-700">
                  Our AI will automatically generate a restaurant-industry optimized resume based on your profile information, certifications, and experience.
                </p>

                <div className="flex gap-3">
                  <Button
                    variant="primary"
                    size="md"
                    onClick={() => {
                      console.log('Generate resume clicked')
                      // TODO: Implement resume generation
                    }}
                  >
                    Generate Resume
                  </Button>

                  <Button
                    variant="outline"
                    size="md"
                    onClick={() => {
                      console.log('View resume clicked')
                      // TODO: Implement resume viewing
                    }}
                  >
                    View Resume
                  </Button>

                  <Button
                    variant="ghost"
                    size="md"
                    onClick={() => {
                      console.log('Download PDF clicked')
                      // TODO: Implement PDF download
                    }}
                  >
                    Download PDF
                  </Button>
                </div>

                <div className="mt-4 p-3 bg-white rounded-lg border border-blue-200">
                  <div className="flex items-start gap-2">
                    <Award className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="text-xs text-gray-600">
                      <strong>Pro Tip:</strong> Keep your profile updated for the best resume quality. The AI highlights your certifications, cuisine experience, and shift preferences automatically.
                    </div>
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>

          {/* Action Buttons */}
          {isEditing && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-4"
            >
              <Button
                variant="primary"
                size="lg"
                fullWidth
                onClick={handleSave}
                leftIcon={<Save className="w-5 h-5" />}
              >
                Save Changes
              </Button>
              <Button
                variant="outline"
                size="lg"
                onClick={() => setIsEditing(false)}
              >
                Cancel
              </Button>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
