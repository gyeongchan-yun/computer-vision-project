from __future__ import print_function
import os,time,cv2, sys, math
import tensorflow as tf
import tensorflow.contrib.slim as slim
import numpy as np
import time, datetime

from helper import *
from utils import *

import matplotlib.pyplot as plt

from FC_DenseNet_Tiramisu import build_fc_densenet

# Count total number of parameters in the model
def count_params():
    total_parameters = 0
    for variable in tf.trainable_variables():
        # shape is an array of tf.Dimension
        shape = variable.get_shape()
        # print(shape)
        # print(len(shape))
        variable_parameters = 1
        for dim in shape:
            # print(dim)
            variable_parameters *= dim.value
        # print(variable_parameters)
        total_parameters += variable_parameters
    print("This model has %d trainable parameters"% (total_parameters))

# Get a list of the training, validation, and testing file paths
def prepare_data(dataset_dir="CamVid"):
    train_input_names=[]
    train_output_names=[]
    val_input_names=[]
    val_output_names=[]
    test_input_names=[]
    test_output_names=[]
    for file in os.listdir(dataset_dir + "/train"):
      cwd = os.getcwd()
      train_input_names.append(cwd + "/" + dataset_dir + "/train/" + file)
    for file in os.listdir(dataset_dir + "/train_labels"):
      cwd = os.getcwd()
      train_output_names.append(cwd + "/" + dataset_dir + "/train_labels/" + file)
    for file in os.listdir(dataset_dir + "/val"):
      cwd = os.getcwd()
      val_input_names.append(cwd + "/" + dataset_dir + "/val/" + file)
    for file in os.listdir(dataset_dir + "/val_labels"):
      cwd = os.getcwd()
      val_output_names.append(cwd + "/" + dataset_dir + "/val_labels/" + file)
    for file in os.listdir(dataset_dir + "/test"):
      cwd = os.getcwd()
      test_input_names.append(cwd + "/" + dataset_dir + "/test/" + file)
    for file in os.listdir(dataset_dir + "/test_labels"):
      cwd = os.getcwd()
      test_output_names.append(cwd + "/" + dataset_dir + "/test_labels/" + file)
    return train_input_names,train_output_names, val_input_names, val_output_names, test_input_names, test_output_names

# Load the data
print("Loading the data ...")
train_input_names,train_output_names, val_input_names, val_output_names, test_input_names, test_output_names = prepare_data()


print("Setting up training procedure ...")
input = tf.placeholder(tf.float32,shape=[None,None,None,3])
output = tf.placeholder(tf.float32,shape=[None,None,None,12])
network = build_fc_densenet(input, preset_model = 'FC-DenseNet103')

loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=network, labels=output))

opt = tf.train.RMSPropOptimizer(learning_rate=0.001, decay=0.995).minimize(loss, var_list=[var for var in tf.trainable_variables()])

### Execution parameters ###
is_training = True
num_epochs = 110
continue_training = False
class_names_string = "Sky, Building, Pole, Road, Pavement, Tree, SignSymbol, Fence, Car, Pedestrian, Bicyclist, Unlabelled"
class_names_list = ["Sky", "Building", "Pole", "Road", "Pavement", "Tree", "SignSymbol", "Fence", "Car", "Pedestrian", "Bicyclist", "Unlabelled"]


config = tf.ConfigProto()
config.gpu_options.allow_growth = True
sess=tf.Session(config=config)

saver=tf.train.Saver(max_to_keep=1000)
sess.run(tf.global_variables_initializer())

count_params()

if continue_training or not is_training:
    print('Loaded latest model checkpoint')
    saver.restore(sess, "checkpoints/latest_model.ckpt")

avg_scores_per_epoch = []

# To use TensorBoard.
board_dir = './board/fc-densent-org'
writer = tf.summary.FileWriter(board_dir, sess.graph)

if is_training:

    print("***** Begin training *****")

    avg_loss_per_epoch = []

    # Do the training here
    for epoch in range(0, num_epochs):

        current_losses = []

        input_image_names=[None]*len(train_input_names)
        output_image_names=[None]*len(train_input_names)

        cnt=0
        for id in np.random.permutation(len(train_input_names)):
            start_time=time.time()
            if input_image_names[id] is None:

                input_image_names[id] = train_input_names[id]
                output_image_names[id] = train_output_names[id]
                input_image = np.expand_dims(np.float32(cv2.imread(input_image_names[id],-1)[:352, :480]),axis=0)/255.0
                output_image = np.expand_dims(np.float32(one_hot_it(labels=cv2.imread(output_image_names[id],-1)[:352, :480])), axis=0)

                # ***** THIS CAUSES A MEMORY LEAK AS NEW TENSORS KEEP GETTING CREATED *****
                # input_image = tf.image.crop_to_bounding_box(input_image, offset_height=0, offset_width=0, 
                #                         target_height=352, target_width=480).eval(session=sess)
                # output_image = tf.image.crop_to_bounding_box(output_image, offset_height=0, offset_width=0, 
                #                         target_height=352, target_width=480).eval(session=sess)
                # ***** THIS CAUSES A MEMORY LEAK AS NEW TENSORS KEEP GETTING CREATED *****

                # memory()

                _, current = sess.run([opt,loss],feed_dict={input:input_image,output:output_image})
                current_losses.append(current)
                cnt = cnt + 1
                if cnt % 20 == 0:
                    message = "Epoch = %d Count = %d Loss = %.2f Time = %.2f" % (epoch, cnt, current, time.time() - start_time)
                    LOG(message)

        mean_loss = np.mean(current_losses)
        avg_loss_per_epoch.append(mean_loss)

        # Create directories if needed
        if not os.path.isdir("%s/%04d"%("checkpoints",epoch)):
            os.makedirs("%s/%04d"%("checkpoints",epoch))

        saver.save(sess,"%s/latest_model.ckpt"%"checkpoints")
        saver.save(sess,"%s/%04d/model.ckpt"%("checkpoints",epoch))


        target=open("%s/%04d/val_scores.txt"%("checkpoints",epoch),'w')
        target.write("val_name, avg_accuracy, %s\n" % (class_names_string))

        val_indices = [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
        scores_list = []
        class_scores_list = []



        # Do the validation on a small set of validation images
        for ind in val_indices:
            input_image = np.expand_dims(np.float32(cv2.imread(val_input_names[ind],-1)[:352, :480]),axis=0)/255.0
            start_time = time.time()
            output_image = sess.run(network,feed_dict={input:input_image})


            output_image = np.array(output_image[0,:,:,:])
            output_image = reverse_one_hot(output_image)
            out = output_image
            output_image = colour_code_segmentation(output_image)

            ground_truth = cv2.imread(val_output_names[ind],-1)[:352, :480]

            accuracy = compute_avg_accuracy(out, ground_truth)
            class_accuracies = compute_class_accuracies(out, ground_truth)
            file_name  =filepath_to_name(val_input_names[ind])
            target.write("%s, %f"%(val_input_names[ind], accuracy))
            for item in class_accuracies:
                target.write(", %f"%(item))
            target.write("\n")

            scores_list.append(accuracy)
            class_scores_list.append(class_accuracies)

            ground_truth = colour_code_segmentation(np.expand_dims(ground_truth, axis=-1))

            file_name = os.path.basename(val_input_names[ind])
            file_name = os.path.splitext(file_name)[0]
            cv2.imwrite("%s/%04d/%s_pred.png"%("checkpoints",epoch, file_name),np.uint8(output_image))
            cv2.imwrite("%s/%04d/%s_ground_truth.png"%("checkpoints",epoch, file_name),np.uint8(ground_truth))


        target.close()

        avg_score = np.mean(scores_list)
        class_avg_scores = np.mean(class_scores_list, axis=0)
        avg_scores_per_epoch.append(avg_score)
        print("\nAverage validation accuracy for epoch # %04d = %f"% (epoch, avg_score))
        print("Average per class validation accuracies for epoch # %04d:"% (epoch))
        for index, item in enumerate(class_avg_scores):
            print("%s = %f" % (class_names_list[index], item))

        scores_list = []

    fig = plt.figure(figsize=(11,8))
    ax1 = fig.add_subplot(111)


    ax1.plot(range(num_epochs), avg_scores_per_epoch)
    ax1.set_title("Average validation accuracy vs epochs")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Avg. val. accuracy")


    plt.savefig('accuracy_vs_epochs.png')

    plt.clf()

    ax1 = fig.add_subplot(111)


    ax1.plot(range(num_epochs), avg_loss_per_epoch)
    ax1.set_title("Average loss vs epochs")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Current loss")

    plt.savefig('loss_vs_epochs.png')

else:
    print("***** Begin testing *****")

    # Create directories if needed
    if not os.path.isdir("%s"%("Test")):
            os.makedirs("%s"%("Test"))

    target=open("%s/test_scores.txt"%("Test"),'w')
    target.write("test_name, avg_accuracy, %s\n" % (class_names_string))
    scores_list = []
    class_scores_list = []

    # Run testing on ALL test images
    for ind in range(len(test_input_names)):
        input_image = np.expand_dims(np.float32(cv2.imread(test_input_names[ind],-1)[:352, :480]),axis=0)/255.0
        start_time = time.time()
        output_image = sess.run(network,feed_dict={input:input_image})


        output_image = np.array(output_image[0,:,:,:])
        output_image = reverse_one_hot(output_image)
        out = output_image
        output_image = colour_code_segmentation(output_image)

        ground_truth = cv2.imread(test_output_names[ind],-1)[:352, :480]

        accuracy = compute_avg_accuracy(out, ground_truth)
        class_accuracies = compute_class_accuracies(out, ground_truth)
        file_name = filepath_to_name(test_input_names[ind])
        target.write("%s, %f"%(file_name, accuracy))
        for item in class_accuracies:
            target.write(", %f"%(item))
        target.write("\n")

        scores_list.append(accuracy)
        class_scores_list.append(class_accuracies)

        ground_truth = colour_code_segmentation(np.expand_dims(ground_truth, axis=-1))

        cv2.imwrite("%s/%s_pred.png"%("Test", file_name),np.uint8(output_image))
        cv2.imwrite("%s/%s_ground_truth.png"%("Test", file_name),np.uint8(ground_truth))


    target.close()

    avg_score = np.mean(scores_list)
    class_avg_scores = np.mean(class_scores_list, axis=0)
    print("Average test accuracy = ", avg_score)
    print("Average per class test accuracies = \n")
    for index, item in enumerate(class_avg_scores):
        print("%s = %f" % (class_names_list[index], item))



