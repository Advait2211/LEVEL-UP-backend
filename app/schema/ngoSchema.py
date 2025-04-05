from mongoengine import Document, StringField, ListField, ReferenceField, URLField, DateTimeField
from datetime import datetime
# from app.schema.userSchema import User
# from app.schema.eventSchema import Event

class NGO(Document):
    name = StringField(required=True)
    description = StringField()
    logo_url = URLField()
    
    owner_id = ReferenceField('User', required=True)
    members = ListField(ReferenceField('User'))
    core_members = ListField(ReferenceField('User'))
    events = ListField(ReferenceField('Event'))
    outreach_count = StringField()
    tags = ListField(StringField(), required=True)
    
    contact_information = StringField()
    location = StringField()
    website = URLField()
    social_media_links = ListField(StringField())

    created_at = DateTimeField(default=datetime.utcnow)

