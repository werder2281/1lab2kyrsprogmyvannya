import os
import sys


users = {
    "devsecops_lead": {"role": "devsecops", "clearance": 4, "department": "DevSecOps", "active": True},
    "security_engineer": {"role": "security_engineer", "clearance": 3, "department": "Security Engineering", "active": True},
    "automation_tech": {"role": "automation", "clearance": 2, "department": "Automation", "active": True},
    "api_developer": {"role": "api_developer", "clearance": 2, "department": "API", "active": True},
    "sandbox_env": {"role": "sandbox", "clearance": 1, "department": "Testing", "active": False},
}

blocked_users = {"sandbox_env", "pipeline_breach", "automation_fail"}

resources = [
    ("security_pipelines", 4),
    ("secure_coding_standards", 3),
    ("automation_scripts", 2),
    ("api_specifications", 2),
    ("threat_models", 4),
    ("testing_frameworks", 1),
    ("security_gates", 3),
    ("vulnerability_scans", 4),
    ("integration_tests", 2),
    ("mock_services", 1),
]
security_levels = ("Sandbox", "Development", "Secure", "Production Critical")




def print_resources():
    for name, level in resources:
        level_name = security_levels[level - 1]
        print(f"{name} : {level_name} (рівень {level})")


def check_access(username, resource_level):
    if username not in users:
        return False, "User not found"

    if username in blocked_users:
        return False, "User is blocked"

    if username in users and not users[username]["active"]:
        return False, "Account inactive"
    if users[username]["clearance"] >= resource_level:
        return True,None

    return False, "Insufficient clearance"

def run_checks():
    for username in users:
        for resource_name, resource_level in resources:
            allowed, reason = check_access(username, resource_level)    
            if allowed == True:
               print(f"user={username} resource={resource_name} -> ALLOW")
            else:
                print(f"user={username} resource={resource_name} -> DENY: ({reason})")


print_resources()   
run_checks()
