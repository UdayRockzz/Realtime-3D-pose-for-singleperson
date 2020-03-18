import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import tensorflow as tf
import data_utils
import viz
import re
import cameras
import json
import os
from predict_3dpose import create_model
import cv2
import imageio
import time
import logging
import glob
import csv
import xlsxwriter


FLAGS = tf.app.flags.FLAGS

order = [15, 12, 25, 26, 27, 17, 18, 19, 1, 2, 3, 6, 7, 8]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_maxvalue():
    for center in centers3:
        if center == (0, 0):
            continue
        min_xy.append(sys.float_info.max)
        min_vex.append((0, 0))
        p_vex.append((0, 0, 0))

def main(_):
    done = []

    enc_in = np.zeros((1, 64))
    enc_in[0] = [0 for i in range(64)]

    actions = data_utils.define_actions(FLAGS.action)


    SUBJECT_IDS = [1, 5, 6, 7, 8, 9, 11]
    rcams = cameras.load_cameras(FLAGS.cameras_path, SUBJECT_IDS)
    train_set_2d, test_set_2d, data_mean_2d, data_std_2d, dim_to_ignore_2d, dim_to_use_2d = data_utils.read_2d_predictions(
        actions, FLAGS.data_dir)
    train_set_3d, test_set_3d, data_mean_3d, data_std_3d, dim_to_ignore_3d, dim_to_use_3d, train_root_positions, test_root_positions = data_utils.read_3d_data(
        actions, FLAGS.data_dir, FLAGS.camera_frame, rcams, FLAGS.predict_14)

    device_count = {"GPU": 0}
    png_lib = []
    with tf.Session(config=tf.ConfigProto(
            device_count=device_count,
            allow_soft_placement=True)) as sess:
        #plt.figure(3)
        batch_size = 128
        model = create_model(sess, actions, batch_size)
        rows = 0
        filename= "Realtimedata.xlsx"
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        while True:
            key = cv2.waitKey(1) & 0xFF
            #logger.info("start reading data")
            # check for other file types
            list_of_files = glob.iglob("{0}/*".format(openpose_output_dir))  # You may use iglob in Python3
            latest_file = ""
            try:
                latest_file = max(list_of_files, key=os.path.getctime)
            except ValueError:
                #empthy dir
                pass
            if not latest_file:
                continue
            try:
                _file = file_name = latest_file
                print (latest_file)
                if not os.path.isfile(_file): raise Exception("No file found!!, {0}".format(_file))
                data = json.load(open(_file))
                #take first person
                _data = data["people"][0]["pose_keypoints_2d"]
                xy = []
                #ignore confidence score
                """for o in range(0,len(_data),3):
                    xy.append(_data[o])
                    xy.append(_data[o+1])"""
                if len(_data)>=53:
                    #openpose incl. confidence score
                    #ignore confidence score
                    for o in range(0,len(_data),3):
                        xy.append(_data[o])
                        xy.append(_data[o+1])
                else:
                    #tf-pose-estimation
                    xy = _data


                frame_indx = re.findall("(\d+)", file_name)
                frame = int(frame_indx[0])

                joints_array = np.zeros((1, 36))
                joints_array[0] = [0 for i in range(36)]
                for o in range(len(joints_array[0])):
                    #feed array with xy array
                    joints_array[0][o] = xy[o]
                _data = joints_array[0]
                # mapping all body parts or 3d pose offline format
                for i in range(len(order)):
                    for j in range(2):
                        # create encoder input
                        enc_in[0][order[i] * 2 + j] = _data[i * 2 + j]
                for j in range(2):
                    # Hip
                    enc_in[0][0 * 2 + j] = (enc_in[0][1 * 2 + j] + enc_in[0][6 * 2 + j]) / 2
                    # Neck/Nose
                    enc_in[0][14 * 2 + j] = (enc_in[0][15 * 2 + j] + enc_in[0][12 * 2 + j]) / 2
                    # Thorax
                    enc_in[0][13 * 2 + j] = 2 * enc_in[0][12 * 2 + j] - enc_in[0][14 * 2 + j]

                # set spine
                spine_x = enc_in[0][24]
                spine_y = enc_in[0][25]

                enc_in = enc_in[:, dim_to_use_2d]
                mu = data_mean_2d[dim_to_use_2d]
                stddev = data_std_2d[dim_to_use_2d]
                enc_in = np.divide((enc_in - mu), stddev)

                dp = 1.0
                dec_out = np.zeros((1, 48))
                dec_out[0] = [0 for i in range(48)]
                _, _, poses3d = model.step(sess, enc_in, dec_out, dp, isTraining=False)
                all_poses_3d = []
                enc_in = data_utils.unNormalizeData(enc_in, data_mean_2d, data_std_2d, dim_to_ignore_2d)
                poses3d = data_utils.unNormalizeData(poses3d, data_mean_3d, data_std_3d, dim_to_ignore_3d)
                gs1 = gridspec.GridSpec(1, 1)
                gs1.update(wspace=-0.00, hspace=0.05)  # set the spacing between axes.
                plt.axis('off')
                all_poses_3d.append( poses3d )
                enc_in, poses3d = map( np.vstack, [enc_in, all_poses_3d] )
                subplot_idx, exidx = 1, 1
                _max = 0
                _min = 10000

                for i in range(poses3d.shape[0]):
                    for j in range(32):
                        tmp = poses3d[i][j * 3 + 2]
                        poses3d[i][j * 3 + 2] = poses3d[i][j * 3 + 1]
                        poses3d[i][j * 3 + 1] = tmp
                        if poses3d[i][j * 3 + 2] > _max:
                            _max = poses3d[i][j * 3 + 2]
                        if poses3d[i][j * 3 + 2] < _min:
                            _min = poses3d[i][j * 3 + 2]

                for i in range(poses3d.shape[0]):
                    for j in range(32):
                        poses3d[i][j * 3 + 2] = _max - poses3d[i][j * 3 + 2] + _min
                        poses3d[i][j * 3] += (spine_x - 630)
                        poses3d[i][j * 3 + 2] += (500 - spine_y)

                for val in min_vex:
                            # f.write(str(val) + ' ' + str(p_vex[i]) + '');
                            # gait_list1.append({'IX': "%i" % val[0],
                            #                     'IY': "%i" % val[1],
                            #                     'Ix': "%i" % p_vex[i][0],
                            #                     'Iy': "%i" % p_vex[i][1],
                            #                     'Iz': "%i" % p_vex[i][2],
                            # })
                    gait_list1.append(val[0])
                    gait_list1.append(val[1])
                    gait_list1.append(p_vex[i][0])
                    gait_list1.append(p_vex[i][1])
                    gait_list1.append(p_vex[i][2])


                    points.append(" %f %f %f %d %d %d 0\n" % (p_vex[i][0], p_vex[i][1], p_vex[i][2], 0, 255, 0))
                    x.append(p_vex[i][0])
                    y.append(p_vex[i][1])
                    z.append(p_vex[i][2])
                    i = i + 1

                # Plot 3d predictions
                ax = plt.subplot(gs1[subplot_idx - 1], projection='3d')
                ax.view_init(18, -70)
                logger.debug(np.min(poses3d))
                if np.min(poses3d) < -1000 and frame != 0:
                    poses3d = before_pose

                p3d = poses3d
                '''gait_list1 = []
                #enter file path below
                with open('key_joint_info.csv', 'w', newline='') as myfile:
                    gait_list2.append(gait_list1)
                    data1 = pd.DataFrame(gait_list2)
                    wr = csv.writer(myfile, dialect = 'key_joint_info.csv' )
                    wr.writerow(p3d)
                    wb.save(key_joint_info.csv)'''

                viz.show3Dpose(p3d, ax, lcolor="#9b59b6", rcolor="#2ecc71")
                col = 0
                for i in p3d[0]:
                    worksheet.write(rows,col,i)
                    col += 1
                    #.append(i)
                rows += 1
                before_pose = poses3d
                pngName = '{}_keypoints.png'.format(str(frame))
                plt.savefig(pngName)

                #plt.show()
                img = cv2.imread(pngName,0)
                rect_cpy = img.copy()
                cv2.imshow('3d-pose-realtime', rect_cpy)
                done.append(file_name)
                if key == ord('q'):
                    break
            except Exception as e:
                print (e)

        sess.close()



if __name__ == "__main__":

    openpose_output_dir = FLAGS.pose_estimation_json

    level = {0:logging.ERROR,
             1:logging.WARNING,
             2:logging.INFO,
             3:logging.DEBUG}

    logger.setLevel(level[FLAGS.verbose])


    tf.app.run()
