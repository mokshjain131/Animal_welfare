"""Quick Module 1 verification script."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.database import get_engine, create_all_tables
engine = get_engine()
print(f"Engine: {engine.url}")

create_all_tables()
print("create_all_tables() OK")

from sqlalchemy.orm import Session
from db.models import Article
from datetime import datetime, timezone

with Session(engine) as session:
    test = Article(
        url="https://test.example.com/article-1",
        title="Test Article",
        full_text="This is a test article about animal welfare.",
        source_name="Test Source",
        source_type="rss",
        published_at=datetime.now(timezone.utc),
    )
    session.add(test)
    session.commit()
    print(f"Inserted article id={test.id}")

    row = session.query(Article).filter_by(id=test.id).first()
    print(f"Retrieved: id={row.id}, title='{row.title}', is_processed={row.is_processed}")

    session.delete(row)
    session.commit()
    print("Test row deleted. Module 1 verified!")
