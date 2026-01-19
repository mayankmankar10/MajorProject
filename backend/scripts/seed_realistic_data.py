# backend/scripts/seed_realistic_data.py
"""
Realistic Data Seeder for SmartServe Platform
Seeds the database with production-quality, realistic data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from backend.db.sql_db import SessionLocal, engine
from backend.db.models import (
    Base, User, Employer, Employee, Job, Application, 
    ApplicationStatus, UserRole, JobCategory, RestaurantRole
)
from backend.utils.auth import get_password_hash
from datetime import datetime, timedelta
import random

class RealisticDataSeeder:
    """Seed database with realistic, production-quality data."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.created_users = []
        self.created_employers = []
        self.created_employees = []
        self.created_jobs = []
        self.created_applications = []
    
    def clear_all_data(self):
        """Clear all existing data (USE WITH CAUTION!)."""
        print("\n⚠️  WARNING: This will delete ALL data from the database!")
        confirm = input("Type 'DELETE ALL' to confirm: ")
        
        if confirm != "DELETE ALL":
            print("❌ Cancellation confirmed. No data was deleted.")
            return False
        
        print("\n🗑️  Clearing all data...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✅ Database cleared and recreated.")
        return True
    
    def seed_employers(self):
        """Seed realistic employer/restaurant data."""
        print("\n🏢 Seeding Employers...")
        
        employers_data = [
            {
                "email": "hr@tamarindrestaurant.com",
                "password": "Tamarind@2024",
                "company_name": "Tamarind Restaurant",
                "industry": "Fine Dining",
                "location": "Nariman Point, Mumbai",
                "description": "Award-winning fine dining restaurant specializing in progressive Indian cuisine. Part of the Tamarind Collection with locations across India.",
                "website": "www.tamarindrestaurant.com",
                "verified": True
            },
            {
                "email": "careers@theoberoidelhi.com",
                "password": "Oberoi@2024",
                "company_name": "The Oberoi Hotel Mumbai",
                "industry": "5-Star Luxury Hotel",
                "location": "Nariman Point, Mumbai",
                "description": "Iconic 5-star luxury hotel featuring multiple restaurants including Fenix, Vetro, and The Dome. Known for exceptional hospitality and culinary excellence.",
                "website": "www.oberoihotels.com",
                "verified": True
            },
            {
                "email": "jobs@socialoffline.in",
                "password": "Social@2024",
                "company_name": "Social Restaurants",
                "industry": "Casual Dining Chain",
                "location": "Multiple locations, Mumbai",
                "description": "Popular casual dining chain with 15+ locations across Mumbai. Known for fusion cuisine, craft cocktails, and co-working spaces.",
                "website": "www.socialoffline.in",
                "verified": True
            },
            {
                "email": "hr@indigo-mumbai.com",
                "password": "Indigo@2024",
                "company_name": "Indigo Delicatessen",
                "industry": "European Cafe",
                "location": "Colaba, Mumbai",
                "description": "European-style delicatessen and restaurant serving artisanal food with an emphasis on fresh, quality ingredients.",
                "website": "www.foodhallmarkets.com",
                "verified": True
            },
            {
                "email": "hiring@bastianrestaurant.com",
                "password": "Bastian@2024",
                "company_name": "Bastian - Seafood & Bar",
                "industry": "Seafood Restaurant",
                "location": "Bandra, Mumbai",
                "description": "Mumbai's premier seafood restaurant and bar, known for fresh catches and innovative cocktails. Celebrity chef-owned establishment.",
                "website": "www.bastianrestaurant.com",
                "verified": True
            },
            {
                "email": "jobs@thebombaycanteen.com",
                "password": "BombayCanteen@2024",
                "company_name": "The Bombay Canteen",
                "industry": "Regional Indian Cuisine",
                "location": "Lower Parel, Mumbai",
                "description": "Contemporary Indian restaurant celebrating regional flavors and ingredients. Award-winning cocktail program and innovative menu.",
                "website": "www.thebombaycanteen.com",
                "verified": True
            },
            {
                "email": "careers@olive-bar.com",
                "password": "Olive@2024",
                "company_name": "Olive Bar & Kitchen",
                "industry": "Mediterranean Restaurant",
                "location": "Bandra, Mumbai",
                "description": "Upscale Mediterranean restaurant with beautiful outdoor seating. Known for authentic Italian and Mediterranean cuisine.",
                "website": "www.olive-bar.com",
                "verified": True
            },
            {
                "email": "hr@zomatokitchen.com",
                "password": "ZomatoKitchen@2024",
                "company_name": "Zomato Kitchen",
                "industry": "Cloud Kitchen",
                "location": "Andheri, Mumbai",
                "description": "Large-scale cloud kitchen operation serving multiple brands. High-volume production facility with modern kitchen technology.",
                "website": "www.zomato.com",
                "verified": True
            },
        ]
        
        for emp_data in employers_data:
            # Create user account
            user = User(
                email=emp_data["email"],
                hashed_password=get_password_hash(emp_data["password"]),
                role=UserRole.EMPLOYER,
                is_active=True,
                created_at=datetime.utcnow()
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Create employer profile
            employer = Employer(
                user_id=user.id,
                company_name=emp_data["company_name"],
                industry=emp_data["industry"],
                location=emp_data["location"],
                company_profile=emp_data["description"],
                website=emp_data.get("website"),
                verification_status="verified" if emp_data.get("verified") else "pending",
                created_at=datetime.utcnow()
            )
            self.db.add(employer)
            self.db.commit()
            self.db.refresh(employer)
            
            self.created_users.append(user)
            self.created_employers.append(employer)
            print(f"  ✅ {employer.company_name} (ID: {employer.id})")
        
        print(f"\n✅ Created {len(self.created_employers)} employers")
    
    def seed_employees(self):
        """Seed realistic employee profiles."""
        print("\n👨‍🍳 Seeding Employees...")
        
        employees_data = [
            {
                "email": "chef.arjun@gmail.com",
                "password": "Chef@2024",
                "full_name": "Arjun Mehta",
                "phone": "+91-9876543210",
                "location": "Mumbai",
                "current_role": "Executive Chef",
                "experience_years": 12,
                "skills": ["North Indian Cuisine", "Fine Dining", "Team Management", "Menu Development", "Cost Control", "HACCP Certified"],
                "preferred_roles": ["chef", "cook"],
                "availability": "2 weeks notice",
                "resume_text": """ARJUN MEHTA
Executive Chef | 12 Years Experience

PROFESSIONAL SUMMARY
Passionate Executive Chef with over 12 years of experience in fine dining and luxury hotel kitchens. Specialized in North Indian and contemporary fusion cuisine. Proven track record of leading teams, reducing costs, and creating award-winning menus.

EXPERIENCE
Executive Chef | The Grand Taj Hotel, Mumbai (2019-Present)
• Lead kitchen team of 25+ staff across 3 restaurants
• Reduced food costs by 22% while maintaining quality standards
• Developed seasonal menu that increased revenue by 35%
• Maintained highest food safety standards (HACCP certified)
• Trained and mentored 15+ junior chefs

Sous Chef | ITC Maratha, Mumbai (2015-2019)
• Managed daily kitchen operations for 200+ cover restaurant
• Specialized in regional Indian cuisines
• Implemented inventory management system
• Assisted in achieving Michelin Bib Gourmand recognition

Chef de Partie | Taj Mahal Palace, Mumbai (2012-2015)
• Specialty: North Indian and Tandoor cuisine
• Prepared dishes for VIP guests and events
• Maintained station cleanliness and organization

EDUCATION & CERTIFICATIONS
• Diploma in Culinary Arts - IHM Mumbai (2012)
• HACCP Food Safety Certification (2020)
• Management Development Program - Oberoi Centre (2018)

SKILLS
• North Indian & Mughlai Cuisine Expert
• Team Leadership & Training
• Menu Engineering & Costing
• Inventory & Vendor Management
• Food Safety & Hygiene (HACCP)
• Multi-cuisine Knowledge

ACHIEVEMENTS
• Times Food Award - Best North Indian Restaurant (2022)
• Reduced kitchen waste by 30% through optimization
• Successfully launched 3 new restaurant concepts

LANGUAGES
English, Hindi, Marathi"""
            },
            {
                "email": "maria.rodrigues@gmail.com",
                "password": "Maria@2024",
                "full_name": "Maria Rodrigues",
                "phone": "+91-9876543211",
                "location": "Mumbai",
                "current_role": "Pastry Chef",
                "experience_years": 8,
                "skills": ["Pastry", "Baking", "Desserts", "French Techniques", "Chocolate Work", "Plating"],
                "preferred_roles": ["chef"],
                "availability": "Immediate",
                "resume_text": """MARIA RODRIGUES
Pastry Chef | 8 Years Experience

PROFESSIONAL SUMMARY
Creative Pastry Chef with 8 years of experience in fine dining and luxury hotels. Specialized in French pastry techniques, modern plating, and chocolate work. Known for innovative dessert concepts and consistent quality.

EXPERIENCE
Pastry Chef | The Leela Palace, Mumbai (2019-Present)
• Lead pastry section serving 150+ daily covers
• Created signature dessert menu (20+ items)
• Managed team of 6 pastry cooks
• Maintained 98% customer satisfaction rating
• Reduced dessert costs by 15% through smart sourcing

Demi Chef de Partie - Pastry | Four Seasons, Mumbai (2016-2019)
• Prepared French pastries and desserts
• Assisted in wedding and event dessert production
• Trained junior pastry cooks
• Maintained ingredient inventory

Commis - Pastry | ITC Grand Central (2015-2016)
• Learned classical French pastry techniques
• Assisted in daily mise en place
• Maintained cleanliness and organization

EDUCATION & CERTIFICATIONS
• Advanced Diploma in Pastry Arts - Le Cordon Bleu (2015)
• Chocolate & Confectionery Course - Barry Callebaut (2018)
• Food Safety Certification (2015)

SKILLS
• French Pastry Techniques
• Dessert Conceptualization
• Chocolate Tempering & Molding  
• Sugar Work & Decorations
• Modern Plating & Presentation
• Team Management

SPECIALTIES
• Classic French Pastries
• Modern Plated Desserts
• Wedding & Event Cakes
• Chocolate Bonbons
• Artisan Breads

LANGUAGES
English, Hindi, Konkani, French (Basic)"""
            },
            {
                "email": "rajesh.kumar.chef@gmail.com",
                "password": "Rajesh@2024",
                "full_name": "Rajesh Kumar",
                "phone": "+91-9876543212",
                "location": "Mumbai",
                "current_role": "Sous Chef",
                "experience_years": 6,
                "skills": ["Multi-Cuisine", "Continental", "Italian", "Team Leadership", "Stock Management"],
                "preferred_roles": ["chef", "cook"],
                "availability": "1 month notice",
                "resume_text": """RAJESH KUMAR
Sous Chef | 6 Years Experience

PROFESSIONAL SUMMARY
Versatile Sous Chef with 6 years of experience in multi-cuisine restaurants. Strong expertise in Continental, Italian, and Asian cuisines. Excellent team player with proven ability to manage high-pressure situations.

EXPERIENCE
Sous Chef | Zorba - The Buddha, Mumbai (2020-Present)
• Manage kitchen operations for 120-cover restaurant
• Specialize in Continental and Italian cuisines
• Train and supervise team of 8 line cooks
• Handle inventory and vendor relationships
• Ensure food quality and consistency

Chef de Partie | Mainland China, Mumbai (2018-2020)
• Primary responsibility: Asian cuisine section
• Prepared authentic Chinese and Asian dishes
• Maintained station during peak hours (200+ covers)
• Assisted in menu development

Commis II & I | Café Zoe, Mumbai (2017-2018)
• Learned multi-cuisine cooking techniques
• Assisted senior chefs in daily operations
• Completed comprehensive training program

EDUCATION
• Diploma in Hotel Management & Catering - IHM Mumbai (2017)
• Food Safety Handler's Certificate (2017)

SKILLS
• Continental Cuisine
• Italian Cuisine
• Asian Cuisine
• Grill & Roast Techniques
• Sauce Preparation
• Team Coordination
• Inventory Management

LANGUAGES
Hindi, English, Punjabi"""
            },
            {
                "email": "priya.nair.server@gmail.com",
                "password": "Priya@2024",
                "full_name": "Priya Nair",
                "phone": "+91-9876543213",
                "location": "Mumbai",
                "current_role": "Restaurant Supervisor",
                "experience_years": 7,
                "skills": ["Customer Service", "Table Management", "Wine Service", "Staff Training", "POS Systems", "Guest Relations"],
                "preferred_roles": ["waiter"],
                "availability": "Immediate",
                "resume_text": """PRIYA NAIR
Restaurant Supervisor | 7 Years Experience

PROFESSIONAL SUMMARY
Experienced Restaurant Supervisor with 7 years in fine dining environments. Expert in customer service, wine pairing, and team management. Known for creating memorable guest experiences and training high-performing service teams.

EXPERIENCE
Restaurant Supervisor | Trishna Restaurant, Mumbai (2020-Present)
• Supervise team of 12 servers and hosts
• Manage floor operations for 80-seat restaurant
• Train new staff on service standards and menu
• Handle guest complaints and special requests
• Increased customer satisfaction scores to 4.8/5

Senior Waiter | Gauri Khan Designs Restaurant (2018-2020)
• Provided fine dining table service
• Specialized in wine recommendations and pairings
• Consistently achieved highest sales in team
• Mentored junior waitstaff

Waiter | Olive Bar & Kitchen, Mumbai (2016-2018)
• Served guests in upscale Mediterranean setting
• Learned wine service and cocktail knowledge
• Managed sections of 6-8 tables

EDUCATION & CERTIFICATIONS
• Diploma in Hospitality & Hotel Management (2016)
• Wine & Spirits Education Trust (WSET) Level 2 (2019)
• Food Safety & Hygiene Certificate (2016)

SKILLS
• Fine Dining Service Excellence
• Wine Knowledge & Pairing  
• Team Leadership & Training
• Guest Relationship Management
• POS Systems (Petpooja, Posist)
• Conflict Resolution
• Upselling Techniques

ACHIEVEMENTS
• Employee of the Year 2021
• Highest average bill per table (6 consecutive months)
• Successfully trained 20+ new servers

LANGUAGES
English (Fluent), Hindi (Fluent), Malayalam (Native), Marathi (Intermediate)"""
            },
            {
                "email": "vikram.bartender@gmail.com",
                "password": "Vikram@2024",
                "full_name": "Vikram Singh",
                "phone": "+91-9876543214",
                "location": "Mumbai",
                "current_role": "Head Bartender",
                "experience_years": 5,
                "skills": ["Mixology", "Cocktail Creation", "Bar Management", "Inventory Control", "Customer Service", "Flair Bartending"],
                "preferred_roles": ["bartender"],
                "availability": "2 weeks notice",
                "resume_text": """VIKRAM SINGH
Head Bartender | 5 Years Experience

PROFESSIONAL SUMMARY
Creative and skilled Head Bartender with 5 years of experience in upscale bars and restaurants. Expert in mixology, cocktail innovation, and customer engagement. Known for creating signature cocktails and managing efficient bar operations.

EXPERIENCE
Head Bartender | AER - Four Seasons, Mumbai (2021-Present)
• Lead bar team of 4 bartenders
• Created seasonal cocktail menu (15 signature drinks)
• Manage inventory and supplier relationships  
• Train staff on mixology and service standards
• Achieved 30% increase in bar revenue

Senior Bartender | Aer Lounge, Mumbai (2019-2021)
• Prepared classic and contemporary cocktails
• Engaged with premium clientele
• Maintained bar cleanliness and organization
• Assisted in menu development

Bartender | Social, Mumbai (2018-2019)
• Served high-volume casual dining environment
• Learned craft cocktail techniques
• Managed cash handling and POS operations

EDUCATION & CERTIFICATIONS
• Professional Bartending Certification - Indian Bartenders Academy (2018)
• Mixology Masterclass - Diageo World Class (2020)
• WSET Level 2 Spirits (2021)
• Responsible Alcohol Service Certified (2018)

SKILLS
• Advanced Mixology
• Cocktail Innovation & Menu Development
• Spirits Knowledge (Whiskey, Gin, Rum)
• Bar Inventory Management
• Staff Training & Development
• Customer Engagement
• Flair Bartending

SIGNATURE COCKTAILS
• Mumbai Monsoon (Featured in TimeOut Mumbai)
• Spice Route Sour
• Gateway Gin Fizz

LANGUAGES
English, Hindi, Punjabi"""
            },
            {
                "email": "sneha.cook@gmail.com",
                "password": "Sneha@2024",
                "full_name": "Sneha Deshmukh",
                "phone": "+91-9876543215",
                "location": "Mumbai",
                "current_role": "Line Cook",
                "experience_years": 3,
                "skills": ["Basic Cooking", "Food Prep", "Grill", "Hygiene Standards", "Fast-Paced Environment"],
                "preferred_roles": ["cook"],
                "availability": "Immediate",
                "resume_text": """SNEHA DESHMUKH
Line Cook | 3 Years Experience

PROFESSIONAL SUMMARY
Dedicated Line Cook with 3 years of experience in fast-paced restaurant kitchens. Strong work ethic, excellent time management, and commitment to food quality. Eager to learn and grow in the culinary field.

EXPERIENCE
Line Cook | Social Offline, Khar (2021-Present)
• Manage grill and sauté station
• Prepare dishes according to recipes and standards
• Maintain clean and organized workstation
• Handle peak service periods (150+ covers)
• Support team during busy shifts

Commis | The Pantry, Mumbai (2020-2021)
• Assisted in food preparation and cooking
• Learned basic cooking techniques
• Maintained kitchen cleanliness
• Managed mise en place for service

EDUCATION
• Certificate in Commercial Cooking - AISSMS College (2020)
• Food Safety & Hygiene Certificate (2020)

SKILLS
• Grill & Sauté Cooking
• Food Preparation & Mise en Place
• Recipe Following & Consistency
• Time Management
• Kitchen Safety & Hygiene
• Team Collaboration

STRENGTHS
• Quick learner
• Punctual and reliable
• Works well under pressure
• Positive attitude

LANGUAGES
Marathi (Native), Hindi, English"""
            },
            {
                "email": "amit.operations@gmail.com",
                "password": "Amit@2024",
                "full_name": "Amit Kapoor",
                "phone": "+91-9876543216",
                "location": "Mumbai",
                "current_role": "Restaurant Manager",
                "experience_years": 10,
                "skills": ["Operations Management", "P&L Management", "Staff Management", "Customer Service", "Process Optimization", "Vendor Relations"],
                "preferred_roles": ["host"],
                "availability": "1 month notice",
                "resume_text": """AMIT KAPOOR
Restaurant Manager | 10 Years Experience

PROFESSIONAL SUMMARY
Results-driven Restaurant Manager with 10 years of comprehensive experience in restaurant operations. Expertise in P&L management, team leadership, and operational excellence. Track record of improving efficiency and profitability.

EXPERIENCE
Restaurant Manager | Barbeque Nation, Mumbai (2019-Present)
• Manage end-to-end operations for 200-seat restaurant
• Oversee team of 35+ staff (kitchen & service)
• Achieved 120% of annual revenue targets (2022, 2023)
• Reduced operational costs by 18%
• Maintained 4.3+ rating on all platforms

Assistant Manager | Mainland China, Mumbai (2016-2019)
• Assisted in daily operations and staff management
• Handled customer complaints and service recovery
• Managed inventory and vendor relationships
• Coordinated events and private dining

Floor Manager | TGI Fridays, Mumbai (2013-2016)
• Managed service floor and guest experience
• Trained and developed service staff
• Ensured brand standards compliance

EDUCATION
• MBA - Hospitality Management (2013)
• Bachelor's in Hotel Management - IHM Mumbai (2011)

SKILLS
• Restaurant Operations Management
• P&L & Budget Management
• Staff Recruitment & Training
• Customer Service Excellence
• Process Optimization
• Health & Safety Compliance
• POS & Restaurant Technology

ACHIEVEMENTS
• Voted Manager of the Year 2022
• Reduced staff turnover by 35%
• Successfully launched 2 new restaurant locations

LANGUAGES
English, Hindi, Punjabi, Marathi"""
            },
            {
                "email": "ravi.fresher@gmail.com",
                "password": "Ravi@2024",
                "full_name": "Ravi Yadav",
                "phone": "+91-9876543217",
                "location": "Mumbai",
                "current_role": "Student/Fresher",
                "experience_years": 0,
                "skills": ["Eager to Learn", "Hospitality", "Basic Kitchen Knowledge", "Good Communication"],
                "preferred_roles": ["dishwasher", "cook"],
                "availability": "Immediate",
                "resume_text": """RAVI YADAV
Hospitality Graduate | Fresher

OBJECTIVE
Enthusiastic hospitality graduate seeking an entry-level position in a restaurant kitchen to start my culinary career. Eager to learn from experienced chefs and contribute to a dynamic team.

EDUCATION
• Diploma in Hotel Management & Catering - AISSMS (2023)
• Secondary School Certificate (SSC) - 75%

INTERNSHIP EXPERIENCE
Kitchen Intern | Marriott Hotel, Mumbai (3 months - 2023)
• Assisted in food preparation and basic cooking
• Learned kitchen hygiene and safety standards
• Observed different kitchen stations
• Supported team during service periods

SKILLS
• Basic Cooking Knowledge
• Quick Learner
• Team Player
• Punctual & Reliable
• Basic English Communication
• Willing to work flexible hours

CERTIFICATIONS
• Food Safety & Hygiene Certificate (2023)

STRENGTHS
• Strong work ethic
• Adaptable to different roles
• Respectful and eager to learn
• Available for all shifts

LANGUAGES
Hindi (Native), Marathi, English (Basic)

AVAILABILITY
Immediate joining, flexible with shifts"""
            },
        ]
        
        for emp_data in employees_data:
            # Create user account
            user = User(
                email=emp_data["email"],
                hashed_password=get_password_hash(emp_data["password"]),
                role=UserRole.EMPLOYEE,
                is_active=True,
                created_at=datetime.utcnow()
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Create employee profile
            # Map preferred_roles to preferred_role enum if available
            preferred_roles = emp_data.get("preferred_roles", [])
            preferred_role = None
            if preferred_roles:
                # Try to map to RestaurantRole enum
                role_map = {
                    "chef": RestaurantRole.CHEF,
                    "cook": RestaurantRole.COOK,
                    "waiter": RestaurantRole.WAITER,
                    "bartender": RestaurantRole.BARTENDER,
                    "host": RestaurantRole.HOST,
                    "dishwasher": RestaurantRole.DISHWASHER
                }
                for role in preferred_roles:
                    if role.lower() in role_map:
                        preferred_role = role_map[role.lower()]
                        break
            
            employee = Employee(
                user_id=user.id,
                full_name=emp_data["full_name"],
                phone=emp_data["phone"],
                preferred_location=emp_data["location"],
                experience_years=emp_data["experience_years"],
                skills=emp_data["skills"],
                preferred_role=preferred_role,
                availability=emp_data.get("availability", "Immediate"),
                resume_text=emp_data["resume_text"],
                created_at=datetime.utcnow()
            )
            self.db.add(employee)
            self.db.commit()
            self.db.refresh(employee)
            
            self.created_users.append(user)
            self.created_employees.append(employee)
            print(f"  ✅ {employee.full_name} - {emp_data['current_role']} ({emp_data['experience_years']} yrs)")
        
        print(f"\n✅ Created {len(self.created_employees)} employees")
    
    def seed_jobs(self):
        """Seed realistic job postings."""
        print("\n💼 Seeding Jobs...")
        
        # Jobs mapped to employers
        jobs_by_employer = {
            "Tamarind Restaurant": [
                {
                    "title": "Executive Chef - Fine Dining",
                    "description": """Tamarind Restaurant is seeking an experienced Executive Chef to lead our kitchen team.

**Responsibilities:**
- Lead and manage kitchen team of 20+ staff
- Develop and innovate seasonal menus focusing on progressive Indian cuisine
- Ensure highest standards of food quality and presentation
- Manage food costs, inventory, and vendor relationships
- Train and mentor junior chefs
- Maintain HACCP and food safety standards

**Requirements:**
- 8+ years of experience in fine dining kitchens
- Expertise in Indian cuisine (regional knowledge preferred)
- Proven track record of menu development
- Strong leadership and team management skills
- HACCP certification required
- Culinary degree from recognized institute

**What We Offer:**
- Competitive salary package
- Performance bonuses
- Professional development opportunities
- Work with award-winning culinary team

Join us in creating unforgettable dining experiences!""",
                    "requirements": "8+ years fine dining experience, HACCP certified, culinary degree",
                    "location": "Nariman Point, Mumbai",
                    "job_type": "full_time",
                    "salary_min": 80000,
                    "salary_max": 120000,
                    "job_category": JobCategory.CHEF,
                    "quantity_needed": 1
                },
            ],
            "The Oberoi Hotel Mumbai": [
                {
                    "title": "Pastry Chef - Luxury Hotel",
                    "description": """The Oberoi Mumbai is looking for a talented Pastry Chef to join our culinary team.

**Responsibilities:**
- Oversee pastry section across multiple F&B outlets
- Create innovative desserts and pastries
- Manage pastry team and daily operations
- Maintain consistency and quality standards
- Control costs and minimize waste
- Ensure food safety compliance

**Requirements:**
- 5+ years experience in luxury hotel or fine dining pastry
- Expertise in French pastry techniques
- Knowledge of modern plating and presentation
- Strong creativity and attention to detail
- Culinary degree with pastry specialization

**Benefits:**
- Industry-leading compensation
- Career growth opportunities
- International exposure
- Staff accommodation available""",
                    "requirements": "5+ years pastry experience, French techniques, culinary degree",
                    "location": "Nariman Point, Mumbai",
                    "job_type": "full_time",
                    "salary_min": 60000,
                    "salary_max": 90000,
                    "job_category": JobCategory.CHEF,
                    "quantity_needed": 1
                },
                {
                    "title": "Head Bartender - Premium Bar",
                    "description": """Join The Oberoi's award-winning bar team as Head Bartender.

**Responsibilities:**
- Manage bar operations and team
- Create signature cocktails and seasonal menu
- Train and develop bartending staff
- Ensure exceptional guest experiences
- Manage inventory and costs
- Maintain bar cleanliness and compliance

**Requirements:**
- 4+ years bartending experience (luxury hotel/fine dining)
- Expert mixology skills
- WSET Level 2 or equivalent
- Strong leadership abilities
- Excellent guest interaction skills

**Perks:**
- Competitive salary + tips
- Creative freedom for menu development
- Professional bartending courses sponsored
- Dynamic work environment""",
                    "requirements": "4+ years experience, mixology expertise, WSET certification",
                    "location": "Nariman Point, Mumbai",
                    "job_type": "full_time",
                    "salary_min": 45000,
                    "salary_max": 70000,
                    "job_category": JobCategory.BARTENDER,
                    "quantity_needed": 1
                },
            ],
            "Social Restaurants": [
                {
                    "title": "Sous Chef - Multiple Locations",
                    "description": """Social is expanding! We need talented Sous Chefs across our Mumbai locations.

**Role:**
- Support Executive Chef in kitchen management
- Ensure food quality and consistency
- Manage your section during service
- Train and mentor line cooks
- Contribute to menu development
- Handle inventory for your section

**What You Need:**
- 4+ years kitchen experience
- Multi-cuisine knowledge (Continental, Asian, Indian)
- High-volume restaurant experience
- Team player with positive attitude
- Culinary training preferred

**Why Social:**
- Fast-growing company with career progression
- Creative and fun work culture
- Staff meals and discounts
- Competitive compensation
- Multiple location opportunities""",
                    "requirements": "4+ years experience, multi-cuisine knowledge, high-volume experience",
                    "location": "Multiple locations, Mumbai",
                    "job_type": "full_time",
                    "salary_min": 40000,
                    "salary_max": 60000,
                    "job_category": JobCategory.CHEF,
                    "quantity_needed": 3
                },
                {
                    "title": "Line Cooks - All Locations",
                    "description": """Social is hiring Line Cooks for our growing restaurant chain!

**Responsibilities:**
- Prepare and cook menu items as per recipes
- Maintain station during service
- Follow food safety protocols
- Support team members
- Keep workstation clean and organized

**Requirements:**
- 1-3 years cooking experience
- Ability to work in fast-paced environment
- Basic cooking skills
- Willingness to learn
- Flexible with shifts

**Benefits:**
- Competitive salary
- Tips sharing
- Staff meals
- Fun work environment
- Growth opportunities""",
                    "requirements": "1-3 years experience, basic cooking skills, flexible schedule",
                    "location": "Multiple locations, Mumbai",
                    "job_type": "full_time",
                    "salary_min": 25000,
                    "salary_max": 35000,
                    "job_category": JobCategory.COOK,
                    "quantity_needed": 5
                },
            ],
            "Indigo Delicatessen": [
                {
                    "title": "Restaurant Supervisor",
                    "description": """Indigo Deli seeks an experienced Restaurant Supervisor to lead our floor team.

**Key Responsibilities:**
- Supervise service staff during operations
- Ensure exceptional guest experiences
- Handle customer queries and complaints
- Train new waitstaff on standards
- Manage floor operations and table assignments
- Support restaurant manager

**Requirements:**
- 5+ years in fine dining/upscale casual dining
- Strong leadership and communication
- Wine knowledge preferred
- Problem-solving skills
- Hospitality degree/diploma

**What We Offer:**
- Competitive package
- European work environment
- Artisanal food culture
- Career development""",
                    "requirements": "5+ years service experience, leadership skills, hospitality education",
                    "location": "Colaba, Mumbai",
                    "job_type": "full_time",
                    "salary_min": 35000,
                    "salary_max": 50000,
                    "job_category": JobCategory.WAITER,
                    "quantity_needed": 1
                },
            ],
            "Bastian - Seafood & Bar": [
                {
                    "title": "Senior Waiter - Fine Dining",
                    "description": """Bastian, Mumbai's premier seafood restaurant, is hiring Senior Waiters.

**Role:**
- Provide exceptional table service
- Expert knowledge of menu and wine list
- Upsell premium items and experiences
- Mentor junior servers
- Handle VIP guests
- Ensure smooth service flow

**Must-Have:**
- 3+ years fine dining experience
- Wine knowledge (WSET Level 1 minimum)
- Excellent English communication
- Professional appearance and demeanor
- Weekend availability essential

**Perks:**
- Premium tips
- Work with celebrity clientele
- Bandra location
- Staff discounts
- Upscale environment""",
                    "requirements": "3+ years fine dining experience, wine knowledge, excellent communication",
                    "location": "Bandra, Mumbai",
                    "job_type": "full_time",
                    "salary_min": 28000,
                    "salary_max": 40000,
                    "job_category": JobCategory.WAITER,
                    "quantity_needed": 2
                },
            ],
            "The Bombay Canteen": [
                {
                    "title": "Bartender - Craft Cocktails",
                    "description": """The Bombay Canteen seeks passionate Bartenders for our award-winning bar.

**What You'll Do:**
- Prepare cocktails using fresh, seasonal ingredients
- Engage with guests and recommend drinks
- Maintain bar cleanliness and organization
- Support bar inventory management
- Learn about Indian spirits and ingredients

**What You Need:**
- 2+ years bartending experience
- Passion for craft cocktails
- Good product knowledge
- Team player attitude
- Creativity and willingness to experiment

**Why TBC:**
- Learn from award-winning bar team
- Creative cocktail program
- Ingredient-focused approach
- Vibrant work culture
- Competitive compensation + tips""",
                    "requirements": "2+ years experience, craft cocktail knowledge, team player",
                    "location": "Lower Parel, Mumbai",
                    "job_type": "full_time",
                    "salary_min": 30000,
                    "salary_max": 45000,
                    "job_category": JobCategory.BARTENDER,
                    "quantity_needed": 2
                },
            ],
            "Olive Bar & Kitchen": [
                {
                    "title": "Restaurant Manager",
                    "description": """Olive Bar & Kitchen is seeking an experienced Restaurant Manager.

**Responsibilities:**
- Overall restaurant operations management
- Lead and motivate team of 30+ staff
- Ensure exceptional guest experiences
- P&L management and cost control
- Vendor and supplier management
- Compliance with health and safety regulations
- Event coordination and private dining

**Requirements:**
- 8+ years in restaurant management
- Proven P&L management experience
- Strong leadership capabilities
- Excellent customer service skills
- Hospitality management degree/MBA preferred

**Package:**
- Attractive salary + performance incentives
- Growth opportunities in restaurant group
- Beautiful work environment
- Industry-leading benefits""",
                    "requirements": "8+ years management experience, P&L skills, hospitality degree",
                    "location": "Bandra, Mumbai",
                    "job_type": "full_time",
                    "salary_min": 70000,
                    "salary_max": 100000,
                    "job_category": JobCategory.HOST,
                    "quantity_needed": 1
                },
            ],
            "Zomato Kitchen": [
                {
                    "title": "Kitchen Assistant / Trainee Cook",
                    "description": """Zomato Kitchen is hiring Kitchen Assistants for our cloud kitchen operations.

**Perfect For:**
- Freshers with culinary education
- Those wanting to start F&B career
- Hardworking individuals ready to learn

**Responsibilities:**
- Assist in food preparation
- Follow recipes and SOPs
- Maintain cleanliness
- Support senior cooks
- Learn cooking techniques

**Requirements:**
- Hospitality/culinary education OR 1 year experience
- Willingness to learn and work hard
- Ability to work in fast-paced environment
- Flexible with shifts (including weekends)
- Food safety awareness

**We Offer:**
- Structured training program
- Career growth in large organization
- Competitive starting salary
- Modern kitchen facilities
- Job security""",
                    "requirements": "Fresher or 1 year experience, culinary education, willing to learn",
                    "location": "Andheri, Mumbai",
                    "job_type": "full_time",
                    "salary_min": 18000,
                    "salary_max": 25000,
                    "job_category": JobCategory.COOK,
                    "quantity_needed": 4
                },
            ],
        }
        
        for employer in self.created_employers:
            if employer.company_name in jobs_by_employer:
                jobs_data = jobs_by_employer[employer.company_name]
                
                for job_data in jobs_data:
                    # Create salary_range string from min/max
                    salary_min = job_data.get("salary_min")
                    salary_max = job_data.get("salary_max")
                    salary_range = None
                    if salary_min and salary_max:
                        salary_range = f"₹{salary_min:,} - ₹{salary_max:,}"
                    
                    job = Job(
                        employer_id=employer.id,
                        title=job_data["title"],
                        description=job_data["description"],
                        requirements=job_data.get("requirements"),
                        location=job_data["location"],
                        job_type=job_data.get("job_type", "full_time"),
                        salary_range=salary_range,
                        job_category=job_data.get("job_category"),
                        quantity_needed=job_data.get("quantity_needed", 1),
                        is_active=True,
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    self.db.add(job)
                    self.db.commit()
                    self.db.refresh(job)
                    
                    self.created_jobs.append(job)
                    salary_display = salary_range if salary_range else "Salary not specified"
                    print(f"  ✅ {job.title} @ {employer.company_name} ({salary_display})")
        
        print(f"\n✅ Created {len(self.created_jobs)} jobs")
    
    def seed_applications(self):
        """Seed realistic job applications."""
        print("\n📝 Seeding Applications...")
        
        # Create realistic application scenarios
        application_count = 0
        
        for employee in self.created_employees:
            # Each employee applies to 2-4 relevant jobs
            num_applications = random.randint(2, 4)
            
            # Filter jobs that match employee's skills/experience
            relevant_jobs = self._filter_relevant_jobs(employee)
            
            if not relevant_jobs:
                relevant_jobs = random.sample(self.created_jobs, min(num_applications, len(self.created_jobs)))
            
            selected_jobs = random.sample(relevant_jobs, min(num_applications, len(relevant_jobs)))
            
            for i, job in enumerate(selected_jobs):
                # Calculate realistic match score based on skills and experience
                match_score = self._calculate_match_score(employee, job)
                
                # Determine application status based on match score and time
                days_ago = random.randint(1, 45)
                status = self._determine_status(match_score, days_ago)
                
                application = Application(
                    job_id=job.id,
                    employee_id=employee.id,
                    status=status,
                    match_score=match_score,
                    cover_letter=self._generate_cover_letter(employee, job),
                    applied_at=datetime.utcnow() - timedelta(days=days_ago),
                    created_at=datetime.utcnow() - timedelta(days=days_ago)
                )
                
                self.db.add(application)
                self.db.commit()
                self.db.refresh(application)
                
                self.created_applications.append(application)
                application_count += 1
                print(f"  ✅ {employee.full_name} → {job.title} (Score: {match_score}, Status: {status.value})")
        
        print(f"\n✅ Created {application_count} applications")
    
    def _filter_relevant_jobs(self, employee: Employee):
        """Filter jobs relevant to employee's profile."""
        relevant_jobs = []
        
        for job in self.created_jobs:
            # Match based on job category and preferred roles
            if employee.preferred_job_types:
                for pref in employee.preferred_job_types:
                    if job.job_category and pref.lower() in job.job_category.value.lower():
                        relevant_jobs.append(job)
                        break
            
            # Match based on skills in job description
            if employee.skills and job.description:
                skill_matches = sum(1 for skill in employee.skills 
                                  if skill.lower() in job.description.lower())
                if skill_matches >= 2:
                    if job not in relevant_jobs:
                        relevant_jobs.append(job)
        
        return relevant_jobs
    
    def _calculate_match_score(self, employee: Employee, job: Job) -> float:
        """Calculate realistic match score."""
        score = 0.5  # Base score
        
        # Experience match
        if job.salary_min:
            if job.salary_min >= 70000 and employee.experience_years >= 8:
                score += 0.2
            elif job.salary_min >= 40000 and employee.experience_years >= 4:
                score += 0.15
            elif job.salary_min <= 30000:
                score += 0.1
        
        # Skills match
        if employee.skills and job.description:
            skill_matches = sum(1 for skill in employee.skills 
                              if skill.lower() in job.description.lower())
            score += min(skill_matches * 0.05, 0.25)
        
        # Category match
        if employee.preferred_job_types and job.job_category:
            for pref in employee.preferred_job_types:
                if pref.lower() in job.job_category.value.lower():
                    score += 0.1
                    break
        
        return round(min(score, 0.98), 2)
    
    def _determine_status(self, match_score: float, days_ago: int) -> ApplicationStatus:
        """Determine application status based on match score and time."""
        if days_ago <= 7:
            return ApplicationStatus.APPLIED
        elif days_ago <= 14:
            if match_score >= 0.75:
                return ApplicationStatus.REVIEWING
            return ApplicationStatus.APPLIED
        elif days_ago <= 30:
            if match_score >= 0.85:
                return random.choice([ApplicationStatus.INTERVIEW_SCHEDULED, ApplicationStatus.SELECTED])
            elif match_score >= 0.70:
                return ApplicationStatus.REVIEWING
            else:
                return random.choice([ApplicationStatus.APPLIED, ApplicationStatus.REJECTED])
        else:
            if match_score >= 0.80:
                return random.choice([ApplicationStatus.SELECTED, ApplicationStatus.HIRED, ApplicationStatus.REJECTED])
            else:
                return ApplicationStatus.REJECTED
    
    def _generate_cover_letter(self, employee: Employee, job: Job) -> str:
        """Generate realistic cover letter."""
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job.title} position at your esteemed establishment.

With {employee.experience_years} years of experience in the hospitality industry, I believe I would be a valuable addition to your team. My expertise in {', '.join(employee.skills[:3]) if employee.skills else 'the field'} aligns well with the requirements of this role.

I am particularly drawn to this opportunity because of your reputation for excellence and would welcome the chance to contribute to your continued success.

I am available {employee.availability} and would appreciate the opportunity to discuss how my skills and experience can benefit your organization.

Thank you for considering my application.

Best regards,
{employee.full_name}
{employee.phone_number}
{employee.user.email}"""
    
    def seed_all(self, clear_first=False):
        """Seed all data."""
        print("\n" + "="*70)
        print("🌱 SEEDING REALISTIC DATA FOR SMARTSERVE")
        print("="*70)
        
        if clear_first:
            if not self.clear_all_data():
                return
        
        try:
            self.seed_employers()
            self.seed_employees()
            self.seed_jobs()
            self.seed_applications()
            
            print("\n" + "="*70)
            print("✅ SEEDING COMPLETE!")
            print("="*70)
            
            print("\n📊 Summary:")
            print(f"  • Employers: {len(self.created_employers)}")
            print(f"  • Employees: {len(self.created_employees)}")
            print(f"  • Jobs: {len(self.created_jobs)}")
            print(f"  • Applications: {len(self.created_applications)}")
            
            print("\n🔐 Login Credentials:")
            print("\n  EMPLOYERS:")
            for user in self.created_users:
                if user.role == UserRole.EMPLOYER:
                    employer = next((e for e in self.created_employers if e.user_id == user.id), None)
                    if employer:
                        print(f"    • {employer.company_name}")
                        print(f"      Email: {user.email}")
                        print(f"      Password: (See seed script)")
            
            print("\n  EMPLOYEES:")
            for user in self.created_users:
                if user.role == UserRole.EMPLOYEE:
                    employee = next((e for e in self.created_employees if e.user_id == user.id), None)
                    if employee:
                        print(f"    • {employee.full_name} ({employee.current_job_title})")
                        print(f"      Email: {user.email}")
            
            print("\n💡 Next Steps:")
            print("  1. Login with any employer/employee credentials")
            print("  2. Test the AI chat with real context")
            print("  3. Use tools like job search, applications, etc.")
            print("  4. Monitor how agents handle real data")
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {str(e)}")
            self.db.rollback()
            raise
        finally:
            self.db.close()


if __name__ == "__main__":
    seeder = RealisticDataSeeder()
    
    print("\n🌱 SmartServe Realistic Data Seeder")
    print("="*70)
    print("\nThis script will populate your database with realistic, production-quality data.")
    print("\nOptions:")
    print("  1. Seed new data (preserves existing data)")
    print("  2. Clear ALL data and seed fresh (DESTRUCTIVE!)")
    print("  3. Exit")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == "1":
        seeder.seed_all(clear_first=False)
    elif choice == "2":
        seeder.seed_all(clear_first=True)
    else:
        print("❌ Exiting without changes.")
