from mongoengine import Document, StringField, ListField, ReferenceField, DictField, FloatField, URLField, DateTimeField

class User(Document):
    meta = {'collection': 'users'}

    # Existing fields
    name = StringField(required=True)
    email = StringField(required=True, unique=True)
    profile_image_url = URLField()
    role = StringField(choices=["user", "ngo_admin"], default="user")
    password = StringField(required=True)
    
    interests = ListField(StringField(), default=[])
    ngos_owned = ListField(ReferenceField('NGO'))
    ngos_joined = ListField(ReferenceField('NGO'))
    joined_ngos = ListField(ReferenceField('NGO'))
    events_attended = ListField(ReferenceField('Event'))

    attendance_summary = DictField(
        field=DictField(
            field=FloatField()
        )
    )   

    # Added fields from database
    session_token = StringField()
    provider = StringField()
    created_at = DateTimeField()
    session_expires = DateTimeField()
    profile_pic_url = URLField()
    password_hash = StringField()
