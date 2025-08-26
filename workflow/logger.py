import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class ActivityLogger:
    
    def __init__(self, log_file: str = "data/timeline/activity.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, action: str, email_id: str, message: str, details: Optional[Dict] = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "email_id": email_id,
            "message": message
        }
        
        if details:
            log_entry["details"] = details
        
        # Append to JSONL file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_recent_activities(self, limit: int = 10) -> list:
        activities = []
        
        if not self.log_file.exists():
            return activities
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            for line in recent_lines:
                try:
                    activity = json.loads(line.strip())
                    activities.append(activity)
                except json.JSONDecodeError:
                    continue  
        
        return activities
    
    def get_activities_by_email(self, email_id: str) -> list:
        activities = []
        
        if not self.log_file.exists():
            return activities
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    activity = json.loads(line.strip())
                    if activity.get("email_id") == email_id:
                        activities.append(activity)
                except json.JSONDecodeError:
                    continue
        
        return activities
    
    def get_activities_by_action(self, action: str) -> list:
        activities = []
        
        if not self.log_file.exists():
            return activities
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    activity = json.loads(line.strip())
                    if activity.get("action") == action:
                        activities.append(activity)
                except json.JSONDecodeError:
                    continue
        
        return activities
    
    def get_summary_stats(self) -> Dict:
        stats = {
            "total_entries": 0,
            "actions": {},
            "email_ids": set(),
            "errors": 0
        }
        
        if not self.log_file.exists():
            return stats
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    activity = json.loads(line.strip())
                    stats["total_entries"] += 1
                    
                    action = activity.get("action", "unknown")
                    stats["actions"][action] = stats["actions"].get(action, 0) + 1
                    
                    email_id = activity.get("email_id", "unknown")
                    stats["email_ids"].add(email_id)
                    
                    if action == "error":
                        stats["errors"] += 1
                        
                except json.JSONDecodeError:
                    stats["errors"] += 1
                    continue
        
        # Convert set to list for JSON serialization
        stats["email_ids"] = list(stats["email_ids"])
        stats["unique_emails"] = len(stats["email_ids"])
        
        return stats
    
    def clear_log(self):
        """Clear the activity log (use with caution)."""
        if self.log_file.exists():
            self.log_file.unlink()
    
    def export_log(self, output_file: str, format: str = "jsonl"):
        """Export log to different formats."""
        if format == "jsonl":
            # Simple copy
            import shutil
            shutil.copy2(self.log_file, output_file)
        
        elif format == "json":
            # Export as JSON array
            activities = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        activity = json.loads(line.strip())
                        activities.append(activity)
                    except json.JSONDecodeError:
                        continue
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(activities, f, indent=2)
        
        elif format == "csv":
            # Export as CSV
            import csv
            activities = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        activity = json.loads(line.strip())
                        activities.append(activity)
                    except json.JSONDecodeError:
                        continue
            
            if activities:
                fieldnames = activities[0].keys()
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(activities)
