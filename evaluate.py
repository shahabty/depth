import torch
import numpy as np


def select_index(img_size):
    p1 = np.random.choice(img_size, int(img_size * 0.6), replace=False)
    np.random.shuffle(p1)
    p2 = np.random.choice(img_size, int(img_size * 0.6), replace=False)
    np.random.shuffle(p2)

    mask = p1 != p2
    p1 = p1[mask]
    p2 = p2[mask]
    p12_index = {'p1': p1, 'p2': p2}
    return p12_index

def weighted_human_disagreement_rate(gt, pred):
    p12_index = select_index(gt.size)
    gt_reshape = np.reshape(gt, gt.size)
    pred_reshape = np.reshape(pred, pred.size)
    gt_p1 = gt_reshape[p12_index['p1']]
    gt_p2 = gt_reshape[p12_index['p2']]
    pred_p1 = pred_reshape[p12_index['p1']]
    pred_p2 = pred_reshape[p12_index['p2']]

    gt_p2[gt_p2 == 0.] = 0.00001
    pred_p2[pred_p2 == 0.] = 0.00001
    gt_p12 = gt_p1 / gt_p2
    pred_p12 = pred_p1 / pred_p2

    l12_gt = np.zeros_like(gt_p12)
    l12_gt[gt_p12 > 1.02] = 1
    l12_gt[gt_p12 < 0.98] = -1

    l12_pred = np.zeros_like(pred_p12)
    l12_pred[pred_p12 > 1.02] = 1
    l12_pred[pred_p12 < 0.98] = -1

    err = np.sum(l12_gt != l12_pred)
    valid_pixels = gt_p1.size
    return err, valid_pixels



def evaluate_err(pred, gt, mask = None, scale=10.0 ):
    smoothed_criteria = {'err_absRel': 0.0, 'err_squaRel': 0.0, 'err_rms': 0.0,
                         'err_silog': 0.0, 'err_logRms': 0.0, 'err_silog2': 0.0,
                         'err_delta1': 0.0, 'err_delta2': 0.0, 'err_delta3': 0.0,
                         'err_log10': 0.0, 'err_whdr': 0.0}

    if type(pred).__module__ != np.__name__:
        pred = pred.cpu().numpy()
    if type(gt).__module__ != np.__name__:
        gt = gt.cpu().numpy()

    pred = np.squeeze(pred)
    gt = np.squeeze(gt)
    if mask is not None:
        gt = gt[mask[0]:mask[1], mask[2]:mask[3]]
        pred = pred[mask[0]:mask[1], mask[2]:mask[3]]
    if pred.shape != gt.shape:
        print('The shapes of dt and gt are not same!')
        return -1

    mask2 = gt > 0
    gt = gt[mask2]
    pred = pred[mask2]
    n_pxl = gt.size
    gt_scale = gt * scale
    pred_scale = pred * scale

    #Mean Absolute Relative Error
    rel = np.abs(gt - pred) / gt# compute errors
    abs_rel_sum = np.sum(rel)
    smoothed_criteria['err_absRel'] = np.float64(abs_rel_sum)

    #Square Mean Relative Error
    s_rel = ((gt_scale - pred_scale) * (gt_scale - pred_scale)) / (gt_scale * gt_scale)# compute errors
    squa_rel_sum = np.sum(s_rel)
    smoothed_criteria['err_squaRel'] = np.float64(squa_rel_sum)

    #Root Mean Square error
    square = (gt_scale - pred_scale) ** 2
    rms_squa_sum = np.sum(square)
    smoothed_criteria['err_rms'] = np.float64(rms_squa_sum)

    #Log Root Mean Square error
    log_square = (np.log(gt_scale) - np.log(pred_scale)) **2
    log_rms_sum = np.sum(log_square)
    smoothed_criteria['err_logRms'] = np.float64(log_rms_sum)

    # Scale invariant error
    diff_log = np.log(pred_scale) - np.log(gt_scale)
    diff_log_sum = np.sum(diff_log)
    smoothed_criteria['err_silog'] = np.float64(diff_log_sum)
    diff_log_2 = diff_log ** 2
    diff_log_2_sum = np.sum(diff_log_2)
    smoothed_criteria['err_silog2'] = np.float64(diff_log_2_sum)

    # Mean log10 error
    log10_sum = np.sum(np.abs(np.log10(gt) - np.log10(pred)))
    smoothed_criteria['err_log10'] = np.float64(log10_sum)
    #Delta
    gt_pred = gt_scale / pred_scale
    pred_gt = pred_scale / gt_scale
    gt_pred = np.reshape(gt_pred, (1, -1))
    pred_gt = np.reshape(pred_gt, (1, -1))
    gt_pred_gt = np.concatenate((gt_pred, pred_gt), axis=0)
    ratio_max = np.amax(gt_pred_gt, axis=0)

    delta_1_sum = np.sum(ratio_max < 1.25)
    smoothed_criteria['err_delta1'] = np.float64(delta_1_sum)
    delta_2_sum = np.sum(ratio_max < 1.25**2)
    smoothed_criteria['err_delta2'] = np.float64(delta_2_sum)
    delta_3_sum = np.sum(ratio_max < 1.25**3)
    smoothed_criteria['err_delta3'] = np.float64(delta_3_sum)

    # WHDR error
    whdr_err_sum, eval_num = weighted_human_disagreement_rate(gt_scale, pred_scale)
    smoothed_criteria['err_whdr'] = np.float64(whdr_err_sum)
    return smoothed_criteria,n_pxl,eval_num

