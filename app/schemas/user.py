from pydantic import BaseModel, EmailStr

# The Registration Form (Data coming IN)
# We don't let the client pick their own VIP number (id).
class UserCreate(BaseModel):
    # EmailStr automatically checks if it has an '@' and a valid domain!
    email: EmailStr
    # The raw, secret password before we hash and lock it in the database.
    password: str


# The Public Name Tag (Data going OUT)
# Display on the frontend. Password is not included to avoid leaking secrets to the internet.
class UserPublic(BaseModel):
    id: int
    email: EmailStr
    is_bot: bool

    # The Magic Translator
    # SQLAlchemy database objects are heavy and complex.
    # This setting tells Pydantic: "Read the SQLAlchemy object and magically 
    # translate its attributes into a clean JSON format the web browser can understand."
    model_config = {"from_attributes": True}


# The VIP Wristband (Authentication)
# Instead of asking for a password every time, hand them this digital wristband after they log in once. 
class Token(BaseModel):
    # A long, scrambled string of characters (usually a JWT) that acts as the key.
    access_token: str
    
    # "bearer" just means: "Whoever is physically holding (bearing) this token is allowed inside."
    token_type: str = "bearer"