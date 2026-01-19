"""
Generate documents for a specific offer
"""

import sqlite3
from pathlib import Path
import sys

DB_PATH = Path(__file__).parent / "manpower.db"

def generate_docs_for_offer(offer_id: int):
    """Generate offer letter and NDA for a specific offer"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get offer details
        cursor.execute("""
            SELECT o.id, o.employee_id, o.employer_id, o.job_id, o.salary, o.start_date,
                   e.full_name as employee_name, emp.company_name as employer_name,
                   j.title as job_title
            FROM offers o
            JOIN employees e ON o.employee_id = e.id
            JOIN employers emp ON o.employer_id = emp.id
            LEFT JOIN jobs j ON o.job_id = j.id
            WHERE o.id = ?
        """, (offer_id,))
        
        offer = cursor.fetchone()
        
        if not offer:
            print(f"Offer {offer_id} not found")
            return
        
        print(f"Offer Details:")
        print(f"  ID: {offer[0]}")
        print(f"  Employee: {offer[6]}")
        print(f"  Employer: {offer[7]}")
        print(f"  Job: {offer[8]}")
        print(f"  Salary: {offer[4]}")
        print(f"  Start Date: {offer[5]}")
        
        # Generate offer letter
        offer_letter = f"""
OFFER LETTER

Dear {offer[6]},

We are pleased to offer you the position of {offer[8]} at {offer[7]}.

Position: {offer[8]}
Salary: Rs. {offer[4]:,}
Start Date: {offer[5]}

We look forward to having you join our team.

Sincerely,
{offer[7]}
"""
        
        # Generate NDA
        nda = f"""
NON-DISCLOSURE AGREEMENT

This Agreement is entered into between {offer[7]} ("Company") and {offer[6]} ("Employee").

The Employee agrees to maintain confidentiality of all proprietary information.

Signed: _______________
Date: {offer[5]}
"""
        
        # Update database
        cursor.execute("""
            UPDATE offers 
            SET offer_letter_content = ?, nda_content = ?
            WHERE id = ?
        """, (offer_letter, nda, offer_id))
        
        conn.commit()
        print(f"\n✓ Successfully generated documents for offer {offer_id}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        offer_id = int(sys.argv[1])
    else:
        offer_id = int(input("Enter offer ID: "))
    
    generate_docs_for_offer(offer_id)
