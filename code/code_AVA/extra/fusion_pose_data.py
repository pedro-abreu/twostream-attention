import csv
import numpy as np
import cv2
import sys
import os
import glob
import utils


def load_split(ids, labels, dim, n_channels, of_len, pose_dir, rgb_dir, flow_dir, encoding, set_type, train=True):
    'Generates data containing batch_size samples'

    sep = "@"
    r_dir = rgb_dir + set_type + "/"
    pose_dir = pose_dir + "/" + set_type + "/"
    # Initialization, assuming its bidimensional (for now)
    X_rgb = np.empty([len(ids), dim[0], dim[1], 3])
    X_flow = np.empty([len(ids), dim[0], dim[1], 20])
    X_pose = np.empty([len(ids), 300, 300, 3])
    ypose = np.empty(len(ids))
    yobject = []
    yhuman = []

    # Generate data
    for i, ID in enumerate(ids):
        # Get image from ID (since we are using opencv we get np array)
        split_id = ID.split(sep)
        vid_name = split_id[0]
        keyframe = split_id[1]
        bb_top_x = float(split_id[2])
        bb_top_y = float(split_id[3])
        bb_bot_x = float(split_id[4])
        bb_bot_y = float(split_id[5])
        vid_name = vid_name + "_" + keyframe
        bbs = str(bb_top_x) + "_" + str(bb_top_y) + "_" + str(bb_bot_x) + "_" + str(bb_bot_y)
        rgb_frame = split_id[6]
        # Many names: 12 = 25 = 1, 17 = 35 = 2, 22 = 45 = 3, 27 = 55 = 4, 32 = 65 = 5
        optical_flow_frame = 12 + (int(rgb_frame) - 1) * 5  # conversion of rgb to of name format
        # Is this the correct format? Yes, the format has to use _
        img_name = r_dir + vid_name + "_" + bbs + "/frames" + rgb_frame + ".jpg"
        if not os.path.exists(img_name):
            print(img_name)
            print("[Error] File does not exist!")
            sys.exit(0)

        img = cv2.imread(img_name)
        # Store sample
        X_rgb[i, ] = img

        pose_name = pose_dir + vid_name + "_" + bbs + "/frames" + rgb_frame + ".jpg"
        if not os.path.exists(pose_name):
            print(pose_name)
            print("[Error] File does not exist!")
            sys.exit(0)

        img = cv2.imread(pose_name)
        X_pose[i, ] = img

        of_volume = np.zeros(shape=(dim[0], dim[1], 20))
        v = 0
        for fn in range(-of_len // 2, of_len // 2):
            of_frame = optical_flow_frame + fn
            if encoding == "grayscale":
                x_img_name = flow_dir + set_type + "/x/" + vid_name + "/frame" + str('{:06}'.format(of_frame)) + ".jpg"
                x_img = cv2.imread(x_img_name, cv2.IMREAD_GRAYSCALE)
                if x_img is None:
                    continue
                y_img_name = flow_dir + set_type + "/y/" + vid_name + "/frame" + str('{:06}'.format(of_frame)) + ".jpg"
                y_img = cv2.imread(y_img_name, cv2.IMREAD_GRAYSCALE)
                if y_img is None:
                    continue
            elif encoding == "rgb":
                f_img_name = flow_dir + set_type + "/" + vid_name + "/frame" + str('{:06}'.format(of_frame)) + ".jpg"
                # print(f_img_name)
                f_img = cv2.imread(f_img_name)
                try:
                    # TODO this is an awful programming practice
                    # but it might be possible that some flow images don't have a last image (frame 36) due to opencv/ffmpeg imprecision
                    x_img = f_img[:, :, 0]
                    y_img = f_img[:, :, 1]
                except:
                    pass
                f_img = None

            # Put them in img_volume (x then y)
            of_volume[:, :, v] = x_img
            v += 1
            of_volume[:, :, v] = y_img
            v += 1
        X_flow[i, ] = of_volume
        if train is True:
            ypose[i] = labels[ID]['pose']
            yobject.append(labels[ID]['human-object'])
            yhuman.append(labels[ID]['human-human'])

    return X_rgb, X_flow, X_pose, ypose, yobject, yhuman


def get_AVA_set(classes, filename, train):
    sep = "@"
    id_list = []
    start_frame = 1
    end_frame = 5
    jump_frames = 1  # Keyframe will be 3

    # Load all lines of filename
    # For training we use a csv file

    with open(filename) as csvDataFile:
        csvReader = csv.reader(csvDataFile)
        for row in csvReader:
            video = row[0]
            kf_timestamp = row[1]

            # action = row[6]
            bb_top_x = row[2]
            bb_top_y = row[3]
            bb_bot_x = row[4]
            bb_bot_y = row[5]
            # This is due to the behav of range
            for frame in range(start_frame, end_frame + jump_frames, jump_frames):
                # Append to the dictionary
                ID = video + sep + kf_timestamp.lstrip("0") + \
                    sep + str(bb_top_x) + sep + str(bb_top_y) + sep + \
                    str(bb_bot_x) + sep + str(bb_bot_y) + sep + str(frame)
                id_list.append(ID)

    id_list = list(set(id_list))
    return id_list


def get_AVA_labels(classes, partition, set_type, filename, soft_sigmoid=False):
    sep = "@"  # Must not exist in any of the IDs

    # HUMAN_HUMAN_CLASSES = 17
    labels = {}
    # Parse partition and create a correspondence to an integer in classes
    class_ids = classes['label_id']
    print("Generating labels: " + str(len(class_ids)))
    # Find entries in the csv that correspond
    start_frame = 1
    end_frame = 5
    jump_frames = 1  # Keyframe will be 3
    for entry in partition[set_type]:
        labels[entry] = {}
        # It might as well be a single entry here and not a list
        labels[entry]['pose'] = -1
        labels[entry]['human-object'] = []
        labels[entry]['human-human'] = []
    with open(filename) as csvDataFile:
        csvReader = csv.reader(csvDataFile)
        for row in csvReader:
            # Read rows
            video = row[0]
            kf = row[1]
            bb_top_x = row[2]
            bb_top_y = row[3]
            bb_bot_x = row[4]
            bb_bot_y = row[5]
            bbs = str(bb_top_x) + sep + str(bb_top_y) + \
                sep + str(bb_bot_x) + sep + str(bb_bot_y)
            action = int(row[6])
            # Construct IDs
            for frame in range(start_frame, end_frame + jump_frames, jump_frames):
                label_ID = video + sep + \
                    kf.lstrip("0") + sep + bbs + sep + str(frame)
                if action <= utils.POSE_CLASSES:
                    labels[label_ID]['pose'] = action - 1
                elif action > utils.POSE_CLASSES and action <= utils.POSE_CLASSES + utils.OBJ_HUMAN_CLASSES:
                    labels[label_ID]['human-object'].append(action - 1)
                else:
                    labels[label_ID]['human-human'].append(action - 1)
    return labels
