from pydantic import BaseModel

class Agent(BaseModel):
    name: str
    role: str
    clearance: int

# Create an instance of your agent
agent = Agent(name="Jane Bond", role="Field Operative", clearance=7)
print(agent)