from flask import render_template, url_for, flash, redirect, request, current_app, send_from_directory, abort
from flask_login import login_user, current_user, logout_user, login_required
from zodi_processing import zodi_app, db, bcrypt
from zodi_processing.forms import UploadZodiForm, LoginForm
from zodi_processing.models import User
from zodi_processing.my_functions import create_plot, process_zodi, mask_zodi
from werkzeug.utils import secure_filename
import numpy as np
import astropy.io.fits as fits
import os
from pathlib import Path
import time

home_path = Path(os.getcwd())/'zodi_processing'

@zodi_app.route("/")
@zodi_app.route("/home")
def home():
    delete_old_files()
    
    psfs_dir = 'PSFs'
    os5_dir = 'OS5_3.2'
    os5_fname = 'OS5_adi_3_highres_polx_lowfc_random_offset_psfs.fits'
    os5_path = home_path/psfs_dir/os5_dir/os5_fname
    
    # open the os5 psfs and get the data
    os5_fits = fits.open(os5_path)
    os5_data = os5_fits[0].data[:,8:-9,8:-9] # trim the data to 200 by 200
    os5_data = np.moveaxis(os5_data,0,-1)
    
    # Create the plot
    os5_plot_url = create_plot(os5_data[:,:,1])
    
    return render_template('home.html',os5_plot_url=os5_plot_url)

'''
@zodi_app.route("/register, methods = ['GET', 'POST'])
def register():
    # form = RegistrationForm()
    if form.validate_on_submit():
        # generate hashed password of the account being created 
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created, you may now login.')
        return redirect(url_for('login'))
'''
    
@zodi_app.route("/login", methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and/or password', 'danger')
    return render_template('login.html', title='Login', form=form)

@zodi_app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@zodi_app.route("/upload_zodi", methods=['GET','POST'])
@login_required
def upload_zodi():
    form = UploadZodiForm()
    
    if request.method == 'POST':
        # get the information from the form
        psfs_choice = form.psfs_choice.data
        users_zodi_file = form.users_zodi_file.data # get the data from the File object
        cmr = form.cmr.data
        thresh = form.thresh.data
        
        # convert the thresh to a string so that it can be passed to the next route
        thresh = str(thresh)
        
        # get the filename and make it secure
        users_zodi_fname = secure_filename(users_zodi_file.filename)
        if users_zodi_fname[-5:] != '.fits': # check if its a .fits file
            flash('The file must be a .fits file, please submit the correct type of file.','danger')
            return redirect(url_for('upload_zodi'))
        
        # make the file path and save the file
        users_zodi_path = home_path/zodi_app.config['UPLOAD_FOLDER']/users_zodi_fname
        users_zodi_file.save(str(users_zodi_path))
        
        return redirect(url_for('processed_zodi',
                                psfs_choice=psfs_choice,
                                users_zodi_fname=users_zodi_fname,
                                cmr=cmr,
                                thresh=thresh))

        
    return render_template('upload_zodi.html',title='Upload',form=form)


@zodi_app.route("/processed_zodi/<string:psfs_choice>/<string:users_zodi_fname>/<float:cmr>/<string:thresh>", 
                methods=['GET','POST'])
@login_required
def processed_zodi(psfs_choice,users_zodi_fname,cmr,thresh):
    
    if thresh != 'None':
        thresh = float(thresh) # convert the thresh back to a float
    
    users_zodi_path = home_path/zodi_app.config['UPLOAD_FOLDER']/users_zodi_fname
    
    # open the file, get the data, and check if the data dimensions are correct
    users_zodi_fits = fits.open(users_zodi_path)
    users_zodi_data = users_zodi_fits[0].data
    users_zodi_header = users_zodi_fits[0].header
    
    if users_zodi_data.shape[0] != 256 or users_zodi_data.shape[1] != 256:
        flash('The file must have pixel dimensions 256 by 256, please submit a correct file.','danger')
        return redirect(url_for('upload_zodi'))
    
    # make a plot of the users data
    users_zodi_plot_url = create_plot(users_zodi_data)
    
    '''
    Masking the data
    '''
    # mask the data and make the plot
    masked_zodi_data = mask_zodi(users_zodi_data,cmr,thresh)
    masked_zodi_plot_url = create_plot(masked_zodi_data)
    
    # set the header of the masked fits file
    masked_zodi_header = users_zodi_header
    masked_zodi_header["CMR"] = cmr
    masked_zodi_header["THRESH"] = thresh
    
    # make the masked file name and save it
    timestr = time.strftime("%Y%m%d_%H%M%S")
    masked_zodi_fname = secure_filename(timestr + "_masked.fits")
    masked_zodi_path = home_path/zodi_app.config['MASKED_FOLDER']/masked_zodi_fname
    fits.writeto(masked_zodi_path, 
                 masked_zodi_data.filled(fill_value=0),
                 overwrite=True, 
                 header=masked_zodi_header)
    
    '''
    Processing the masked data
    '''
    # process the data and make the processed plot
    zodi_processed = process_zodi(psfs_choice,masked_zodi_data)
    zodi_processed_plot_url = create_plot(zodi_processed)
    
    # set the header of the processed fits file
    zodi_processed_header = users_zodi_header
    zodi_processed_header["CMR"] = cmr
    zodi_processed_header["THRESH"] = thresh
    
    # make the processed file name and save it
    timestr = time.strftime("%Y%m%d_%H%M%S")
    zodi_processed_fname = secure_filename(timestr + "_processed.fits")
    zodi_processed_path = home_path/zodi_app.config['PROC_FOLDER']/zodi_processed_fname
    fits.writeto(zodi_processed_path, 
                 zodi_processed,
                 overwrite=True, 
                 header=zodi_processed_header)
    
    flash('Your file has been uploaded.','success')
    
    return render_template('processed_zodi.html',
                           users_zodi_plot_url=users_zodi_plot_url,
                           masked_zodi_plot_url=masked_zodi_plot_url,
                           cmr=cmr,
                           thresh=thresh,
                           masked_zodi_fname=masked_zodi_fname,
                           zodi_processed_plot_url=zodi_processed_plot_url,
                           zodi_processed_fname=zodi_processed_fname)


'''
This route is for allowing the user to download the masked or processed data
'''
@zodi_app.route('/download/<string:fname>', methods=['GET', 'POST'])
def download(fname):
    if fname[-11:] == 'masked.fits':
        directory=zodi_app.config['MASKED_FOLDER']
    else:
        directory=zodi_app.config['PROC_FOLDER']
    
    directory = os.path.join(current_app.root_path, directory)
    
    return send_from_directory(directory=directory, 
                               filename=fname)


def delete_old_files():
    cur_time = time.time()
    
    for f in os.listdir(home_path/zodi_app.config['UPLOAD_FOLDER']):
        f_path = home_path/zodi_app.config['UPLOAD_FOLDER']/f
        if os.stat(f_path).st_mtime < cur_time - 7 * 86400:
            os.remove(f_path)
    
    for f in os.listdir(home_path/zodi_app.config['MASKED_FOLDER']):
        f_path = home_path/zodi_app.config['MASKED_FOLDER']/f
        if os.stat(f_path).st_mtime < cur_time - 7 * 86400:
            os.remove(f_path)
    
    for f in os.listdir(home_path/zodi_app.config['PROC_FOLDER']):
        f_path = home_path/zodi_app.config['PROC_FOLDER']/f
        if os.stat(f_path).st_mtime < cur_time - 7 * 86400:
            os.remove(f_path)
    
    
    
    
    
    