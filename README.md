# Realtime-3D-pose-for-singleperson

## 2D Human Pose Estimation

First run the 2d pose estimator model for generating the 2D predictions 


Dependencies:


    •	python3
    
    •	tensorflow 1.4.1+
       
    •	opencv3, protobuf, python3-tk


git clone https://www.github.com/ildoonet/tf-openpose

cd tf-openpose

pip install -r requirements.txt


## Realtime
python run_webcam.py --model=mobilenet_thin --resize=432x368 --camera=0 --output_json /path/to/directory
  
  
## 3D Human Pose Estimation


Dependencies:


    •	H5py
    
    •	Tensorflow 1.0 or later
        
    •	Python 3
   
   
git clone https://github.com/Uday038/Realtime-3D-pose-for-singleperson.git

cd Realtime-3D-pose-for-singleperson

mkdir data

cd data

download human3.6M data from  https://drive.google.com/drive/folders/1HBGmdk9UyeOXKgqnt82GiP43SDIWcHc- and store in data folder

cd ..


## Training 
python train.py --camera_frame --residual --batch_norm --dropout 0.5 --max_norm –evaluateActionWise --use_2d


## Generating 3D predictions from 2D predictions
python pose3D_normal.py --camera_frame --residual --batch_norm --dropout 0.5 --max_norm --evaluateActionWise --use_sh --epochs 200 --load 4874200 --pose_estimation_json /path/to/json_directory


## Realtime
Python pose3D_realtime.py --camera_frame --residual --batch_norm --dropout 0.5 --max_norm --evaluateActionWise --use_sh --epochs 200 --load 4874200 --pose_estimation_json /path/to/json_directory
 
 
## Prerequisites
In order to run the model in realtime, first run the 2D pose estimator followed by 3D pose estimation model.

