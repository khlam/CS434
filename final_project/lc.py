# general_nn.py line 224

'''
To Do

1. Ensure model (weight vector?) is being stored effectively
2. Verify model accuracy using test data, other subjects w/e
3. Normalize data if necessary
4. Encode model (weight vector?) into linear classifier
	OR Update the batch_gradient_descent method to write into the files desired
	
Output files will need to write to a file and store the raw value and the 0 or 1
for predicting whether a hypo event happens.

Can we write the prediction during batch_gradient_descent or will it need to be done
separately using a classifier created a la gradient descent?
	
What's this about FAC? False positives/negatives counts? ROC? Not in Kansas anymore
'''

# Using Lam's code as a base to read and unpack data
import itertools
import csv
import numpy as np
from sklearn.model_selection import KFold

k = 20					# K-fold validation
batch_size = 4
window_size = 7

''' Parsing Code '''
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

def load_data(data_file, indice_file):
	data = np.loadtxt(data_file, delimiter=',', usecols=(1, 2, 3, 4, 5, 6, 7, 8, 9), dtype=np.float32)
	
	with open(indice_file, 'r') as f:
		indice = [line.strip() for line in f]

	data_total_len = data.shape[0]
	all_indice = get_indice(indice)

	batch = []
	labels = []

	for i, row in enumerate(data):
		new_batch = []
		if  (i+window_size <= data_total_len) and (check_window(all_indice, i, i+window_size)):
			for j in range(i, i+window_size):
				new_batch = [x for x in itertools.chain(new_batch, data[j, 0:8])]
				if j == i+window_size-1:
					last = data[j, [-1]]
			batch.append(new_batch)
			labels = np.append(labels, last)
		else:
			continue			# If window size is not 7 or if the contents of the window is not continuous, skip this window

	batch = np.array(batch)
	return batch, labels

def load_test_data(path):
    #label = []
    array = []
    with open(path, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        for row in spamreader:
            single = []
            #num = 0
            for i in xrange(7,14,1):
                for j in range(8):
                    single.append(float(row[i+(7*j)]))
                #num += float(row[i+(7*8)])
            #if(num == 0):
                #label.append(0)
            #else:
                #label.append(1)
            array.append(single)
    return np.array(array)

def kFold(batch, labels):
	kf = KFold(n_splits = k)
	for train_index, test_index in kf.split(batch):
		# print("TRAIN:", train_index, "TEST:", test_index)
		X_train, X_test = batch[train_index], batch[test_index]
		y_train, y_test = labels[train_index], labels[test_index]

	return X_train, y_train, X_test, y_test
''' End of Parsing Code '''

''' Classifier Code '''
# Might actually need this to be L2 and descent?
def weight(batch, labels):
	return (np.transpose(batch).dot(labels)).dot(np.linalg.inv(np.transpose(batch).dot(batch)))   # W = (X^T * X)^-1 * X^T * Y  

# This is a problem spot, learning rate must be low or it will overflow
def sigmoid(w, f):
	return 1.0 / (1.0 + np.exp((-1.0 * np.transpose(w)).dot(f)))  # 1 / (1 + e^(-w^T x))

# Solution might be to not let g reset to 0 every time?
def gradient(w, f, o, lam = 0):
	g = np.zeros(56, dtype=float)
	for i in range(f.shape[0]):
		y_hat = sigmoid(w, f[i])                # Iterate over all features in each row
		if lam != 0:                            # If there is a lamda value then we're doing regularization for Part 2.3
			y_hat = y_hat + (lam * np.linalg.norm(w, 2))
		#g = g + ((float(o[i]) - y_hat) * f[i])  # Reversed on slides, does't work for y_hat - o[i]
		g = g + ((y_hat - float(o[i])) * f[i])
	return g

def batch_gradient_descent(itr, learning_rate, f_train, o_train, f_test, o_test, w):
	print("Iteration\tTraining Accuracy\tTest Accuracy")
	
	for i in range(1, itr):
		#print(g)
		g = gradient(w, f_train, o_train)
		w = w - (learning_rate * g)
		#print(w)
		print(str(i) + "\t" + str(check(w, f_train, o_train)) + "\t" + str(check(w, f_test, o_test)))
		#f.write(str(i) + "," + str(check(w, f_train, o_train)) + "," + str(check(w, f_test, o_test)) + "\n")
	
	#f.close()
	return w

def check(w, f, expected):  # Check predicted values agaist the correct value column and take the ratio of correct / total
	out = open("output.csv", 'a')
	correct = 0
	for i in range(0, f.shape[0]):
		y_hat = sigmoid(w, f[i])
		out.write(str(y_hat) + ',' + str(np.round(y_hat)) + '\n')
		if np.round(y_hat) == expected[i]:
			correct += 1
	out.close()
	return float(correct) / float(f.shape[0])   # Ratio expresses this weight's accuracy

def run_model(w, f, filename):
	out = open(filename, 'w')
	for i in range(0, f.shape[0]):
		y_hat = sigmoid(w, f[i])
		out.write(str(y_hat) + ',' + str(int(np.round(y_hat))) + '\n')
	out.close()

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
''' End Classifier Code '''

''' Individual Training Code '''	# It's messy, deal with it.
itr = 10
learning_rate = 0.00000000000001					# must be very low, e-14?
w = np.zeros(56, dtype=float)                      # Initialize w = [0, ...0]

print("Individual Model\n")
print("Subject 2")
s2_batch, s2_label = load_data('./data/part1/Subject_2_part1.csv', './data/part1/list2_part1.csv')
train_data, train_labels, test_data, test_labels = kFold(s2_batch, s2_label)
w = batch_gradient_descent(itr, learning_rate, train_data, train_labels, test_data, test_labels, w)
# Save the weights so they can be applied to another set of data

print("\nSubject 7")
s7_batch, s7_label = load_data('./data/part1/Subject_7_part1.csv', './data/part1/list_7_part1.csv')
train_data, train_labels, test_data, test_labels = kFold(s7_batch, s7_label)
individual_model = batch_gradient_descent(itr, learning_rate, train_data, train_labels, test_data, test_labels, w)

with open("Subject_7_gold.csv", 'w') as file:
	for i in test_labels:
		file.write(str(int(i)) + '\n')
	
run_model(individual_model, test_data, "Subject_7_pred.csv")

s2_batch, s2_label = load_data('./data/part1/Subject_2_part1.csv', './data/part1/list2_part1.csv')
train_data, train_labels, test_data, test_labels = kFold(s2_batch, s2_label)

with open("Subject_2_gold.csv", 'w') as file:
	for i in test_labels:
		file.write(str(int(i)) + '\n')
	
run_model(individual_model, test_data, "Subject_2_pred.csv")

''' Individual Test Code '''
test_batch = load_test_data("data/final_test/subject2/subject2_instances.csv")
run_model(individual_model, test_batch, "results/individual1_pred3.csv")

test_batch = load_test_data("data/final_test/subject7/subject7_instances.csv")
run_model(individual_model, test_batch, "results/individual2_pred3.csv")

''' General Population Training Code '''
w = np.zeros(56, dtype=float)                      # Initialize w = [0, ...0]
learning_rate = 0.000000000000001				   # e-15

print("\nGeneral Population\n")
print("Subject 1")
s1_batch, s1_label = load_data('./data/part2/Subject_1.csv', './data/part2/list_1.csv')
train_data, train_labels, test_data, test_labels = kFold(s1_batch, s1_label)
w = batch_gradient_descent(itr, learning_rate, train_data, train_labels, test_data, test_labels, w)

print("\nSubject 4")
s4_batch, s4_label = load_data('./data/part2/Subject_4.csv', './data/part2/list_4.csv')
train_data, train_labels, test_data, test_labels = kFold(s4_batch, s4_label)
w = batch_gradient_descent(itr, learning_rate, train_data, train_labels, test_data, test_labels, w)

print("\nSubject 6")
s6_batch, s6_label = load_data('./data/part2/Subject_6.csv', './data/part2/list_6.csv')
train_data, train_labels, test_data, test_labels = kFold(s6_batch, s6_label)
w = batch_gradient_descent(itr, learning_rate, train_data, train_labels, test_data, test_labels, w)

with open("Subject_6_gold.csv", 'w') as file:
	for i in test_labels:
		#print(i)
		file.write(str(int(i)) + '\n')
		
run_model(w, test_data, "Subject_6_pred.csv")

print("\nSubject 9")
s9_batch, s9_label = load_data('./data/part2/Subject_9.csv', './data/part2/list_9.csv')
train_data, train_labels, test_data, test_labels = kFold(s9_batch, s9_label)
general_population_model = batch_gradient_descent(itr, learning_rate, train_data, train_labels, test_data, test_labels, w)

with open("Subject_9_gold.csv", 'w') as file:
	for i in test_labels:
		#print(i)
		file.write(str(int(i)) + '\n')
		
run_model(w, test_data, "Subject_9_pred.csv")

''' General Population Test Code '''
test_batch = load_test_data("data/final_test/general/general_test_instances.csv")
run_model(general_population_model, test_batch, "results/general_pred3.csv")