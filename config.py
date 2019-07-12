from app import app


MEDIA_FOLDER = 'media'
app.config['MEDIA_FOLDER'] = MEDIA_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
