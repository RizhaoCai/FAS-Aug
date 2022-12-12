"""
Evaluation metrics for binary classification
"""

import math
import numpy as np
import torch
import pdb
from utils.parse_video_info import parse_attr_from_video_name
import sklearn.metrics as metrics

def eval_stat(scores, labels, thr=0.5):
    # label 1 for the postive, and the label 2 for the negatvie
    # print(scores)
    pred = scores >= thr
    TN = np.sum((labels == 0) & (pred == False))  # True Negative   -- True Reject 
    FN = np.sum((labels == 1) & (pred == False))  # False Negative  -- False Reject
    FP = np.sum((labels == 0) & (pred == True))   # False Positive  -- False Accept
    TP = np.sum((labels == 1) & (pred == True))   # True Positive   -- True Accept
    # print("TN, FN, FP, TP: ",TN, FN, FP, TP)
    return TN, FN, FP, TP

def get_thresholds(scores, grid_density):
    """
        @scores: a vector of scores with shape [n,1] or [n,]
    """
    # uniform thresholds in [min, max]
    Min, Max = min(scores), max(scores)
    thresholds = []
    for i in range(grid_density + 1):
        thresholds.append(Min + i * (Max - Min) / float(grid_density))
    return thresholds


def get_eer_stats(scores, labels, grid_density = 100000):
    thresholds = get_thresholds(scores, grid_density)
    min_dist = 1.0
    min_dist_stats = []
    for thr in thresholds:
        TN, FN, FP, TP = eval_stat(scores, labels, thr)
        far = 0 if FP==0 else FP / float(TN + FP)  
        frr = 0 if FN==0 else FN / float(TP + FN)  
        dist = math.fabs(far - frr)
        if dist < min_dist:
            min_dist = dist
            min_dist_stats = [far, frr, thr]
    try:
        eer = (min_dist_stats[0] + min_dist_stats[1]) / 2.0
        thr = min_dist_stats[2]
    except:
        pdb.set_trace()
    # pdb.set_trace()
    return eer, thr

def get_min_hter(scores, labels, grid_density = 100000):
    thresholds = get_thresholds(scores, grid_density)
    min_hter = 1.0
    hter_thr = 0.5
    far_at_thr = 0.5
    frr_at_thr = 0.5
    for thr in thresholds:
        TN, FN, FP, TP = eval_stat(scores, labels, thr)
        far = 0 if FP==0 else FP / float(TN + FP)
        frr = 0 if FN==0 else FN / float(TP + FN)
        hter = (far+frr) / 2

        if hter < min_hter:
            min_hter = hter
            hter_thr = thr
            far_at_thr = far
            frr_at_thr = frr
    # TODO:
    return min_hter, hter_thr, far_at_thr, frr_at_thr

def get_hter_at_thr(scores, labels, thr):
    TN, FN, FP, TP = eval_stat(scores, labels, thr)
    far = FP / float(TN + FP)   
    frr = FN / float(TP + FN)
    hter = (far + frr) / 2.0
    return hter,far,frr

def get_accuracy(scores, labels, thr):
    TN, FN, FP, TP = eval_stat(scores, labels, thr)
    accuracy = float(TP + TN) / len(scores)
    return accuracy

def get_best_thr(scores, labels, grid_density = 10000):
    thresholds = get_thresholds(scores, grid_density)
    acc_best = 0.0
    for thr in thresholds:
        acc = get_accuracy(scores, labels, thr)
        if acc > acc_best:
            acc_best = acc
            thr_best = thr
    return thr_best, acc_best



#######################################################################################
###What is below are metrics function for multi-class classification###################
#######################################################################################

def get_accuracy_mc(scores,labels):
    """
        Get_accuracy_multi-class
        # scores: N-c shape: one-hot encoding
        # label: N-c shape:  one-hot encoding
    """ 
    assert scores.shape == labels.shape
    pred = np.argmax(scores,1)
    labels = np.argmax(labels,1)
    correct = pred==labels
    wrong = np.where(correct==False)
    correct_num = np.sum(correct)
    total_num = scores.shape[0]
    acc = correct_num / float(total_num)
    return acc, pred, wrong
    
def pick_up_false_classification_index(scores,labels,thr,):

    preds = scores >= thr
    fa_idx_list = []
    fr_idx_list = []

    for idx in range(len(preds)):
        fr = (labels[idx] == 1) & (preds[idx] == False)  # False Negative  -- False Reject
        fa = (labels[idx] == 0) & (preds[idx] == True)  # False Positive  -- False Accept

        if fa:
            fa_idx_list.append(idx)
        if fr:
            fr_idx_list.append(idx)
    misclassification_idx = fa_idx_list + fr_idx_list
    return misclassification_idx, fa_idx_list, fr_idx_list


def point_cloud_score(points):
    """

    :param points: shape -> [b, num_points, cordinates]
    :return: scores
    """
    mean_score = points[:,:,2].mean(dim=1) # shape -> [b]
    return mean_score


def get_cls_from_score_dict(score_dict, threshold):
    """

    :param score_dict: a dict that contains scores of different videos
    :param threshold:
    :return:
    """
    cls_dict = {}
    for key in score_dict:
        cls_dict[key] = score_dict[key]>threshold
    return cls_dict

def parse_cls_type_from_dict(cls_dict):
    """

    :param cls_dict:
    :return: cls_type: TN, FN, FP, TP
    """
    video_cls_type_dict = {}
    cls_type_dict = {
        'TN': [],
        'FP': [],
        'TP': [],
        'FN': []
    }

    for key in cls_dict:
        cls_pred_of_key = cls_dict[key]
        cls_type_dict[key] = list()
        video_info = parse_attr_from_video_name(key)
        if video_info['face_label'] is not 'real':
            video_label = 1
        else:
            video_label = 0

        for i in range(len(cls_pred_of_key.shape)):
            cls_pred = cls_pred_of_key[i]
            if video_label == 0 and cls_pred == 0:
                cls_type = 'TN' # True Negative / Reject


            elif video_label == 1 and cls_pred == 0:
                cls_type = 'FN'  # False Negative  -- False Reject

            elif video_label == 0 and cls_pred == 1:
                cls_type = 'FP' # False Positive  -- False Accept

            elif video_label == 1 and cls_pred == 1:
                cls_type = 'TP' # True Positive   -- True Accept

            video_cls_type_dict[key].append(cls_type)
            cls_type_dict[cls_type].append([cls_pred_of_key, i])

    return video_cls_type_dict, cls_type_dict


def metric_report_from_dict(scores_gt_dict, scores_pred_dict, thr):
    frame_pred_list = list()
    frame_label_list = list()
    video_pred_list = list()
    video_label_list = list()

    for key in scores_pred_dict.keys():
        num_frames = len(scores_pred_dict[key])
        avg_single_video_pred = sum(scores_pred_dict[key]) /num_frames
        avg_single_video_label = sum(scores_gt_dict[key]) / num_frames

        video_pred_list = np.append(video_pred_list, avg_single_video_pred).astype(np.float32)
        video_label_list = np.append(video_label_list, avg_single_video_label).astype(int)

        frame_pred_list = np.append(frame_pred_list, scores_pred_dict[key]).astype(np.float32)
        frame_label_list = np.append(frame_label_list, scores_gt_dict[key]).astype(int)

    frame_metrics = metric_report(frame_pred_list, frame_label_list, thr)
    video_metrics = metric_report(video_pred_list, video_label_list, thr)
    return frame_metrics, video_metrics


def metric_report(scores_pred, scores_gt, thr):
    fpr, tpr, threshold = metrics.roc_curve(scores_gt, scores_pred)
    auc = metrics.auc(fpr, tpr)

    eer, eer_thr = get_eer_stats(scores_pred, scores_gt)
    hter, far, frr = get_hter_at_thr(scores_pred, scores_gt, thr)
    hter05, far05, frr05 = get_hter_at_thr(scores_pred, scores_gt, 0.5)
    min_hter, hter_thr, far_at_thr, frr_at_thr = get_min_hter(scores_pred, scores_gt)

    metric_dict = {
        'AUC':auc,
        'EER': eer,
        'EER_THR': eer_thr,
        'HTER@THR': hter,
        'FAR@THR': far,
        'FRR@THR': frr,
        'THR': thr,
        'HTER@0.5': hter05,
        'FAR@0.5': far05,
        'FRR@0.5': frr05,
        'MIN_HTER': min_hter,
        'MIN_HTER_THR': hter_thr,
        'MIN_FAR_THR': far_at_thr,
        'MIN_FRR_THR': frr_at_thr,

    }
    return metric_dict    
