# -*- coding: utf-8 -*-
"""Cross_Validate_Scratch.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18NGwhgaP0ffEoX9LRuFu7gjBBjSM9ry4
"""

# Commented out IPython magic to ensure Python compatibility.
# Multi-class Classification
import zipfile
import nibabel as nib
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.utils import make_grid
import numpy as np
import pandas as pd
import pickle
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import glob
from torch.autograd import Variable
from torchvision import models
from torch.nn import Module,  Linear, ReLU, CrossEntropyLoss, Sequential, Conv3d, MaxPool3d, Softmax, BatchNorm3d
from torch.optim import Adam
from tqdm import tqdm
from sklearn.metrics import accuracy_score
import seaborn as sn
import torch.optim as optim
from sklearn.metrics import accuracy_score
from sklearn.metrics import balanced_accuracy_score
from sklearn.metrics import matthews_corrcoef
from torchsummary import summary
from torch.utils.data import DataLoader, ConcatDataset
from sklearn.model_selection import KFold

# %matplotlib inline

from google.colab import drive
drive.mount('/content/drive/')

import os
#walk through directory and list through files
for dirpath, dirnames, filenames in os.walk("/content/drive/My Drive/ADNI_full"):
  print(f"There are {len(dirnames)} directories and {len(filenames)} images in '{dirpath}'.")
len(filenames)

#Get the class names
import numpy as np
import pathlib
data_dir = pathlib.Path('/content/drive/My Drive/ADNI_full')
class_names = np.array(sorted([item.name for item in data_dir.glob('*')]))
print(class_names)

with open("/content/drive/MyDrive/Images_ADNI.txt", 'rb') as fp:
  X=pickle.load(fp)
  y=pickle.load(fp)

X.shape, y.shape

X = torch.from_numpy(X)
X.shape, X.dtype

X=X.reshape(663,1,100,100,55)

X.shape

X=X.expand(-1,3,-1,-1,-1)
X.shape

y = torch.from_numpy(y)
y.shape, y.dtype

from sklearn.model_selection import train_test_split
X_train,X_test_data, y_train,y_test_data =train_test_split(X,y, test_size=0.2,  random_state=42)

from torch.utils.data import DataLoader,TensorDataset
dataset1 = TensorDataset(X_train, y_train)
dataset2= TensorDataset(X_test_data, y_test_data)

dataset = ConcatDataset([dataset1, dataset2])

len(dataset1)

len(dataset2)

len(dataset)

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

multiclass_resnet_scratch = models.video.r3d_18(pretrained=False, progress=False)

multiclass_resnet_scratch = multiclass_resnet_scratch.to(device)

summary(multiclass_resnet_scratch, (3, 100, 100,55))

print(multiclass_resnet_scratch)

for param in multiclass_resnet_scratch.parameters():
    param.requires_grad = False

multiclass_resnet_scratch.fc =  nn.Sequential(
            nn.Linear(512, 512),
            nn.LeakyReLU(inplace=True),
            nn.Dropout(),
            nn.Linear(512, 3),
            )
for param in multiclass_resnet_scratch.fc.parameters():
    param.requires_grad = True

summary(multiclass_resnet_scratch.to(device), (3, 100, 100,55))

# Configuration options
k_folds = 3
num_epochs = 5
loss_function = nn.CrossEntropyLoss()
  
# For fold results
results = {}
  
# Set random number seed
torch.manual_seed(22)
kfold = KFold(n_splits=k_folds, shuffle=True)
# Start print
print('kfold')
# K-fold Cross Validation model evaluation
for fold, (train_ids, test_ids) in enumerate(kfold.split(dataset)):
  print(train_ids)
  #print(test_ids)
  #print(len(test_ids))
  train_subsampler = torch.utils.data.SubsetRandomSampler(train_ids)
  test_subsampler = torch.utils.data.SubsetRandomSampler(test_ids)
  #print(train_subsampler)
  #print(len(train_subsampler))
  #print(test_subsampler)
  #print(len(test_subsampler))















# Configuration options
k_folds = 3
num_epochs = 10
loss_function = nn.CrossEntropyLoss()

# For fold results
results = {}
  
# Set random number seed
torch.manual_seed(22)
kfold = KFold(n_splits=k_folds, shuffle=True)
    
# Start print
print('kfold')
# K-fold Cross Validation model evaluation
for fold, (train_ids, test_ids) in enumerate(kfold.split(dataset)):
  # Print
  print(f'FOLD {fold}')
  # Sample elements randomly from a given list of ids, no replacement.
  train_subsampler = torch.utils.data.SubsetRandomSampler(train_ids)
  test_subsampler = torch.utils.data.SubsetRandomSampler(test_ids)
  
  trainloader = torch.utils.data.DataLoader(
                      dataset, 
                      batch_size=10, sampler=train_subsampler)
  validationloader = torch.utils.data.DataLoader(
                      dataset,
                      batch_size=10, sampler=test_subsampler)
  # Initialize optimizer
  optimizer = torch.optim.Adam(multiclass_resnet_scratch.fc.parameters(), lr=0.001)
  history = {'train_loss': [], 'test_loss': [],'train_acc':[],'test_acc':[]}
    
  # Run the training loop for defined number of epochs
  for epoch in range(0, num_epochs):

    # Print epoch
    print(f'Starting epoch {epoch+1}')

    # Set current loss value
    current_loss = 0.0

    # Iterate over the DataLoader for training data
    for i, data in enumerate(trainloader, 0):
        
      # Get inputs
      inputs, targets = data
        
      # Zero the gradients
      optimizer.zero_grad()
        
      # Perform forward pass
      outputs = multiclass_resnet_scratch(inputs)
        
      # Compute loss
      loss = loss_function(outputs, targets)
        
      # Perform backward pass
      loss.backward()
        
      # Perform optimization
      optimizer.step()

      # Set total and correct
      _, predicted = torch.max(outputs.data, 1)
      total += targets.size(0)
      train_correct += (predicted == targets).sum().item()
        
      # Print statistics
      current_loss += loss.item()
      if i % 10 == 9:
          print('Loss after mini-batch %5d: %.3f' %
                  (i + 1, current_loss / 10))
          current_loss = 0.0      
    # Process is complete.
    print('Training process has finished. Saving trained model.')

    # Print about testing
    print('Starting testing')
    
    # Saving the model
    save_path = f'./model-fold-{fold}.pth'
    model_scripted = torch.jit.script(multiclass_resnet_scratch) 
    model_scripted.save(save_path) 

    # Evaluation for this fold
    correct, total = 0, 0
    with torch.no_grad():

      # Iterate over the test data and generate predictions
      for i, data in enumerate(validationloader, 0):

        # Get inputs
        inputs, targets = data

        # Generate outputs
        outputs = multiclass_resnet_scratch(inputs)

        # Set total and correct
        _, predicted = torch.max(outputs.data, 1)
        total += targets.size(0)
        correct += (predicted == targets).sum().item()
    train_loss = current_loss / len(train_loader.sampler)
    train_acc = correct / len(train_loader.sampler) * 100
    test_loss = test_loss / len(test_loader.sampler)
    test_acc = test_correct / len(test_loader.sampler) * 100   
      # Print accuracy
      print('Accuracy for fold %d: %d %%' % (fold, 100.0 * correct / total))
      print('--------------------------------')
      results[fold] = 100.0 * (correct / total)
    print("Epoch:{}/{} AVG Training Loss:{:.3f} AVG Test Loss:{:.3f} AVG Training Acc {:.2f} % AVG Test Acc {:.2f} %".format(epoch + 1,
                                                                                                             num_epochs,
                                                                                                             train_loss,
                                                                                                             test_loss,
                                                                                                             train_acc,
                                                                                                             test_acc))  
  # Print fold results
  print(f'K-FOLD CROSS VALIDATION RESULTS FOR {k_folds} FOLDS')
  print('--------------------------------')
  sum = 0.0
  for key, value in results.items():
    print(f'Fold {key}: {value} %')
    sum += value
  print(f'Average: {sum/len(results.items())} %')



