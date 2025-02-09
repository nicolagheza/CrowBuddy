# YOLOv5 Hyperparameter Evolution Results
# Best generation: 160
# Last generation: 313
#    metrics/precision,       metrics/recall,      metrics/mAP_0.5, metrics/mAP_0.5:0.95,         val/box_loss,         val/obj_loss,         val/cls_loss
#              0.96757,              0.95569,               0.9836,              0.75192,             0.019989,            0.0032185,            0.0020147

lr0: 0.01
lrf: 0.1
momentum: 0.937
weight_decay: 0.0005
warmup_epochs: 3.0
warmup_momentum: 0.8
warmup_bias_lr: 0.1
box: 0.05
cls: 0.3
cls_pw: 1.0
obj: 0.7
obj_pw: 1.0
iou_t: 0.2
anchor_t: 4.0
fl_gamma: 0.0
hsv_h: 0.093131
hsv_s: 0.012277
hsv_v: 0.0
degrees: 0.095213
translate: 0.14417
scale: 0.0
shear: 0.0
perspective: 0.0
flipud: 0.0
fliplr: 0.0
mosaic: 0.70553
mixup: 0.36718
copy_paste: 0.8501
anchors: 3.0
