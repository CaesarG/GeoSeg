from torch.utils.data import DataLoader
from geoseg.losses import *
from geoseg.datasets.potsdam_dataset import *
from geoseg.models.UNetFormer import UNetFormer
from catalyst.contrib.nn import Lookahead
from catalyst import utils
import os

# training hparam
max_epoch = 45
ignore_index = len(CLASSES)
train_batch_size = 6
val_batch_size = 6
lr = 6e-4
weight_decay = 0.01
backbone_lr = 6e-5
backbone_weight_decay = 0.01
num_classes = len(CLASSES)
classes = CLASSES

backbone = "convnext_base.fb_in22k_ft_in1k_384"
test_time_aug = "d4"
output_mask_dir, output_mask_rgb_dir = None, None
weights_name = "unetformer-r18-512crop-ms-e45"
weights_path = "model_weights/potsdam/{}".format(weights_name)
test_weights_name = "unetformer-r18-512crop-ms-e45"
log_name = "potsdam/{}".format(weights_name)
monitor = "val_F1"
monitor_mode = "max"
save_top_k = 1
save_last = True
check_val_every_n_epoch = 1
pretrained_ckpt_path = None  # the path for the pretrained model weight
gpus = "auto"  # default or gpu ids:[0] or gpu nums: 2, more setting can refer to pytorch_lightning
resume_ckpt_path = None  # whether continue training with the checkpoint, default None

#  define the network
net = UNetFormer(num_classes=num_classes,backbone_name=backbone)

# define the loss
loss = UnetFormerLoss(ignore_index=ignore_index)
use_aux_loss = True

# define the dataloader
work_dirs = "/media/caesarg/Game2/mmsegmentation"

train_dataset = PotsdamDataset(
    data_root=os.path.join(work_dirs, "data/Potsdam"),
    mode="train",
    mosaic_ratio=0.25,
    img_dir="img_dir/train",
    mask_dir="ann_dir/train",
    img_suffix=".png",
    transform=train_aug,
)

val_dataset = PotsdamDataset(
    data_root=os.path.join(work_dirs, "data/Potsdam"),
    transform=val_aug,
    img_dir="img_dir/val",
    mask_dir="ann_dir/val",
    img_suffix=".png",
)
test_dataset = PotsdamDataset(
    data_root=os.path.join(work_dirs, "data/Potsdam"),
    transform=val_aug,
    img_dir="img_dir/val",
    mask_dir="ann_dir/val",
    img_suffix=".png",
)

train_loader = DataLoader(
    dataset=train_dataset,
    batch_size=train_batch_size,
    num_workers=4,
    pin_memory=True,
    shuffle=True,
    drop_last=True,
)

val_loader = DataLoader(
    dataset=val_dataset,
    batch_size=val_batch_size,
    num_workers=4,
    shuffle=False,
    pin_memory=True,
    drop_last=False,
)

# define the optimizer
layerwise_params = {
    "backbone.*": dict(lr=backbone_lr, weight_decay=backbone_weight_decay)
}
net_params = utils.process_model_params(net, layerwise_params=layerwise_params)
base_optimizer = torch.optim.AdamW(net_params, lr=lr, weight_decay=weight_decay)
optimizer = Lookahead(base_optimizer)
lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
    optimizer, T_0=15, T_mult=2
)
