# Using https://github.com/CSCfi/machine-learning-scripts/blob/master/notebooks/pytorch-mnist-mlp.ipynb 
# as a template for implementing PyTorch
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.autograd import Variable
from torch.utils.data import Dataset, DataLoader
from itertools import chain

import itertools

import numpy as np

from sklearn.model_selection import KFold

import os.path
#	---	Global Statements Start	---

k = 25				# K-fold validation

epochs = 3

batch_size = 1

window_size = 7
num_classes = 8
output_size = 2

learningRate = 0.00000001

input_size = num_classes * window_size 		# Input size is 7*8
#	---	Global Statements End	---

cuda = torch.cuda.is_available()

kwargs = {'num_workers': 1, 'pin_memory': True} if cuda else {}

class DiabetesDataset(Dataset):
	def __init__(self, batch, labels):
		self.x_data = batch
		self.y_data = labels
		self.len = self.x_data.shape[0]

	def __getitem__(self, index):
		window = torch.tensor(torch.from_numpy(self.x_data[index]))
		label = torch.tensor(self.y_data[index]).long()
		return window, label

	def __len__(self):
		return self.len

class cnn(nn.Module):
	def __init__(self, input_size, out_size):
		super(cnn, self).__init__()
		self.conv1 = nn.Sequential(
					nn.Conv1d(7, 56, kernel_size=5, stride=1),
					nn.ReLU(),
					nn.MaxPool2d(2,2)
				)
	
		self.fc1 = nn.Sequential(
			nn.Linear(56, 250),
			nn.ReLU(),
		)

		self.fc2 = nn.Sequential(
			nn.Linear(250, 30),
			nn.ReLU(),
		)

		self.fc3 = nn.Sequential(
			nn.Linear(30, 2),
			#nn.ReLU(),
		)

		self.log_softmax = nn.LogSoftmax()
	
	def forward(self, x):
		x = self.conv1(x)

		x = x.view(x.size(0), -1)
		
		x = self.fc1(x)
		x = self.fc2(x)
		x = self.fc3(x)
		x = self.log_softmax(x)

		return x

def train(model, epoch, data_set, criterion, optimizer, log_interval = 100):
	model.train()
	for batch_idx, (data, target) in enumerate(data_set):
		
		if cuda:
			data, target = data.cuda(), target.cuda()
		
		# Conv data reshape
		a = data.numpy()
		final = []
		for i, b in enumerate(a):
			final.append(np.array_split(b, 7))
		final = np.array(final)
		data = torch.tensor(final)

		# Convert torch tensor to variable
		data, target = Variable(data), Variable(target)
		
		# forward + backward + optimize
		optimizer.zero_grad()
		output = model(data)
		loss = criterion(output, target)
		loss.backward()
		optimizer.step()
		
		
		if batch_idx % log_interval == 0:
			print('\t{}\t\t[{}/{} ({:.0f}%)] \t\t{:.6f}'.format(
				epoch, batch_idx * len(data), len(data_set.dataset),
				100. * batch_idx / len(data_set), loss.data.item()))
	
def validate(model, model_name, valid_set):
	model.eval()
	pred_name = str(model_name.split(".", 1)[0]) + "_pred1.csv"
	gold_name = str(model_name.split(".", 1)[0]) + "_gold1.csv"
	
	pred = open(pred_name, 'w+')
	gold = open(gold_name, 'w+')
	
	#print("Predicted\tLabel")
	for data, labels in valid_set:

		# Conv data reshape
		a = data.numpy()
		final = []
		for i, b in enumerate(a):
			final.append(np.array_split(b, 7))
		final = np.array(final)
		data = torch.tensor(final)


		outputs = model(data)
		#print outputs
		_, predicted = torch.max(outputs.data, 1)
		prob = outputs.sum().data.numpy()

		#print str(predicted.data.numpy()) + "\t" + str(labels)
		pred.write(str(prob)+"," + str(predicted.data.numpy()[0]) + "\n")
		gold.write(str(labels.data.numpy()[0]) + "\n")

	gold.close()
	pred.close()
	print("Created " + str(pred_name))
	print("Created "+ str(gold_name))
	print("Run with the following command: \n\t" + "python eval_simple.py -p " + str(pred_name) + " -g " + str(gold_name) + " -o result.csv")


# Retrieves all indices
def get_indice(indice = False):
	all_indice = []
	if indice is not False:
		for line in indice:
			all_indice.append(int(line))
	return all_indice

# Checks if window[start:end] is a continuous block
def check_window(indice, start, end):
	if len(indice) != 0:
		array = indice[start:end]
		for i, x in enumerate(array):
			if i + 1 < len(array):
				temp = x + 1
				if temp == array[i+1]:
					continue
				else:
					return False	# Window is not continuous
	return True						# Window is continuous

def load_data(data_file, indice_file = False):
	batch = []
	labels = []

	if (indice_file != False):
		data = np.loadtxt(data_file, delimiter=',', usecols=(1, 2, 3, 4, 5, 6, 7, 8, 9), dtype=np.float32)

		with open(indice_file, 'r') as f:
			indice = [line.strip() for line in f]

		data_total_len = data.shape[0]
		all_indice = get_indice(indice)

		for i, row in enumerate(data):
			new_batch = []
			if (i+window_size <= data_total_len) and (check_window(all_indice, i, i+window_size)):
				for j in range(i, i+window_size):
					new_batch = [x for x in itertools.chain(new_batch, data[j, 0:8])]
					if j == i+window_size-1:
						last = data[j, [-1]]
				batch.append(new_batch)
				labels = np.append(labels, last)
			else:
				continue			# If window size is not 7 or if the contents of the window is not continuous, skip this window
	else:
		data = np.loadtxt(data_file, delimiter=',', usecols=(0, 1, 2, 3, 4, 5, 6, 7, 8), dtype=np.float32)
		batch = [row[0:8] for i, row in enumerate(data)]
		batch = list(chain.from_iterable(batch))
		#print  data[6, [-1]]
		last = 1
		labels = last

	batch = np.array(batch)
	return batch, labels

def kFold(batch, labels):
	kf = KFold(n_splits = k)
	for train_index, test_index in kf.split(batch):
		# print("TRAIN:", train_index, "TEST:", test_index)
		X_train, X_test = batch[train_index], batch[test_index]
		y_train, y_test = labels[train_index], labels[test_index]

	return X_train, y_train, X_test, y_test

def trainModel(model_name, training):
	model = cnn(input_size, output_size)
	if cuda:
		model.cuda()
	criterion = nn.CrossEntropyLoss()
	optimizer = optim.SGD(model.parameters(), lr=learningRate, momentum=0.5)
	#optimizer = torch.optim.Adam(model.parameters(), lr=learningRate)  	
	print("Learning Rate: " + str(learningRate))
	print("\tEpoch\t\tInterval\t\tLoss")
	for epoch in range(1, epochs + 1):
		train(model, epoch, training, criterion, optimizer)

	torch.save(model.state_dict(), model_name)	# Saves model

def run(model_name, validation):
	model = cnn(input_size, output_size)
	if cuda:
		model.cuda()
	model.load_state_dict(torch.load(model_name))
	validate(model, model_name, validation)

def print_data(train_data, train_labels, test_data, test_labels):
	print "Training Data"
	print train_data
	print train_data.shape
	print "\nTraining Labels"
	print train_labels
	print train_labels.shape

	print "\nTest Data"
	print test_data
	print test_data.shape
	print "\nTest Labels"
	print test_labels
	print test_labels.shape

## Building Individual Model for Subject_2
'''
s7_batch, s7_label = load_data('./data/part1/Subject_7_part1.csv', './data/part1/list_7_part1.csv')

train_data, train_labels, test_data, test_labels = kFold(s7_batch, s7_label)

print_data(train_data, train_labels, test_data, test_labels)

if not os.path.isfile("subject2.pt"):
	train_set = DiabetesDataset(train_data, train_labels)
	train_loader = DataLoader(dataset=train_set,
							batch_size=batch_size,
							shuffle=True,
							num_workers=6)

	print("\tPart2: Training model subject2.pt")
	trainModel("subject2.pt", train_loader)
'''

test_data = []
test_labels = []
for i in range(1, len(os.listdir("./data/final_test/subject7/"))+1):
	fname = "subject7_"+ str(i) + ".csv"
	if os.path.isfile("./data/final_test/subject7/" + fname):
		batch, label = load_data("./data/final_test/subject7/" + fname)
		test_data.append(batch)
		test_labels.append(label)

test_data = np.array(test_data)
test_labels = np.array(test_labels)

if os.path.isfile("./results/subject2_model/subject2.pt"):
	test_set = DiabetesDataset(test_data, test_labels)
	validation_loader = DataLoader(dataset=test_set,
							batch_size=batch_size,
							shuffle=False,
							num_workers=6)
	print("\tPart 2: Running model subject2.pt")
	run("./results/subject2_model/subject2_m0.pt", validation_loader)
	#run("subject2.pt", validation_loader)