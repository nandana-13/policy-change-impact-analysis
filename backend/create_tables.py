from app.database import Base, engine

# Import all models so SQLAlchemy knows about every table
from app.models import (
    User,
    Policy,
    PolicyVersion,
    RegulatoryChange,
    PolicyRelationship,
    ImpactGroundTruth,
)


print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print()
print("Database tables created successfully.")
print()
print("Tables created:")
print(" - users")
print(" - policies")
print(" - policy_versions")
print(" - regulatory_changes")
print(" - policy_relationships")
print(" - impact_ground_truth")