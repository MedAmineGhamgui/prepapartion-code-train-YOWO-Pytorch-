import os
import random
import numpy as np
import cv2
import torch
from torch.utils.data import Dataset
from PIL import Image

from pytorchvideo.transforms.transforms import UniformTemporalSubsample
from pytorchvideo.data.encoded_video import EncodedVideo



# Dataset for AVA
class AVA_Dataset(Dataset):
    def __init__(self,
                 cfg,
                 is_train=False,
                 img_size=224,
                 transform=None,
                 len_clip=16,
                 sampling_rate=1):
        self._downsample = 4
        self.num_classes = 2          
        
        if is_train:
            self.pathhhhh = os.path.join("/kaggle/input/train-csv-version1/train.csv")
            # self.exclusion_file = os.path.join("/kaggle/input/exclusion-version1/ava_train_excluded_timestamps_v2.2.csv")
        else:
            self.pathhhhh = os.path.join("/kaggle/input/validationcsv-version1/val.csv")
            # self.exclusion_file = os.path.join("/kaggle/input/exclusion-version1/ava_train_excluded_timestamps_v2.2.csv")

        self.transform = transform
        self.is_train = is_train
        
        self.img_size = img_size
        self.len_clip = len_clip
        self.sampling_rate = sampling_rate
        self.seq_len = self.len_clip * self.sampling_rate
        # load ava data
        self._load_data()

    
    
  

    import cv2


    @staticmethod
    def extract_frames(video_path):
        video = EncodedVideo.from_path(video_path)
        return video


    def parse_csv_to_dict(self):
        result_dict = {}

        with open(self.pathhhhh, "r") as f:
            f.readline()  # Ignorer la première ligne (en-tête)

            for line in f:
                row = line.strip().split(",")
                key = row[0]
                key1 = row[1]
                if key not in result_dict:
                    result_dict[key] = {}

                path = "/kaggle/input/data-faux-train-yowo/data_faux/" + key + "/" + key1 + ".mp4"
                result_dict[key][key1] = self.extract_frames(path)

        return result_dict

    
    def get_boxes_to_seq(self):

        result_dict = {}

        with open(self.pathhhhh, "r") as f:
            f.readline()
            for line in f:

                row = line.strip().split(",")
                key = row[0]
                key1 = row[1]
                if key not in result_dict:
                    result_dict[key] = {}  
                if key1 not in result_dict[key]:
                    result_dict[key][key1] = []  
                result_dict[key][key1].append([row[2:6],row[6]])
        
        return result_dict
    #sortie de  get_boxes_to_seq entre de combiner_valeurs
    
    
    def combiner_valeurs(self):
        diction=self.get_boxes_to_seq()#diction 
        for keys in diction:
            for keys1 in diction[keys]:
                liste=diction[keys][keys1]
                result = {}
                for sous_liste in liste:
                    cle = tuple(map(float, sous_liste[0]))  # Conversion en float
                    valeur = int(sous_liste[1][0])  # Conversion en int
                    if cle in result:
                        result[cle].append(valeur)
                    else:
                        result[cle] = [valeur]

                resultat_final = [[list(k), v] for k, v in result.items()]
                diction[keys][keys1]=resultat_final
        return diction


    
    def _load_data(self):
        video_factory=self.parse_csv_to_dict()
        annotation_factory=self.combiner_valeurs()
        self.l_clip=[]
        self.l_boxes=[]
        self.l_name=[]
        for keys in annotation_factory:
            for keys1 in annotation_factory[keys]:
                self.l_clip.append(video_factory[keys][keys1])
                self.l_boxes.append(annotation_factory[keys][keys1])
                self.l_name.append([keys,keys1])
        video_factory = None
        annotation_factory=None
         
    def __len__(self):
        return len(self.l_boxes)


 




    def __getitem__(self, idx):
        # load a data
        frame_idx, video_clip, target = self.pull_item(idx)

        return frame_idx, video_clip, target
    


    def pull_item(self, idx):

            video_clip = self.l_clip[idx].get_clip(start_sec=0.0, end_sec=1.0)["video"].permute(1,0,2,3)
            video_clip=255-video_clip
            keyframe_info="self.l_clip[idx][-1]"

            # load a video clip
             
                
            oh = video_clip.size(2) 
            ow = video_clip.size(3)

            
            
            # Get boxes and labels for current clip.
            boxes = []
            labels = []
            for box_labels in self.l_boxes[idx]:
                bbox = box_labels[0]
                label = box_labels[1]
                multi_hot_label = np.zeros(1 +  self.num_classes)
                multi_hot_label[..., label] = 1.0

                boxes.append(bbox)
                labels.append(multi_hot_label[..., 1:].tolist())

            boxes = np.array(boxes).reshape(-1, 4)
            # renormalize bbox
            boxes[..., [0, 2]] *= ow
            boxes[..., [1, 3]] *= oh
            labels = np.array(labels).reshape(-1,  self.num_classes)

            # target: [N, 4 + C]
            target8 = np.concatenate([boxes, labels], axis=-1)
            # transform
            
            l_clip, target = self.transform(video_clip, target8)
            # reformat target
            target = {
                'boxes': target[:, :4].float(),  # [N, 4]
                'labels': target[:, 4:].long(),  # [N, C]
                'orig_size': [ow, oh],
                'video_idx': self.l_name[idx][0],
                'sec': self.l_name[idx][1],

            }

            return keyframe_info, l_clip, target



if __name__ == '__main__':
    import cv2
    from transforms import Augmentation, BaseTransform

    is_train = False
    img_size = 224
    len_clip = 16
    dataset_config = {

    }
    
    trans_config = {
        'pixel_mean': [0.45, 0.45, 0.45],
        'pixel_std': [0.225, 0.225, 0.225],
        'jitter': 0.2,
        'hue': 0.1,
        'saturation': 1.5,
        'exposure': 1.5
    }
    transform = Augmentation(
        img_size=img_size,
        pixel_mean=trans_config['pixel_mean'],
        pixel_std=trans_config['pixel_std'],
        jitter=trans_config['jitter'],
        saturation=trans_config['saturation'],
        exposure=trans_config['exposure']
        )
#     transform = BaseTransform(
#         img_size=img_size,
#         pixel_mean=trans_config['pixel_mean'],
#         pixel_std=trans_config['pixel_std']
#         )

    train_dataset = AVA_Dataset(
        cfg=dataset_config,
        is_train=is_train,
        img_size=img_size,
        transform=transform,
        len_clip=len_clip,
        sampling_rate=1
    )

    print("*************************************************************************************amine")
    print(type(train_dataset))
    print(len(train_dataset))
