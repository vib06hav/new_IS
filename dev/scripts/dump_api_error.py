import json
import traceback
from fastapi.testclient import TestClient
from app.main import app

def dump_error():
    from app.database import SessionLocal
    from app.models.synthesis_record import SynthesisRecord
    from app.api.schemas import SynthesisOutput
    
    db = SessionLocal()
    records = db.query(SynthesisRecord).order_by(SynthesisRecord.created_at.desc()).limit(1).all()
    for rec in records:
        print("Record App ID:", rec.application_id)
        # print first keys
        print("Keys:", list(rec.synthesis_output.keys()))
        try:
            so = SynthesisOutput(**rec.synthesis_output)
            print("Pydantic load succeeded")
        except Exception as e:
            print("Pydantic Error:")
            if hasattr(e, 'json'):
                print(e.json())
            else:
                traceback.print_exc()

if __name__ == "__main__":
    dump_error()
