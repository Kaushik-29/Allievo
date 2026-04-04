from app.core.database import SessionLocal
from app.models.worker import Worker
from app.core.security import create_access_token
import traceback
print("starting")
try:
    db = SessionLocal()
    contact = "9949781999"
    name = "Gig Worker"
    city = "Bengaluru"

    worker = db.query(Worker).filter(Worker.phone == contact).first()
    if not worker:
        print("creating worker")
        worker = Worker(
            phone=contact,
            name=name,
            city=city,
            language_pref="en"
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)
        print("created worker", worker.id)
        
    token = create_access_token({"sub": str(worker.id), "phone": worker.phone, "role": "worker"})
    print("generated token")
except Exception as e:
    with open("error.log", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())
finally:
    db.close()
