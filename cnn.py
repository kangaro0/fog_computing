from keras.models import load_model
import os


# load from h5-file
cnn = os.path.join('static', 'models', 'cnn.h5')
MODEL = load_model(cnn)
# this function is needed for BugFix
# https://github.com/keras-team/keras/issues/6462#issuecomment-319232504
MODEL._make_predict_function()
