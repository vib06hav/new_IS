import os
import sys
import logging

# Configure root logger for debug script
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.canonical_record import CanonicalRecord
from app.projection.ros_projector import project_ros
from app.agents.synthesis_agent import run_synthesis_agent
from app.policy.guard import validate_synthesis_output

def replay_last_failed():
    engine = create_engine('postgresql://postgres:postgres_password@db/ag_db', connect_args={'options': '-c timezone=utc'})
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Get the latest CanonicalRecord
    record = db.query(CanonicalRecord).order_by(CanonicalRecord.created_at.desc()).first()
    if not record:
        logger.error("No CanonicalRecord found in DB!")
        return
        
    logger.info(f"Replaying Application ID: {record.application_id}")
    
    canonical_data = record.canonical_data
    
    try:
        # 1. Project ROS
        page_1, page_2, page_3, annotated_canonical, entity_map = project_ros(canonical_data)
        logger.info("ROS Projection successful.")
        
        # 2. Synthesis 
        synthesis_output_raw = run_synthesis_agent(annotated_canonical)
        
        # 3. Validate
        validation_result = validate_synthesis_output(synthesis_output_raw, entity_map, sanitize=True)
        
        if validation_result.get("passed"):
            logger.info("Validation PASSED (Unexpected!)")
        else:
            logger.error("Validation FAILED (Expected!)")
            
    except Exception as e:
        logger.exception(f"Exception during replay: {e}")

if __name__ == "__main__":
    replay_last_failed()
