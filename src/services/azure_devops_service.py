"""
Azure DevOps integration service for work item management and reporting.

This service provides integration with Azure DevOps API for:
- Work item tracking and management
- Project reporting and analytics
- Task synchronization with scraping jobs
- Team productivity metrics
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
import base64
from dataclasses import dataclass, asdict
from enum import Enum

from config.app_config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WorkItemState(Enum):
    """Work item states in Azure DevOps"""
    NEW = "New"
    ACTIVE = "Active"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    REMOVED = "Removed"


class WorkItemType(Enum):
    """Work item types in Azure DevOps"""
    USER_STORY = "User Story"
    TASK = "Task"
    BUG = "Bug"
    FEATURE = "Feature"
    EPIC = "Epic"


@dataclass
class WorkItem:
    """Azure DevOps work item data structure"""
    id: int
    title: str
    work_item_type: str
    state: str
    assigned_to: Optional[str] = None
    description: Optional[str] = None
    story_points: Optional[int] = None
    iteration_path: Optional[str] = None
    area_path: Optional[str] = None
    created_date: Optional[str] = None
    changed_date: Optional[str] = None
    created_by: Optional[str] = None
    tags: Optional[str] = None
    priority: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert work item to dictionary"""
        return asdict(self)


@dataclass
class ProjectStats:
    """Project statistics from Azure DevOps"""
    project_name: str
    total_work_items: int
    active_work_items: int
    completed_work_items: int
    in_progress_work_items: int
    total_story_points: int
    completed_story_points: int
    team_members: List[str]
    last_updated: str


class AzureDevOpsService:
    """Service for Azure DevOps API integration"""
    
    def __init__(self):
        self.organization = getattr(settings, 'AZURE_DEVOPS_ORGANIZATION', 'centralgroup')
        self.pat_token = getattr(settings, 'AZURE_DEVOPS_PAT', None)
        self.base_url = f"https://dev.azure.com/{self.organization}"
        self.api_version = "7.0"
        
        if not self.pat_token:
            logger.warning("Azure DevOps PAT token not configured. Set AZURE_DEVOPS_PAT environment variable.")
        
        # Create authentication header
        self.auth_header = self._create_auth_header()
        
        # HTTP client with timeout and retry configuration
        # Temporarily clear proxy environment variables to avoid proxy parameter errors
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        original_values = {}
        
        try:
            # Save original values and clear proxy vars
            for var in proxy_vars:
                if var in os.environ:
                    original_values[var] = os.environ[var]
                    del os.environ[var]
            
            # Create client without proxy interference
            self.client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
            
        finally:
            # Restore original proxy environment variables
            for var, value in original_values.items():
                os.environ[var] = value
    
    def _create_auth_header(self) -> Dict[str, str]:
        """Create authentication header for Azure DevOps API"""
        if not self.pat_token:
            return {}
        
        # Azure DevOps uses basic auth with empty username and PAT as password
        auth_string = f":{self.pat_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        return {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json"
        }
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects in the organization"""
        try:
            url = f"{self.base_url}/_apis/projects?api-version={self.api_version}"
            
            response = await self.client.get(url, headers=self.auth_header)
            response.raise_for_status()
            
            data = response.json()
            return data.get("value", [])
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch projects: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching projects: {e}")
            raise
    
    async def get_work_items_by_query(self, project: str, wiql_query: str) -> List[WorkItem]:
        """Execute WIQL query and return work items"""
        try:
            # First, execute the query to get work item IDs
            query_url = f"{self.base_url}/{project}/_apis/wit/wiql?api-version={self.api_version}"
            query_payload = {"query": wiql_query}
            
            response = await self.client.post(
                query_url, 
                headers=self.auth_header,
                json=query_payload
            )
            response.raise_for_status()
            
            query_result = response.json()
            work_item_refs = query_result.get("workItems", [])
            
            if not work_item_refs:
                return []
            
            # Extract work item IDs
            work_item_ids = [str(item["id"]) for item in work_item_refs]
            
            # Fetch detailed work item information
            return await self.get_work_items_by_ids(project, work_item_ids)
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to execute WIQL query: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in WIQL query: {e}")
            raise
    
    async def get_work_items_by_ids(self, project: str, work_item_ids: List[str]) -> List[WorkItem]:
        """Get detailed work item information by IDs"""
        try:
            if not work_item_ids:
                return []
            
            # Azure DevOps API supports batch requests for up to 200 work items
            batch_size = 200
            all_work_items = []
            
            for i in range(0, len(work_item_ids), batch_size):
                batch_ids = work_item_ids[i:i + batch_size]
                ids_param = ",".join(batch_ids)
                
                url = f"{self.base_url}/{project}/_apis/wit/workitems"
                params = {
                    "ids": ids_param,
                    "api-version": self.api_version,
                    "$expand": "fields"
                }
                
                response = await self.client.get(url, headers=self.auth_header, params=params)
                response.raise_for_status()
                
                data = response.json()
                work_items_data = data.get("value", [])
                
                # Convert to WorkItem objects
                for item_data in work_items_data:
                    work_item = self._parse_work_item(item_data)
                    all_work_items.append(work_item)
            
            return all_work_items
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch work items by IDs: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching work items: {e}")
            raise
    
    def _parse_work_item(self, item_data: Dict[str, Any]) -> WorkItem:
        """Parse Azure DevOps work item data into WorkItem object"""
        fields = item_data.get("fields", {})
        
        # Extract assigned to user (handle both display name and unique name)
        assigned_to = None
        if "System.AssignedTo" in fields:
            assigned_to_data = fields["System.AssignedTo"]
            if isinstance(assigned_to_data, dict):
                assigned_to = assigned_to_data.get("displayName", assigned_to_data.get("uniqueName"))
            else:
                assigned_to = str(assigned_to_data)
        
        return WorkItem(
            id=item_data.get("id"),
            title=fields.get("System.Title", ""),
            work_item_type=fields.get("System.WorkItemType", ""),
            state=fields.get("System.State", ""),
            assigned_to=assigned_to,
            description=fields.get("System.Description", ""),
            story_points=fields.get("Microsoft.VSTS.Scheduling.StoryPoints"),
            iteration_path=fields.get("System.IterationPath"),
            area_path=fields.get("System.AreaPath"),
            created_date=fields.get("System.CreatedDate"),
            changed_date=fields.get("System.ChangedDate"),
            created_by=fields.get("System.CreatedBy", {}).get("displayName") if isinstance(fields.get("System.CreatedBy"), dict) else fields.get("System.CreatedBy"),
            tags=fields.get("System.Tags"),
            priority=fields.get("Microsoft.VSTS.Common.Priority")
        )
    
    async def get_active_work_items(self, project: str) -> List[WorkItem]:
        """Get all active work items for a project"""
        wiql_query = f"""
        SELECT [System.Id], [System.Title], [System.AssignedTo], [System.State], 
               [Microsoft.VSTS.Scheduling.StoryPoints], [System.IterationPath], 
               [System.WorkItemType], [System.Description], [System.Tags],
               [Microsoft.VSTS.Common.Priority]
        FROM WorkItems 
        WHERE [System.TeamProject] = '{project}' 
        AND [System.State] IN ('Active', 'In Progress', 'New')
        ORDER BY [System.Id] DESC
        """
        
        return await self.get_work_items_by_query(project, wiql_query)
    
    async def get_completed_work_items(self, project: str, days_back: int = 30) -> List[WorkItem]:
        """Get completed work items within the specified time period"""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        wiql_query = f"""
        SELECT [System.Id], [System.Title], [System.AssignedTo], [System.State], 
               [Microsoft.VSTS.Scheduling.StoryPoints], [System.IterationPath], 
               [System.WorkItemType], [System.ChangedDate]
        FROM WorkItems 
        WHERE [System.TeamProject] = '{project}' 
        AND [System.State] IN ('Resolved', 'Closed', 'Done')
        AND [System.ChangedDate] >= '{cutoff_date}'
        ORDER BY [System.ChangedDate] DESC
        """
        
        return await self.get_work_items_by_query(project, wiql_query)
    
    async def get_project_statistics(self, project: str) -> ProjectStats:
        """Get comprehensive project statistics"""
        try:
            # Get all work items for the project
            all_items_query = f"""
            SELECT [System.Id], [System.Title], [System.AssignedTo], [System.State], 
                   [Microsoft.VSTS.Scheduling.StoryPoints], [System.WorkItemType]
            FROM WorkItems 
            WHERE [System.TeamProject] = '{project}'
            """
            
            all_work_items = await self.get_work_items_by_query(project, all_items_query)
            
            # Calculate statistics
            total_items = len(all_work_items)
            active_items = len([item for item in all_work_items if item.state in ['Active', 'In Progress', 'New']])
            completed_items = len([item for item in all_work_items if item.state in ['Resolved', 'Closed', 'Done']])
            in_progress_items = len([item for item in all_work_items if item.state == 'In Progress'])
            
            # Calculate story points
            total_story_points = sum(item.story_points or 0 for item in all_work_items)
            completed_story_points = sum(
                item.story_points or 0 for item in all_work_items 
                if item.state in ['Resolved', 'Closed', 'Done']
            )
            
            # Get unique team members
            team_members = list(set(
                item.assigned_to for item in all_work_items 
                if item.assigned_to and item.assigned_to.strip()
            ))
            
            return ProjectStats(
                project_name=project,
                total_work_items=total_items,
                active_work_items=active_items,
                completed_work_items=completed_items,
                in_progress_work_items=in_progress_items,
                total_story_points=total_story_points,
                completed_story_points=completed_story_points,
                team_members=team_members,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to get project statistics: {e}")
            raise
    
    async def create_work_item(self, project: str, work_item_type: WorkItemType, 
                             title: str, description: str = "", assigned_to: str = None,
                             story_points: int = None, tags: str = None) -> WorkItem:
        """Create a new work item in Azure DevOps"""
        try:
            url = f"{self.base_url}/{project}/_apis/wit/workitems/${work_item_type.value}?api-version={self.api_version}"
            
            # Build the patch document for creating work item
            patch_document = [
                {
                    "op": "add",
                    "path": "/fields/System.Title",
                    "value": title
                }
            ]
            
            if description:
                patch_document.append({
                    "op": "add",
                    "path": "/fields/System.Description",
                    "value": description
                })
            
            if assigned_to:
                patch_document.append({
                    "op": "add",
                    "path": "/fields/System.AssignedTo",
                    "value": assigned_to
                })
            
            if story_points:
                patch_document.append({
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.Scheduling.StoryPoints",
                    "value": story_points
                })
            
            if tags:
                patch_document.append({
                    "op": "add",
                    "path": "/fields/System.Tags",
                    "value": tags
                })
            
            headers = self.auth_header.copy()
            headers["Content-Type"] = "application/json-patch+json"
            
            response = await self.client.post(url, headers=headers, json=patch_document)
            response.raise_for_status()
            
            work_item_data = response.json()
            return self._parse_work_item(work_item_data)
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to create work item: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating work item: {e}")
            raise
    
    async def update_work_item_state(self, project: str, work_item_id: int, 
                                   new_state: WorkItemState) -> bool:
        """Update work item state"""
        try:
            url = f"{self.base_url}/{project}/_apis/wit/workitems/{work_item_id}?api-version={self.api_version}"
            
            patch_document = [
                {
                    "op": "replace",
                    "path": "/fields/System.State",
                    "value": new_state.value
                }
            ]
            
            headers = self.auth_header.copy()
            headers["Content-Type"] = "application/json-patch+json"
            
            response = await self.client.patch(url, headers=headers, json=patch_document)
            response.raise_for_status()
            
            return True
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to update work item state: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating work item: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Singleton instance for global use
_azure_devops_service = None

def get_azure_devops_service() -> AzureDevOpsService:
    """Get or create Azure DevOps service instance"""
    global _azure_devops_service
    if _azure_devops_service is None:
        _azure_devops_service = AzureDevOpsService()
    return _azure_devops_service