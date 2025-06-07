from sqlalchemy.orm import Session
from app.services.crud import UserCRUD
from app.services.goal_crud import GoalCRUD
from app.schemas.schemas import UserCreate
from app.models.users import User
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Extended user service that handles goal assignment"""
    
    @staticmethod
    def create_user_with_goals(db: Session, user_data: UserCreate) -> User:
        """Create a user and assign initial goals"""
        try:
            user = UserCRUD.create_user(db, user_data)
            
            try:
                goal_result = GoalCRUD.assign_goals_for_new_user(db, user.id)
                logger.info(f"Initial goals assigned to new user {user.id}: {goal_result}")
            except Exception as e:
                logger.warning(f"Failed to assign initial goals to user {user.id}: {str(e)}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error creating user with goals: {str(e)}")
            raise e
    
    @staticmethod
    def create_user_for_customer_with_goals(db: Session, user_data: UserCreate, customer_id: int) -> User:
        """Create a user for a customer and assign initial goals"""
        try:
            user = UserCRUD.create_user_for_customer(db, user_data, customer_id)
            
            try:
                goal_result = GoalCRUD.assign_goals_for_new_user(db, user.id)
                logger.info(f"Initial goals assigned to new customer user {user.id}: {goal_result}")
            except Exception as e:
                logger.warning(f"Failed to assign initial goals to customer user {user.id}: {str(e)}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error creating customer user with goals: {str(e)}")
            raise e
    
    @staticmethod
    def reassign_goals_for_user(db: Session, user_id: int) -> dict:
        """Manually reassign all goals for a user (admin function)"""
        try:
            result = GoalCRUD.assign_goals_for_new_user(db, user_id)
            logger.info(f"Goals reassigned for user {user_id}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error reassigning goals for user {user_id}: {str(e)}")
            raise e