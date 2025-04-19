from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import List


class UserBase(SQLModel):
    """Base model for user with common attributes."""
    email: str = Field(index=True, unique=True)
    name: str
    role: str  # TODO: This should be an enum. Change this later.


class User(UserBase, table=True):
    """User model representation of a person who can own agents and create
    configurations."""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow,
                                 nullable=False, description="Timestamp when the user was create (UTC)")
    updated_at: datetime = Field(default_factory=datetime.utcnow,
                                 sa_column_args={"onupdate": datetime.utcnow},
                                 nullable=False, description="Timestamp when the user data was updated(UTC)")
    # Relationships
    agents: List["Agent"] = Relationship(back_populates="owner")
    configurations: List["AgentConfiguration"] = Relationship(
        back_populates="created_by")


class AgentBase(SQLModel):
    pass


class Agent(AgentBase, table=True):
    pass


class AgentConfigurationBase(SQLModel):
    pass


class AgentConfiguration(AgentConfigurationBase, table=True):
    pass
