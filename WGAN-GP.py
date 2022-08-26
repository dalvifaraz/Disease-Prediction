# -*- coding: utf-8 -*-
"""wgan-gp_128x128.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1UanBgkj-Q50ZFq-MxJ6lT7nHGct9oDLJ

# WGAN-GP For 128x128

## Prerequisite
"""

!pip install tensorflow==1.14
!pip install tensorflow-gpu==1.14
!pip install keras==2.2.3

"""## Necessary Imports"""

import numpy as np # linear algebra

import os
import sys
from tqdm import tqdm, tqdm_notebook
import glob
import shutil
import time      # time.perf_counter()
import random

import matplotlib.pyplot as plt
import cv2

import xml.etree.ElementTree as ET

from keras.layers import Input, Dense, Reshape, Flatten
from keras.layers import BatchNormalization, Activation
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.convolutional import UpSampling2D, Conv2D
from keras.models import Model
from keras import backend as K
from keras.optimizers import Adam
from keras.preprocessing.image import image

"""## Constants"""

# image size
img_size = 128
channels = 3
img_shape = (img_size, img_size, channels)    # (64,64,3)

# z(latent variable) size
z_dim = 100
z_shape = (z_dim,)

# gradient penalty coefficient "λ"
penaltyLambda = 10    # d_loss = f_loss - r_loss + λ･penalty

# critic(discriminator) iterations per generator iteration
trainRatio = 5

batch_size = 64        # 16 or 64 better?
rec_interval = 1000

DIR = os.getcwd()
DIRimg = "/content/chest_xray/train/PNEUMONIA/"    #path for input directory 
DIRout = "/content/drive/My Drive/sn"    #path for input directory

"""## Image Loading and Resizing Function"""

def loadImage(fPath, resize = True):
    img = cv2.imread(fPath)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)      # BGR to RGB
    if resize:
        interpolation = cv2.INTER_CUBIC         # expantion
        img = cv2.resize(img, (img_size, img_size), interpolation = interpolation)  # resize
    return img

"""## Sample Images before Resizing"""

all_fNames = os.listdir(DIRimg)

# image sample
sample_ids = random.sample(range(len(all_fNames)), 9)
fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(12,10))
for i, axis in enumerate(axes.flatten()):
    img = loadImage(os.path.join(DIRimg,
                    all_fNames[sample_ids[i]]), resize=False)
    imgplot = axis.imshow(img)
    axis.set_title(all_fNames[sample_ids[i]])
    axis.set_axis_off()
plt.tight_layout()

"""## Samples Images after Resizing"""



"""## Convert Images to Train Data"""

# train data
x_train = np.zeros((len(all_fNames),img_size,img_size,3))
for i in tqdm(range(len(all_fNames))):
    path = os.path.join(DIRimg, all_fNames[i])
    x_train[i] = loadImage(path)

x_train = x_train / 255.
print(x_train.shape)

"""## WGAN-gp Model

### Generator
"""

def build_generator():
    input = Input(shape=z_shape)
    
    #8x8x1024
    x = Dense(4*img_size*img_size, activation="relu")(input)                            
    x = Reshape((8, 8, -1))(x)
    
    #8x8x1024 -> 16x16x512
    x = UpSampling2D((2, 2))(x)                                                         
    x = Conv2D(64*16, kernel_size=3, strides=1, padding="same", use_bias=False)(x)      
    x = BatchNormalization(momentum=0.9, epsilon=1e-5)(x, training=1)
    x = Conv2D(64*16, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = BatchNormalization(momentum=0.9, epsilon=1e-5, )(x, training=1)
    x = Activation("relu")(x)
    x = Conv2D(64*16, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = BatchNormalization(momentum=0.9, epsilon=1e-5)(x, training=1)
    x = Activation("relu")(x)
    
    #16x16x512 -> 32x32x256
    x = UpSampling2D((2, 2))(x)                                                         
    x = Conv2D(64*8, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = BatchNormalization(momentum=0.9, epsilon=1e-5)(x, training=1)
    x = Conv2D(64*8, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = BatchNormalization(momentum=0.9, epsilon=1e-5, )(x, training=1)
    x = Activation("relu")(x)
    x = Conv2D(64*8, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = BatchNormalization(momentum=0.9, epsilon=1e-5)(x, training=1)
    x = Activation("relu")(x)
    
    #32x32x256 -> 64x64x128
    x = UpSampling2D((2, 2))(x)                                                         
    x = Conv2D(64*4, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = BatchNormalization(momentum=0.9, epsilon=1e-5)(x,training=1)
    x = Conv2D(64*4, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = BatchNormalization(momentum=0.9, epsilon=1e-5, )(x, training=1)
    x = Activation("relu")(x)
    x = Conv2D(64*4, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = BatchNormalization(momentum=0.9, epsilon=1e-5)(x, training=1)
    x = Activation("relu")(x)
    
    #64x64x128 -> 128x128x64
    x = UpSampling2D((2, 2))(x)                                                         
    x = Conv2D(64*2, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = BatchNormalization(momentum=0.9, epsilon=1e-5)(x,training=1)
    x = Conv2D(64*2, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = BatchNormalization(momentum=0.9, epsilon=1e-5, )(x, training=1)
    x = Activation("relu")(x)
    x = Conv2D(64*2, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = BatchNormalization(momentum=0.9, epsilon=1e-5)(x, training=1)
    x = Activation("relu")(x)
    
    #128x128x64 -> 128x128x3
    x = Conv2D(3, kernel_size=3, strides=1, padding="same", activation="tanh", use_bias=False,)(x) 

    model = Model(input, x)
    print("●generator")
    model.summary()
    return model

"""### Discriminator"""

def build_discriminator():
    input = Input(shape=img_shape)
    
    # 128*128*3 -> 64x64x64 
    x = Conv2D(128, kernel_size=4, strides=2, padding="same", use_bias=False)(input)
    x = LeakyReLU(0.2)(x)
    # 64x64x64-> 32x32x128 
    x = Conv2D(256, kernel_size=4, strides=2, padding="same", use_bias=False)(x)
    x = LeakyReLU(0.2)(x)
    # 32x32x128 -> 16x16x256  
    x = Conv2D(512, kernel_size=4, strides=2, padding="same", use_bias=False)(x)
    x = Conv2D(512, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = LeakyReLU(0.2)(x)
    # 16x16x256 -> 16x16x512
    x = Conv2D(512, kernel_size=3, strides=1, padding="same", use_bias=False)(x)
    x = LeakyReLU(0.2)(x)
    # 16x16x512 -> 8x8x1024
    x = Conv2D(1024, kernel_size=4, strides=2, padding="same", use_bias=False)(x)
    x = LeakyReLU(0.2)(x)
    
    x = Conv2D(1, kernel_size=1, strides=1, padding="same", use_bias=False)(x)
    x = Flatten()(x)
    x = Dense(units=1, activation=None)(x)   # activation = None
    
    model = Model(input, x)
    print("●discriminator")
    model.summary()
    return model

"""### WGan-gp Function"""

def build_WGANgp(generator, discriminator):
    #### model
    # generator image(fake image)
    z = Input(shape=z_shape)
    f_img = generator(z)
    f_out = discriminator(f_img)
    # real image
    r_img = Input(shape=img_shape)
    r_out = discriminator(r_img)
    # average image
    epsilon = K.placeholder(shape=(None,1,1,1))
    a_img = Input(shape=(img_shape),
                  tensor = epsilon * r_img + (1-epsilon) * f_img)
    a_out = discriminator(a_img)

    #### loss
    # original critic(discriminator) loss
    r_loss = K.mean(r_out)
    f_loss = K.mean(f_out)
    # gradient penalty  <this is point of WGAN-gp>
    grad_mixed = K.gradients(a_out, [a_img])[0]
    norm_grad_mixed = K.sqrt(K.sum(K.square(grad_mixed), axis=[1,2,3]))
    grad_penalty = K.mean(K.square(norm_grad_mixed -1))
    penalty = penaltyLambda * grad_penalty
    # d loss
    d_loss = f_loss - r_loss + penalty
    
    #### discriminator update function
    d_updates = Adam(lr=1e-4, beta_1=0.5, beta_2=0.9). \
                get_updates(discriminator.trainable_weights,[],d_loss)
    d_train = K.function([r_img, z, epsilon],
                         [r_loss, f_loss, penalty, d_loss],
                         d_updates)
    
    #### generator update function
    g_loss = -1. * f_loss
    g_updates = Adam(lr=1e-4, beta_1=0.5, beta_2=0.9). \
                get_updates(generator.trainable_weights,[],g_loss)
    g_train = K.function([z], [g_loss], g_updates)

    return g_train, d_train

"""## Build Training Model"""

# generator Model
generator = build_generator()
# discriminator Model
discriminator = build_discriminator()
# WGAN-gp Training Model
G_train, D_train = build_WGANgp(generator, discriminator)

"""## Prepare Training"""

# fixed z for confirmation of generated image
z_fix = np.random.normal(0, 1, (64, z_dim)) 

# list for store learning progress data
g_loss_list = []
r_loss_list = []
f_loss_list = []
f_r_loss_list = []
penalty_list = []
d_loss_list = []

# (0～1) → (-1～+1)
X_train = (x_train.astype(np.float32) - 0.5) / 0.5

"""### Function for ploting Images"""

def sumple_images(imgs, rows=3, cols=3, figsize=(12,10)):
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=figsize)
    for indx, axis in enumerate(axes.flatten()):
        img = image.array_to_img(imgs[indx])    # ndarray → PIL
        imgplot = axis.imshow(img)
        axis.set_axis_off()
    plt.tight_layout()

"""## Perform Training"""

import time

iteration = 0
while iteration<=2001:
    
    start_time = time.time()
    #### Discriminator
    for j in range(trainRatio):
        # Generator in
        z = np.random.normal(0, 1, (batch_size, z_dim))
        # Generator out Images
        f_imgs = generator.predict(z)
        # Real Images
        idx = np.random.randint(0, X_train.shape[0], batch_size)
        r_imgs = X_train[idx]
        # train the discriminator
        epsilon = np.random.uniform(size = (batch_size, 1,1,1))
        r_loss, f_loss, penalty, d_loss = D_train([r_imgs, z, epsilon])

    #### Generator
    # Generator in
    z = np.random.normal(0, 1, (batch_size, z_dim))
    # train the generator
    g_loss = G_train([z])

    #### Record of learning progress
    # loss
    r_loss_list.append(r_loss)
    f_loss_list.append(f_loss)
    f_r_loss_list.append(f_loss - r_loss)
    penalty_list.append(penalty)
    d_loss_list.append(d_loss)
    # generated image sumple
    if (iteration in [100, 1000]) or (iteration % 500 == 0):
        print(f'iteration:{iteration} / d_loss:{d_loss:.3f} / g_loss:{sum(g_loss)/len(g_loss):.3f}')
        print('Time Taken : %f' % (time.time()-start_time))
        g_imgs = generator.predict(z_fix)
        imgs = g_imgs * 127.5 + 127.5
        sumple_images(imgs, rows=1, cols=7)
        plt.show()

    iteration += 1
    print('Done Iteration %d'%iteration)
    print(f'iteration:{iteration} / d_loss:{d_loss:.3f} / g_loss:{sum(g_loss)/len(g_loss):.3f}')
    print('Time Taken : %f' % (time.time()-start_time))
print("last iteration:",iteration - 1)

"""## Plot the Graphs"""

# plot loss
fig, ax = plt.subplots(5, 2, figsize=(8.27,11.69))
for j in range(2):
    ax[0,j].plot(r_loss_list, label="r_los")
    ax[1,j].plot(f_loss_list, label="f_loss")
    ax[2,j].plot(f_r_loss_list, label="f-r_loss")
    ax[3,j].plot(penalty_list, label="penalty")
    ax[4,j].plot(d_loss_list, label="d_loss")
for i in range(5):
    ax[i,0].set_xlim([0,200])
    ax[i,1].set_xlim([200,iteration])
    for j in range(2):
        ax[i,j].grid()
        ax[i,j].legend()
plt.savefig('normal_128')
plt.show()

"""## Create Output Directory"""

if os.path.exists(DIRout):
    shutil.rmtree(DIRout)
if not os.path.exists(DIRout):
    os.mkdir(DIRout)

"""## Generate Sample Images Using Training Model"""

# generate images for submit
n = 5000
batch = 64
for i in tqdm(range(0, n, batch)):
    z = np.random.normal(0,1,size=(batch, z_dim))
    g_imgs = generator.predict(z)
    imgs = g_imgs * 127.5 + 127.5
    for j in range(batch):
        img = image.array_to_img(imgs[j])      # ndarray → PIL 
        img.save(os.path.join(DIRout, 'image_' + str(i+j+1).zfill(5) + '.png'))
        if i+j+1 == n:
            break
print(len(os.listdir(DIRout)))

"""## Plot the sample Images"""

# generated xrays sumple
sumple_images(g_imgs, rows=5, cols=7, figsize=(12,8))

"""## Submit the Directory"""

if os.path.exists('pneumonia_128.zip'):
    os.remove('pneumonia_128.zip')
shutil.make_archive('pneumonia_128', 'zip', DIRout)
print("<END>")



mv /content/pneumonia_128.zip /content/drive/My Drive/Assdf2/Assdf