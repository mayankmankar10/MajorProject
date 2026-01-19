# EMPLOYER ONBOARDING ENDPOINTS - ADDED FOR EMPLOYER ONBOARDING FEATURE

class EmployerProfileUpdate(BaseModel):
    company_profile: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

class HiringPreferenceItem(BaseModel):
    role: str
    positions: int
    location: str
    shift: str
    salary_min: int
    salary_max: int

class HiringPreferencesUpdate(BaseModel):
    preferences: List[HiringPreferenceItem]


@router.put("/profile")
def update_employer_profile(
    profile_data: EmployerProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update employer profile information."""
    try:
        user_id = current_user.get("user_id")
        
        # Get employer profile
        employer = db.query(Employer).filter(Employer.user_id == user_id).first()
        if not employer:
            raise HTTPException(status_code=404, detail="Employer profile not found")
        
        # Update fields
        if profile_data.company_profile is not None:
            employer.company_profile = profile_data.company_profile
        if profile_data.industry is not None:
            employer.industry = profile_data.industry
        if profile_data.location is not None:
            employer.location = profile_data.location
        if profile_data.website is not None:
            employer.website = profile_data.website
        
        db.commit()
        db.refresh(employer)
        
        logger.info(f"Employer profile updated for employer_id={employer.id}")
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "profile": {
                "company_name": employer.company_name,
                "company_profile": employer.company_profile,
                "industry": employer.industry,
                "location": employer.location,
                "website": employer.website
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating employer profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/hiring-preferences")
def set_hiring_preferences(
    preferences_data: HiringPreferencesUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set or update employer's hiring preferences/templates."""
    try:
        user_id = current_user.get("user_id")
        
        # Get employer profile
        employer = db.query(Employer).filter(Employer.user_id == user_id).first()
        if not employer:
            raise HTTPException(status_code=404, detail="Employer profile not found")
        
        # Convert Pydantic models to dict
        preferences_list = [pref.dict() for pref in preferences_data.preferences]
        
        # Validate at least one preference
        if not preferences_list:
            raise HTTPException(status_code=400, detail="At least one hiring preference required")
        
        # Validate salary ranges
        for pref in preferences_list:
            if pref['salary_max'] < pref['salary_min']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Max salary must be >= min salary for {pref['role']}"
                )
        
        # Update hiring preferences
        employer.hiring_preferences = preferences_list
        db.commit()
        db.refresh(employer)
        
        logger.info(f"Hiring preferences updated for employer_id={employer.id}, count={len(preferences_list)}")
        
        return {
            "success": True,
            "message": f"Saved {len(preferences_list)} hiring preference(s)",
            "preferences": employer.hiring_preferences
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating hiring preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/onboarding-status")
def get_employer_onboarding_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get employer onboarding completion status."""
    try:
        user_id = current_user.get("user_id")
        
        # Get employer profile
        employer = db.query(Employer).filter(Employer.user_id == user_id).first()
        if not employer:
            raise HTTPException(status_code=404, detail="Employer profile not found")
        
        # Check completion status for each step
        step1_complete = bool(
            employer.company_profile and 
            employer.industry and 
            employer.location
        )
        
        step2_complete = bool(
            employer.hiring_preferences and 
            len(employer.hiring_preferences) > 0
        )
        
        onboarding_complete = step1_complete and step2_complete
        
        return {
            "onboarding_complete": onboarding_complete,
            "steps": {
                "company_profile": step1_complete,
                "hiring_preferences": step2_complete
            },
            "profile": {
                "company_name": employer.company_name,
                "company_profile": employer.company_profile,
                "industry": employer.industry,
                "location": employer.location,
                "website": employer.website,
                "hiring_preferences": employer.hiring_preferences
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching onboarding status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
