"""
Follow-Up Task Management Service for FollowUp
Coordinates task assignments, progress tracking, deadline monitoring,
and healthcare worker action notes.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple

import config
from database.connection import execute_query, execute_single, execute_statement
from utils.security import generate_reference
from utils.helpers import parse_iso_date
from services.validation_service import validate_task_input
from services.auth_service import log_audit_action

def get_next_task_ref() -> str:
    """Generate sequential standardized task reference."""
    row = execute_single("SELECT MAX(id) as max_id FROM tasks")
    next_id = (row["max_id"] or 0) + 1
    return generate_reference("TSK", next_id, year=2026)

def create_task(patient_id: int,
                title: str,
                description: str,
                assigned_to: str,
                assigned_by: str,
                priority: str,
                due_date_str: str,
                actor_username: str = "system",
                actor_role: str = "Healthcare Provider",
                is_demo: int = 0) -> Tuple[bool, str, Optional[str]]:
    """Create a new follow-up task assigned to a healthcare worker or officer."""
    is_valid, err = validate_task_input(title, assigned_to, due_date_str)
    if not is_valid:
        return False, err, None
        
    task_ref = get_next_task_ref()
    now_str = datetime.now().isoformat()
    
    try:
        execute_statement(
            """
            INSERT INTO tasks (
                task_ref, patient_id, title, description, assigned_to, assigned_by,
                priority, status, due_date, is_demo, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?, ?)
            """,
            (
                task_ref, patient_id, title.strip(), description.strip(),
                assigned_to.strip(), assigned_by.strip(), priority,
                due_date_str, is_demo, now_str, now_str
            )
        )
        
        log_audit_action(
            username=actor_username,
            role=actor_role,
            action="TASK_CREATE",
            target_type="Task",
            target_ref=task_ref,
            details=f"Assigned task '{title}' to {assigned_to} with deadline {due_date_str}."
        )
        
        return True, f"Task {task_ref} created successfully.", task_ref
    except Exception as e:
        return False, f"Database error creating task: {str(e)}", None

def update_task_status(task_id: int,
                       new_status: str,
                       action_taken: Optional[str] = None,
                       actor_username: str = "system",
                       actor_role: str = "Healthcare Provider") -> Tuple[bool, str]:
    """Update task status and record action taken."""
    if new_status not in config.ALL_TASK_STATUSES:
        return False, "Invalid task status."
        
    now_str = datetime.now().isoformat()
    comp_date = date.today().isoformat() if new_status == config.TASK_STATUS_COMPLETED else None
    
    try:
        execute_statement(
            """
            UPDATE tasks SET
                status = ?, action_taken = COALESCE(?, action_taken),
                completion_date = COALESCE(?, completion_date),
                updated_at = ?
            WHERE id = ?
            """,
            (new_status, action_taken.strip() if action_taken else None, comp_date, now_str, task_id)
        )
        
        log_audit_action(
            username=actor_username,
            role=actor_role,
            action="TASK_UPDATE",
            target_type="Task",
            target_ref=str(task_id),
            details=f"Updated task status to {new_status}."
        )
        return True, "Task updated successfully."
    except Exception as e:
        return False, f"Database error updating task: {str(e)}"

def list_tasks(patient_id: Optional[int] = None,
               assigned_to: Optional[str] = None,
               status: Optional[str] = None,
               priority: Optional[str] = None,
               only_overdue: bool = False) -> List[Dict[str, Any]]:
    """Retrieve tasks with patient details and deadline calculations."""
    sql = """
        SELECT t.*, p.patient_ref, p.full_name as patient_name, p.condition_category,
               p.phone_number as patient_phone, f.name as facility_name
        FROM tasks t
        JOIN patients p ON t.patient_id = p.id
        JOIN facilities f ON p.facility_id = f.id
        WHERE 1=1
    """
    params = []
    
    if patient_id:
        sql += " AND t.patient_id = ?"
        params.append(patient_id)
        
    if assigned_to and assigned_to != "All Assignees":
        sql += " AND t.assigned_to = ?"
        params.append(assigned_to)
        
    if status and status != "All Statuses":
        sql += " AND t.status = ?"
        params.append(status)
        
    if priority and priority != "All Priorities":
        sql += " AND t.priority = ?"
        params.append(priority)
        
    sql += " ORDER BY t.due_date ASC, t.id DESC"
    
    rows = execute_query(sql, tuple(params))
    today_str = date.today().isoformat()
    
    results = []
    for r in rows:
        d = dict(r)
        d["is_overdue"] = (d["status"] in ["Pending", "In Progress"]) and (d["due_date"] < today_str)
        if only_overdue and not d["is_overdue"]:
            continue
        results.append(d)
        
    return results
