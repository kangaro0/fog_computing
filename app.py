import os
import shutil
from flask import Flask, request, redirect, url_for, render_template, \
    send_from_directory
import json
from cnn import MODEL
from preprocessing import preprocess
from declaration import declare_template_class
from validation import validate


app = Flask(__name__)
app.config.from_object('config')
app.config.update(
    DEBUG=False,
    TESTING=False
)


def allowed_file(filename):
    """Checks if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/media/<path:path>', methods=['GET', 'POST'])
def media(path):
    """Displays any file in the media-folder."""
    path_without_filename = ''
    for element in path.split("/")[:-1]:
        path_without_filename = os.path.join(path_without_filename, element)

    directory = os.path.join(app.config['MEDIA_FOLDER'],
                             path_without_filename)

    filename = path.split("/")[-1]

    return send_from_directory(directory,
                               filename)


@app.route('/', methods=['GET', 'POST'])
def display_home_route():
    """Shows all directories in the media folder."""
    directories = os.listdir(app.config['MEDIA_FOLDER'])

    try:
        directories.sort(key=int)
    except:
        pass

    folders = []

    for idx, directory in enumerate(directories):
        # get every image in the folder
        files = os.listdir(os.path.join(app.config['MEDIA_FOLDER'],
                                        directory))

        only_pictures = files.copy()

        for idx, file in enumerate(files):
            if not allowed_file(file):
                only_pictures.remove(file)

        folders.append({'folder': directory,
                        'pictures': only_pictures})

    return render_template('home.html',
                           title="Home",
                           folders=folders)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file_route():
    # http://flask.pocoo.org/docs/1.0/patterns/fileuploads/
    error = ""
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            error = "Bitte eine Datei auswählen."
        else:
            file = request.files['file']

            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                error = "Bitte eine Datei auswählen."
            elif file and allowed_file(file.filename):
                demonstrate = request.form.getlist('demonstrate')
                regions_of_interest, folder_id = preprocess(file, demonstrate)

                data = {}

                if regions_of_interest:
                    if demonstrate:
                        # get the image_names in the preprocessing folder
                        preprocessing_folder = os.path.join('media',
                                                            str(folder_id),
                                                            'preprocessing')

                    general_valid = True
                    for idx, region_of_interest_tuple in enumerate(regions_of_interest):
                        filename = region_of_interest_tuple[0]
                        region_of_interest = region_of_interest_tuple[1]
                        # declare class of each region_of_interest
                        template_as_image, delta = declare_template_class(region_of_interest)

                        # validate the clamp
                        valid = validate(region_of_interest, template_as_image, delta, folder_id, filename)

                        if not valid:
                            general_valid = False

                        if demonstrate:
                            data.update({str(filename): valid})

                    if demonstrate:
                        data_filepath = os.path.join(preprocessing_folder,
                                                     'data.txt')
                        with open(data_filepath, 'w') as outfile:
                            json.dump(data, outfile)

                    if folder_id:
                        return redirect(url_for('display_result_route',
                                                folder_id=folder_id))
                    else:
                        if not general_valid:
                            message = "Ausschuss"
                        else:
                            message = "Fehlerfrei"

                        return render_template('upload.html',
                                               title="Upload",
                                               message=message,
                                               valid=general_valid)
                else:
                    message = "No Circles Found!"
                    return render_template('upload.html',
                                           title="Upload",
                                           message=message)

            else:
                error = "Bitte eine Datei mit dem Format {0} hochladen.".format(
                    app.config['ALLOWED_EXTENSIONS']
                )

    return render_template('upload.html', title="Upload", error=error)


@app.route('/result/<string:folder_id>', methods=['GET', 'POST'])
def display_result_route(folder_id):
    # check if folder_id exists
    try:
        directory = os.listdir(
            os.path.join(app.config['MEDIA_FOLDER'],
                         str(folder_id)))
    except:
        directory = False

    if not directory:
        return redirect(url_for('display_home_route'))

    original_picture = None
    preprocessing_string = 'preprocessing'
    preprocessing = []
    templates = []
    for content in directory:
        if allowed_file(content):
            original_picture = content
        elif content == preprocessing_string:
            preprocessing_folder = os.path.join(app.config['MEDIA_FOLDER'], str(folder_id), preprocessing_string)
            try:
                for picture in os.listdir(preprocessing_folder):
                    if allowed_file(picture):
                        if picture.endswith('template.jpg'):
                            templates.append(picture)
                        else:
                            preprocessing.append(picture)
            except:
                pass

            data_filepath = os.path.join(preprocessing_folder, 'data.txt')
            with open(data_filepath) as json_file:
                data = json.load(json_file)

    templates.sort()
    preprocessing.sort()

    return render_template('result.html',
                           folder_id=folder_id,
                           picture=original_picture,
                           preprocessing=preprocessing,
                           data=data,
                           templates=templates)


@app.route('/result/<string:folder_id>/delete', methods=['GET', 'POST'])
def delete_result_route(folder_id):
    # check if folder_id exists
    path = os.path.join(app.config['MEDIA_FOLDER'],
                        str(folder_id))
    try:
        directory = os.listdir(path)
    except:
        directory = False

    if not directory:
        return redirect(url_for('display_home_route'))

    if request.method == 'POST':
        shutil.rmtree(path, ignore_errors=False, onerror=None)

    return redirect(url_for('display_home_route'))


if __name__ == '__main__':
    app.run()
