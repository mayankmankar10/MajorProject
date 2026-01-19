"""
Restaurant Job Templates - Pre-defined templates for common restaurant positions
Used by JobDescriptionEnhancer and BulkHiringWorkflow
"""

RESTAURANT_JOB_TEMPLATES = {
    "waiter": {
        "title": "Waiter/Server",
        "base_description": "Responsible for taking customer orders, serving food and beverages, ensuring excellent dining experience, and maintaining table cleanliness.",
        "required_skills": ["customer service", "multitasking", "communication", "menu knowledge", "POS systems"],
        "preferred_certifications": ["Food Safety Certification"],
        "min_experience": 0,
        "max_experience": 3,
        "job_category": "waiter",
        "shift_types": ["morning", "afternoon", "evening"],
        "requires_food_safety": True,
        "requires_alcohol_cert": False
    },
    
    "cook": {
        "title": "Line Cook",
        "base_description": "Prepare dishes according to recipes and chef specifications, maintain kitchen cleanliness, assist with food preparation, and ensure food quality standards.",
        "required_skills": ["cooking", "knife skills", "food preparation", "sanitation", "recipe following"],
        "preferred_certifications": ["Food Safety Certification", "ServSafe"],
        "min_experience": 1,
        "max_experience": 5,
        "job_category": "cook",
        "shift_types": ["morning", "afternoon", "evening"],
        "requires_food_safety": True,
        "requires_alcohol_cert": False
    },
    
    "chef": {
        "title": "Executive Chef",
        "base_description": "Oversee kitchen operations, menu planning and development, staff management and training, inventory control, and maintain quality standards across all dishes.",
        "required_skills": ["menu planning", "leadership", "cost control", "creativity", "team management", "food safety"],
        "preferred_certifications": ["Culinary Degree", "ServSafe Manager", "Food Safety Certification"],
        "min_experience": 5,
        "max_experience": None,
        "job_category": "chef",
        "shift_types": ["morning", "afternoon", "evening"],
        "requires_food_safety": True,
        "requires_alcohol_cert": False
    },
    
    "bartender": {
        "title": "Bartender",
        "base_description": "Mix and serve alcoholic and non-alcoholic beverages, handle cash transactions, maintain bar cleanliness, engage with customers, and ensure responsible alcohol service.",
        "required_skills": ["mixology", "customer service", "cash handling", "multitasking", "drink recipes"],
        "preferred_certifications": ["Alcohol Service Certification", "Food Safety Certification", "Mixology Certificate"],
        "min_experience": 0,
        "max_experience": 4,
        "job_category": "bartender",
        "shift_types": ["afternoon", "evening", "night"],
        "requires_food_safety": True,
        "requires_alcohol_cert": True
    },
    
    "host": {
        "title": "Host/Hostess",
        "base_description": "Greet and seat guests, manage reservations and waitlists, coordinate seating arrangements, answer phone calls, and ensure smooth front-of-house operations.",
        "required_skills": ["customer service", "organization", "communication", "phone etiquette", "multitasking"],
        "preferred_certifications": [],
        "min_experience": 0,
        "max_experience": 2,
        "job_category": "host",
        "shift_types": ["morning", "afternoon", "evening"],
        "requires_food_safety": False,
        "requires_alcohol_cert": False
    },
    
    "dishwasher": {
        "title": "Dishwasher",
        "base_description": "Wash dishes, utensils, and kitchen equipment, maintain cleanliness of dishwashing area, support kitchen staff, and ensure proper sanitation procedures.",
        "required_skills": ["sanitation", "speed", "reliability", "physical stamina"],
        "preferred_certifications": ["Food Safety Certification"],
        "min_experience": 0,
        "max_experience": 2,
        "job_category": "dishwasher",
        "shift_types": ["morning", "afternoon", "evening", "night"],
        "requires_food_safety": True,
        "requires_alcohol_cert": False
    }
}

# Common cuisine types for reference
CUISINE_TYPES = [
    "Italian",
    "Chinese",
    "Indian",
    "Mexican",
    "Japanese",
    "Thai",
    "French",
    "American",
    "Mediterranean",
    "Continental",
    "Fusion"
]

# Common shift types
SHIFT_TYPES = [
    "morning",      # 6am-2pm
    "afternoon",    # 2pm-6pm
    "evening",      # 6pm-11pm
    "night",        # 11pm-6am
    "weekends",
    "flexible"
]

def get_template(job_type: str) -> dict:
    """
    Get template for a specific job type.
    
    Args:
        job_type: One of 'waiter', 'cook', 'chef', 'bartender', 'host', 'dishwasher'
    
    Returns:
        Template dict or None if not found
    """
    return RESTAURANT_JOB_TEMPLATES.get(job_type.lower())

def get_all_templates() -> dict:
    """Get all available templates."""
    return RESTAURANT_JOB_TEMPLATES

def enhance_template(job_type: str, **custom_fields) -> dict:
    """
    Get template and enhance with custom fields.
    
    Example:
        enhance_template('waiter', 
                        location='Mumbai', 
                        cuisine_type='Italian',
                        shift_type='evening')
    """
    template = get_template(job_type)
    if not template:
        return None
    
    # Create a copy to avoid modifying original
    enhanced = template.copy()
    
    # Merge custom fields
    enhanced.update(custom_fields)
    
    # Enhanced description with context
    if 'location' in custom_fields or 'cuisine_type' in custom_fields:
        location = custom_fields.get('location', '')
        cuisine = custom_fields.get('cuisine_type', '')
        
        desc_additions = []
        if cuisine:
            desc_additions.append(f"specializing in {cuisine} cuisine")
        if location:
            desc_additions.append(f"located in {location}")
        
        if desc_additions:
            enhanced['enhanced_description'] = f"{template['base_description']} " + ", ".join(desc_additions) + "."
    
    return enhanced
