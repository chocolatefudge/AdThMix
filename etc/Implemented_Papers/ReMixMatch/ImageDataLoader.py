from PIL import Image
import os
import os.path
import torch.utils.data
import torchvision.transforms as transforms
import numpy as np
import torch

def default_image_loader(path):
    return Image.open(path).convert('RGB')

class TransformTwice:
    def __init__(self, transform):
        self.transform = transform
    def __call__(self, inp):
        out1 = self.transform(inp)
        out2 = self.transform(inp)
        return out1, out2

class TransformFourth:
    def __init__(self, transform):
        self.transform = transform
    def __call__(self, inp):
        out1 = self.transform(inp)
        out2 = self.transform(inp)
        out3 = self.transform(inp)
        out4 = self.transform(inp)
        return out1, out2, out3, out4

class SimpleImageLoader(torch.utils.data.Dataset):
    def __init__(self, rootdir, split, ids=None, transform=None,ra=None, loader=default_image_loader):
        if split == 'test':
            self.impath = os.path.join(rootdir, 'test_data')
            meta_file = os.path.join(self.impath, 'test_meta.txt')
        else:
            self.impath = os.path.join(rootdir, 'train/train_data')
            meta_file = os.path.join(rootdir, 'train/train_label')

        imnames = []
        imclasses = []

        with open(meta_file, 'r') as rf:
            for i, line in enumerate(rf):
                if i == 0:
                    continue
                instance_id, label, file_name = line.strip().split()
                if int(label) == -1 and (split != 'unlabel' and split != 'test'):
                    continue
                if int(label) != -1 and (split == 'unlabel' or split == 'test'):
                    continue
                if (ids is None) or (int(instance_id) in ids):
                    if os.path.exists(os.path.join(self.impath, file_name)):
                        imnames.append(file_name)
                        if split == 'train' or split == 'val':
                            imclasses.append(int(label))

        self.transform_w = transform
        if ra is None:
            self.transform_s = transform
        else:
            self.transform_s = transforms.Compose([ra, transform])
        self.TransformTwice = TransformTwice(self.transform_s)
        self.TransformFourth = TransformFourth(self.transform_s)
        self.loader = loader
        self.split = split
        self.imnames = imnames
        self.imclasses = imclasses

    def __getitem__(self, index):
        filename = self.imnames[index]
        img = self.loader(os.path.join(self.impath, filename))

        if self.split == 'test':
            if self.transform_w is not None:
                img = self.transform_w(img)
            return img
        elif self.split != 'unlabel':
            if self.transform_s is not None:
                img = self.transform_s(img)
            label = self.imclasses[index]
            return img, label
        else:
            #img1, img2, img3, img4 = self.TransformFourth(img)
            img1, img2 = self.TransformTwice(img)
            imgw = self.transform_w(img)
            return img1, img2, imgw

    def __len__(self):
        return len(self.imnames)
