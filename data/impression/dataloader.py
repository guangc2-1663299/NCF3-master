import os
import numpy as np
import pandas as pd
import scipy.sparse as sp
import torch.utils.data as data
from tqdm import tqdm


def load_all(params):
    """ We load all the three file here to save time in each epoch. """
    train_data = pd.read_csv(os.path.join('data', params.data_dir, params.train_rating), dtype={0: np.int32, 1: np.int32})
    train_data = train_data[['user_index','mlog_index','isClick']]

    user_num = train_data['user_index'].nunique()
    item_num = train_data['mlog_index'].nunique()

    train_data = train_data.values.tolist()

    print('load ratings as a dok matrix')
    train_mat = sp.dok_matrix((user_num, item_num), dtype=np.float32)
    for x in tqdm(train_data):
        train_mat[x[0], x[1]] = x[2]

    test_data = pd.read_csv(os.path.join('data', params.data_dir, params.test_negative), dtype={0: np.int32, 1: np.int32})
    test_data = test_data[['user_index','mlog_index']].values.tolist()
    return train_data, test_data, user_num, item_num, train_mat


class TrainSet(data.Dataset):
    def __init__(self, features, num_item, train_mat=None, num_ng=0):
        super(TrainSet, self).__init__()
        """ Note that the labels are only useful when training, we thus 
            add them in the ng_sample() function.
        """
        #self.features_ps = features
        features_ps = []
        for x in features:
            features_ps.append(x[:2])
        self.features_ps = features_ps
        self.num_item = num_item
        self.train_mat = train_mat
        self.num_ng = num_ng
        self.labels = [0 for _ in range(len(features))]

    def ng_sample(self):
        self.features_ng = []
        for x in self.features_ps:
            u = x[0]
            for t in range(self.num_ng):
                j = np.random.randint(self.num_item)
                while (u, j) in self.train_mat:
                    j = np.random.randint(self.num_item)
                self.features_ng.append([u, j])

        #labels_ps = [1 for _ in range(len(self.features_ps))]
        labels_ps = []
        for x in train_data:
            labels_ps.append(x[2])
        labels_ng = [0 for _ in range(len(self.features_ng))]
        self.features_fill = self.features_ps + self.features_ng
        self.labels_fill = labels_ps + labels_ng

    def __len__(self):
        return (self.num_ng + 1) * len(self.features_ps)

    def __getitem__(self, idx):
        user = self.features_fill[idx][0]
        item = self.features_fill[idx][1]
        label = self.labels_fill[idx]
        return user, item, label


class TestSet(data.Dataset):
    def __init__(self, features, num_item, num_ng=0):
        super(TestSet, self).__init__()
        """ Note that the labels are only useful when training, we thus 
            add them in the ng_sample() function.
        """
        self.features_ps = features
        self.num_item = num_item
        self.num_ng = num_ng

    def __len__(self):
        return (self.num_ng + 1) * len(self.features_ps)

    def __getitem__(self, idx):
        user = self.features_ps[idx][0]
        item = self.features_ps[idx][1]
        return user, item
