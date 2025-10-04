"""
Background cleanup scheduler for AI Coaching application
Handles automatic cleanup of expired sessions and orphaned resources
"""

import asyncio
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

from backend.database.connection import get_db
from backend.database.models import ChatSession
from backend.database.chat_memory import ChatMemoryService
from backend.assistant.utils import delete_vector_store

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CleanupScheduler:
    """
    Handles scheduled cleanup tasks for the AI Coaching system
    """
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        
    def _cleanup_session_with_vector_store(self, session_id: str) -> Dict:
        """
        Internal method to cleanup a session and its vector store
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict with cleanup results
        """
        cleanup_result = {
            "session_deleted": False,
            "vector_store_deleted": False,
            "messages_deleted": 0,
            "errors": []
        }
        
        try:
            db = next(get_db())
            memory_service = ChatMemoryService(db)
            
            # Get session info
            session = memory_service.get_session(session_id)
            if not session:
                cleanup_result["errors"].append(f"Session not found: {session_id}")
                db.close()
                return cleanup_result
            
            vector_store_id = session.vector_store_id
            
            # Get message count
            messages = memory_service.get_chat_history(session_id)
            cleanup_result["messages_deleted"] = len(messages)
            
            # Delete session (cascade will delete messages)
            success = memory_service.delete_session(session_id)
            cleanup_result["session_deleted"] = success
            
            db.close()
            
            # Clean up vector store if exists
            if vector_store_id:
                try:
                    vector_store_deleted = delete_vector_store(vector_store_id)
                    cleanup_result["vector_store_deleted"] = vector_store_deleted
                    if not vector_store_deleted:
                        cleanup_result["errors"].append("Failed to delete vector store")
                except Exception as e:
                    cleanup_result["errors"].append(f"Error deleting vector store: {str(e)}")
            
        except Exception as e:
            cleanup_result["errors"].append(f"Error during session cleanup: {str(e)}")
        
        return cleanup_result
    
    def _cleanup_orphaned_resources(self) -> Dict:
        """
        Internal method to clean up orphaned resources
        
        Returns:
            Dict with cleanup statistics
        """
        try:
            db = next(get_db())
            memory_service = ChatMemoryService(db)
            
            # Get all sessions
            all_sessions = memory_service.get_all_sessions()
            
            cleanup_stats = {
                "sessions_checked": len(all_sessions),
                "orphaned_sessions_cleaned": 0,
                "vector_stores_cleaned": 0,
                "errors": []
            }
            
            # For now, just return the stats without detailed orphan checking
            # In a full implementation, you would check if vector stores actually exist
            db.close()
            return cleanup_stats
            
        except Exception as e:
            return {
                "error": f"Failed to cleanup orphaned resources: {str(e)}",
                "sessions_checked": 0,
                "orphaned_sessions_cleaned": 0,
                "vector_stores_cleaned": 0,
                "errors": [str(e)]
            }
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> Dict:
        """
        Clean up sessions that are older than max_age_hours
        
        Args:
            max_age_hours: Maximum age of sessions before cleanup (default: 24 hours)
            
        Returns:
            Dict with cleanup statistics
        """
        logger.info(f"Starting cleanup of sessions older than {max_age_hours} hours")
        
        cleanup_stats = {
            "expired_sessions_found": 0,
            "expired_sessions_cleaned": 0,
            "errors": []
        }
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            db = next(get_db())
            expired_sessions = db.query(ChatSession).filter(
                ChatSession.updated_at < cutoff_time,
                ChatSession.is_active == True
            ).all()
            
            cleanup_stats["expired_sessions_found"] = len(expired_sessions)
            logger.info(f"Found {len(expired_sessions)} expired sessions")
            
            for session in expired_sessions:
                try:
                    logger.info(f"Cleaning up expired session: {session.session_id} (last updated: {session.updated_at})")
                    result = self._cleanup_session_with_vector_store(session.session_id)
                    
                    if result.get("session_deleted", False):
                        cleanup_stats["expired_sessions_cleaned"] += 1
                        logger.info(f"✅ Successfully cleaned up session: {session.session_id}")
                    else:
                        error_msg = f"Failed to clean up session: {session.session_id}"
                        cleanup_stats["errors"].append(error_msg)
                        logger.warning(f"⚠️ {error_msg}")
                        
                except Exception as e:
                    error_msg = f"Error cleaning up session {session.session_id}: {str(e)}"
                    cleanup_stats["errors"].append(error_msg)
                    logger.error(f"❌ {error_msg}")
            
            db.close()
            
        except Exception as e:
            error_msg = f"Error during expired session cleanup: {str(e)}"
            cleanup_stats["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        logger.info(f"Expired session cleanup completed: {cleanup_stats['expired_sessions_cleaned']}/{cleanup_stats['expired_sessions_found']} sessions cleaned")
        return cleanup_stats
    
    def cleanup_inactive_sessions(self, max_inactive_hours: int = 6) -> Dict:
        """
        Clean up sessions that have been inactive for max_inactive_hours
        
        Args:
            max_inactive_hours: Maximum inactivity time before cleanup (default: 6 hours)
            
        Returns:
            Dict with cleanup statistics
        """
        logger.info(f"Starting cleanup of sessions inactive for more than {max_inactive_hours} hours")
        
        cleanup_stats = {
            "inactive_sessions_found": 0,
            "inactive_sessions_cleaned": 0,
            "errors": []
        }
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_inactive_hours)
            
            db = next(get_db())
            # Find sessions that haven't had any recent messages
            inactive_sessions = db.query(ChatSession).filter(
                ChatSession.updated_at < cutoff_time,
                ChatSession.is_active == True
            ).all()
            
            # Additional check: ensure no recent messages
            truly_inactive = []
            for session in inactive_sessions:
                if session.messages:
                    latest_message = max(session.messages, key=lambda msg: msg.timestamp)
                    if latest_message.timestamp < cutoff_time:
                        truly_inactive.append(session)
                else:
                    # No messages at all, consider inactive
                    truly_inactive.append(session)
            
            cleanup_stats["inactive_sessions_found"] = len(truly_inactive)
            logger.info(f"Found {len(truly_inactive)} truly inactive sessions")
            
            for session in truly_inactive:
                try:
                    logger.info(f"Cleaning up inactive session: {session.session_id} (last activity: {session.updated_at})")
                    result = self._cleanup_session_with_vector_store(session.session_id)
                    
                    if result.get("session_deleted", False):
                        cleanup_stats["inactive_sessions_cleaned"] += 1
                        logger.info(f"✅ Successfully cleaned up inactive session: {session.session_id}")
                    else:
                        error_msg = f"Failed to clean up inactive session: {session.session_id}"
                        cleanup_stats["errors"].append(error_msg)
                        logger.warning(f"⚠️ {error_msg}")
                        
                except Exception as e:
                    error_msg = f"Error cleaning up inactive session {session.session_id}: {str(e)}"
                    cleanup_stats["errors"].append(error_msg)
                    logger.error(f"❌ {error_msg}")
            
            db.close()
            
        except Exception as e:
            error_msg = f"Error during inactive session cleanup: {str(e)}"
            cleanup_stats["errors"].append(error_msg)
            logger.error(f"❌ {error_msg}")
        
        logger.info(f"Inactive session cleanup completed: {cleanup_stats['inactive_sessions_cleaned']}/{cleanup_stats['inactive_sessions_found']} sessions cleaned")
        return cleanup_stats
    
    def run_full_cleanup(self) -> Dict:
        """
        Run a comprehensive cleanup including:
        - Orphaned resources
        - Expired sessions  
        - Inactive sessions
        
        Returns:
            Dict with combined cleanup statistics
        """
        logger.info("Starting full system cleanup...")
        
        combined_stats = {
            "orphaned_cleanup": {},
            "expired_cleanup": {},
            "inactive_cleanup": {},
            "total_errors": 0,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None
        }
        
        try:
            # 1. Clean up orphaned resources
            logger.info("Phase 1: Cleaning up orphaned resources...")
            combined_stats["orphaned_cleanup"] = self._cleanup_orphaned_resources()
            
            # 2. Clean up expired sessions (older than 24 hours)
            logger.info("Phase 2: Cleaning up expired sessions...")
            combined_stats["expired_cleanup"] = self.cleanup_expired_sessions(max_age_hours=24)
            
            # 3. Clean up inactive sessions (inactive for more than 6 hours)
            logger.info("Phase 3: Cleaning up inactive sessions...")
            combined_stats["inactive_cleanup"] = self.cleanup_inactive_sessions(max_inactive_hours=6)
            
            # Count total errors
            combined_stats["total_errors"] = (
                len(combined_stats["orphaned_cleanup"].get("errors", [])) +
                len(combined_stats["expired_cleanup"].get("errors", [])) +
                len(combined_stats["inactive_cleanup"].get("errors", []))
            )
            
        except Exception as e:
            logger.error(f"❌ Error during full cleanup: {str(e)}")
            combined_stats["total_errors"] += 1
        
        combined_stats["end_time"] = datetime.utcnow().isoformat()
        logger.info(f"Full cleanup completed with {combined_stats['total_errors']} total errors")
        return combined_stats
    
    def schedule_cleanup_tasks(self):
        """
        Schedule regular cleanup tasks
        """
        # Run orphaned resource cleanup every 2 hours
        schedule.every(2).hours.do(self._safe_run, self._cleanup_orphaned_resources)
        
        # Run inactive session cleanup every 3 hours
        schedule.every(3).hours.do(self._safe_run, self.cleanup_inactive_sessions, max_inactive_hours=6)
        
        # Run expired session cleanup every 6 hours
        schedule.every(6).hours.do(self._safe_run, self.cleanup_expired_sessions, max_age_hours=24)
        
        # Run full cleanup daily at 2 AM
        schedule.every().day.at("02:00").do(self._safe_run, self.run_full_cleanup)
        
        logger.info("Cleanup tasks scheduled successfully")
    
    def _safe_run(self, func, *args, **kwargs):
        """
        Safely run a function with error handling
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ Error in scheduled task {func.__name__}: {str(e)}")
    
    def start_scheduler(self):
        """
        Start the background scheduler
        """
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.schedule_cleanup_tasks()
        
        def run_scheduler():
            logger.info("Starting cleanup scheduler thread...")
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            logger.info("Cleanup scheduler thread stopped")
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Cleanup scheduler started successfully")
    
    def stop_scheduler(self):
        """
        Stop the background scheduler
        """
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        logger.info("Cleanup scheduler stopped successfully")

# Global instance
cleanup_scheduler = CleanupScheduler()

def start_cleanup_scheduler():
    """
    Start the global cleanup scheduler
    """
    cleanup_scheduler.start_scheduler()

def stop_cleanup_scheduler():
    """
    Stop the global cleanup scheduler
    """
    cleanup_scheduler.stop_scheduler()

def manual_cleanup() -> Dict:
    """
    Manually trigger a full cleanup
    """
    return cleanup_scheduler.run_full_cleanup()