// Authentication
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  role: 'employer' | 'employee';
  full_name?: string;
  company_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface User {
  id: number;                    // user_id for authentication
  email: string;
  role: 'employer' | 'employee';
  profileId?: number;             // employee_id or employer_id for role-specific operations
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

// Jobs
export interface Job {
  id: number;
  employer_id: number;
  title: string;
  description: string;
  enhanced_description?: string;
  requirements: Record<string, any>;
  location: string;
  job_type: 'full_time' | 'part_time' | 'contract';
  salary_range: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface JobPostRequest {
  title: string;
  description: string;
  location: string;
  job_type: 'full_time' | 'part_time' | 'contract';
  salary_range: string;
  requirements: {
    skills: string[];
    experience: number;
    certifications?: string[];
  };
}

// Applications
export interface Application {
  id: number;
  job_id: number;
  employee_id: number;
  status: 'applied' | 'reviewing' | 'interview_scheduled' | 'selected' | 'rejected' | 'hired';
  match_score: number;
  cover_letter: string;
  applied_at: string;
  reviewed_at: string | null;
  notes: string;
  job?: Job;
}

export interface ApplicationCreateRequest {
  job_id: number;
  cover_letter?: string;
}

// Interviews
export interface Interview {
  id: number;
  application_id: number;
  scheduled_at: string;
  duration_minutes: number;
  location: string;
  meeting_link: string;
  calendar_link: string;
  status: 'scheduled' | 'confirmed' | 'completed' | 'cancelled';
  interviewer_notes: string;
  feedback: string;
  created_at: string;
  updated_at: string;
}

export interface InterviewCreateRequest {
  application_id: number;
  scheduled_at: string;
  duration_minutes?: number;
  meeting_link?: string;
}

// Employees
export interface Employee {
  id: number;
  user_id: number;
  full_name: string;
  phone: string;
  resume_text: string;
  resume_filename: string;
  skills: string[];
  experience_years: number;
  certifications: Certification[];
  education: Education[];
  preferred_location: string;
  availability: 'immediate' | '2_weeks' | '1_month';
  created_at: string;
}

export interface Certification {
  name: string;
  issuer: string;
  issued_date?: string;
  expiry_date?: string;
}

export interface Education {
  school: string;
  degree: string;
  field_of_study: string;
  start_date?: string;
  end_date?: string;
}

// Employers
export interface Employer {
  id: number;
  user_id: number;
  company_name: string;
  company_profile: string;
  industry: string;
  location: string;
  website: string;
  verification_status: 'pending' | 'verified' | 'rejected';
  created_at: string;
}

// Notifications
export interface Notification {
  id: number;
  recipient_id: number;
  title: string;
  message: string;
  notification_type: 'job_match' | 'interview' | 'application' | 'onboarding';
  action_url: string;
  metadata: Record<string, any>;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
}

// Chat
export interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatSession {
  session_id: string;
  messages: ChatMessage[];
}

// Analytics
export interface DashboardMetrics {
  total_jobs?: number;
  active_applications?: number;
  scheduled_interviews?: number;
  recent_activity?: Activity[];
  profile_completeness?: number;
  match_scores?: MatchScore[];
}

export interface Activity {
  id: number;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  action_url?: string;
}

export interface MatchScore {
  id: number;
  title: string;
  score: number;
  timestamp: string;
}

// Tools
export interface Tool {
  name: string;
  description: string;
  parameters?: Record<string, any>;
}

export interface ToolInvokeRequest {
  tool_name: string;
  parameters: Record<string, any>;
}

// Onboarding
export interface OnboardingTask {
  id: number;
  employee_id: number;
  job_id: number;
  task_type: 'offer_letter' | 'nda' | 'checklist' | 'document_upload';
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
  document_url: string;
  document_content: string;
  deadline: string;
  completed_at: string | null;
  created_at: string;
}
