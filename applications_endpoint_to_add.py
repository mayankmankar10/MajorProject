# Add this to the end of backend/routes/employee_routes.py

@router.get("/applications")
def get_employee_applications(user_id: Optional[int] = None):
    """
    Get all applications for an employee by user_id.
    Converts user_id to employee_id and fetches applications with job details.
    """
    db = SessionLocal()
    try:
        # If no user_id provided, return empty (in production, get from JWT)
        if not user_id:
            return []
        
        # Convert user_id to employee_id
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        if not employee:
            logger.warning(f"No employee found for user_id {user_id}")
            return []
        
        # Fetch applications with job and employer details
        applications = db.query(Application).filter(
            Application.employee_id == employee.id
        ).all()
        
        # Format response
        result = []
        for app in applications:
            result.append({
                "id": app.id,
                "job_id": app.job_id,
                "employee_id": app.employee_id,
                "status": app.status.value if app.status else "applied",
                "match_score": app.match_score or 0.0,
                "cover_letter": app.cover_letter,
                "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                "updated_at": app.updated_at.isoformat() if app.updated_at else None,
                "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None,
                "notes": app.notes,
                "job": {
                    "id": app.job.id,
                    "title": app.job.title,
                    "description": app.job.description,
                    "location": app.job.location,
                    "salary_range": app.job.salary_range,
                    "job_type": app.job.job_type.value if app.job.job_type else None,
                    "employer": {
                        "company_name": app.job.employer.company_name if app.job.employer else None
                    }
                } if app.job else None
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching applications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch applications: {str(e)}")
    finally:
        db.close()
