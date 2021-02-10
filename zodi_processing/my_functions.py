import numpy as np
from tables import *
import astropy.units as u
import matplotlib
matplotlib.use('Agg') # required because matplotlib can cause crashes on the site
import matplotlib.pyplot as plt
import io
import base64
from flask import current_app
import os

plt.rcParams.update({'image.origin': 'lower',
                     'image.interpolation':"nearest"})

'''
These are the functions used to create the plots and process the zodi
'''

def create_plot(zodi_data):
    img = io.BytesIO()
    #plt.figure(figsize=(5,5))
    plt.imshow(zodi_data)
    plt.colorbar()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return 'data:image/png;base64,{}'.format(plot_url)

def mask_zodi(users_zodi_data, cmr, thresh):
    
    n_zodi = 256
    
    if thresh == 'None':
        index = users_zodi_data < 0
    else:
        index = users_zodi_data < users_zodi_data.max()/thresh # using the thresh to mask pixels
    
    # creating the coremask
    zodi_pixscale = 0.003*u.arcsecond
    cmr = cmr*u.milliarcsecond.to(u.arcsecond) # put the core mask in milliarcseconds
    xpix,ypix = np.meshgrid(np.arange(-n_zodi/2,n_zodi/2),np.arange(-n_zodi/2,n_zodi/2))
    x = (xpix+.5).flatten()*zodi_pixscale
    y = (ypix+.5).flatten()*zodi_pixscale
    index[(np.sqrt((x)**2 + (y)**2).value<cmr).reshape([n_zodi,n_zodi])]=True
    
    masked_zodi_data = np.ma.masked_array(users_zodi_data,index)
    
    return masked_zodi_data

def process_zodi(psfs_choice,masked_zodi_data):
    
    # open the h5file containing the table
    if psfs_choice == 'os5': 
        h5fname = "Interpped_OS5_PSFs.h5"
        n = 200
    elif psfs_choice == 'cgi':
        h5fname = "Interpped_CGI_PSFs.h5"
        n = 128
    
    h5path = os.path.join(current_app.root_path, current_app.config['INTERPPED_FOLDER'], h5fname)
    h5file = open_file(h5path, mode="r")
    table = h5file.root.interpolated_library # points to the table containing the data
    
    # Now run the masked data with the PSFs using the h5file
    zodi_processed_flat = np.zeros([n*n])
    
    for i,zodi_val in enumerate(masked_zodi_data.flatten()):
        if np.ma.is_masked(zodi_val):
            continue
        zodi_processed_flat += zodi_val*table[i]['array']

    zodi_processed = zodi_processed_flat.reshape(n,n)
    
    h5file.close() # close the h5file
    
    return zodi_processed












