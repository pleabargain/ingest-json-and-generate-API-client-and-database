from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from app.utils.logger import log_function_call

db = SQLAlchemy()

class BaseModel(db.Model):
    """Abstract base model with common fields"""
    __abstract__ = True
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Step(db.Model):
    """Model for individual steps in the output"""
    __tablename__ = 'steps'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    log_entry_id = db.Column(db.String(36), db.ForeignKey('log_entries.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    pseudo_code = db.Column(db.JSON, nullable=False)  # Store as JSON array
    
    def __repr__(self):
        return f"<Step {self.step_number} for Log {self.log_entry_id}>"

class LogEntry(BaseModel):
    """Model for JSON log entries"""
    __tablename__ = 'log_entries'
    
    model = db.Column(db.String(100), nullable=False, index=True)
    input_text = db.Column(db.Text, nullable=False)
    response_time = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    
    # Relationship with steps
    steps = db.relationship('Step', backref='log_entry', lazy=True,
                          cascade='all, delete-orphan')
    
    @log_function_call
    def add_step(self, step_number: int, description: str, pseudo_code: list):
        """Add a step to the log entry"""
        step = Step(
            log_entry_id=self.id,
            step_number=step_number,
            description=description,
            pseudo_code=pseudo_code
        )
        db.session.add(step)
        return step
    
    def __repr__(self):
        return f"<LogEntry {self.id} Model: {self.model}>"

class ValidationError(BaseModel):
    """Model for validation errors"""
    __tablename__ = 'validation_errors'
    
    error_type = db.Column(db.String(100), nullable=False, index=True)
    error_message = db.Column(db.Text, nullable=False)
    data_snapshot = db.Column(db.JSON, nullable=True)
    
    @classmethod
    @log_function_call
    def log_error(cls, error_type: str, message: str, data: dict = None):
        """Create a new validation error entry"""
        error = cls(
            error_type=error_type,
            error_message=message,
            data_snapshot=data
        )
        db.session.add(error)
        db.session.commit()
        return error
    
    def __repr__(self):
        return f"<ValidationError {self.id} Type: {self.error_type}>"

@log_function_call
def init_db(app):
    """Initialize the database"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
