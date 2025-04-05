from mongoengine import Document, StringField, DateTimeField, ReferenceField, ListField, URLField, DictField, FloatField, BooleanField
from app.schema.ngoSchema import NGO
from app.schema.userSchema import User

class Event(Document):
    title = StringField(required=True)
    description = StringField()
    ngo_id = ReferenceField(NGO, required=True)
    location = StringField()
    
    start_time = DateTimeField(required=True)
    end_time = DateTimeField(required=True)
    google_calendar_event_id = StringField()

    date = DateTimeField(required=True)
    
    start_photo_url = URLField(required=True)
    end_photo_url = URLField(required=True)

    # participants list
    participants = ListField(ReferenceField(User))

    # { user_id (as str): hours_worked }
    attendance = DictField(field=FloatField())

    completed = BooleanField(default=False)