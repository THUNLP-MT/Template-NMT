# A Template-based Method for Constrained Neural Machine Translation (EMNLP 2022)

## Introduction

We propose a template-based framework that can cope with both lexical and structural constraints for neural machine translation. We use [fairseq](https://github.com/facebookresearch/fairseq) to implement our method, and the commit code is `d5f7b50` (Mon Sep 21 13:45:35 2020 -0700). Our major modification is that we update the [generate.py](https://github.com/shuo-git/Template-NMT/blob/main/fairseq-pro/fairseq_cli/generate.py) to achieve prefix-based inference.

## Lexically Constrained Translation

### Data

We use [WMT17 En-Zh](https://www.statmt.org/wmt17/translation-task.html) and [WMT20 En-De](https://www.statmt.org/wmt20/translation-task.html) as our training sets. We use [En-Zh](http://nlp.csai.tsinghua.edu.cn/~ly/systems/TsinghuaAligner/TsinghuaAligner.html) and [En-De](https://github.com/lilt/alignment-scripts) alignment test sets for evaluation. We follow [Chen et al., (2021)](https://ojs.aaai.org/index.php/AAAI/article/view/17496) to extract the constraints.

### Build the templates

We use the script [prepare_template.py](https://github.com/shuo-git/Template-NMT/blob/main/lexical_scripts/prepare_template.py) to convert natural language sentences into template-based ones.

Prepare the template-based training data:
```
python prepare_template.py en zh train.bpe train.bpe.const.en-zh t2s
```
Prepare the template-based inference data:
```
python prepare_template.py en zh test.bpe test.bpe.const.en-zh t2s.infer
```

Here is an example:

Filename | Example
---|---
en | this approach , also adopted by italy , contributes to reducing costs and increasing the overall volume of funds for beneficiaries .
zh | 这种 方式 也 被 意大利 所 采用 。 它 有助于 降低成本 , 增加 受益人 收到 的 汇款 总额 。
const.en-zh | italy \|\|\| 意大利 \|\|\| approach \|\|\| 方式 \|\|\| increasing \|\|\| 增加 \|\|\|
t2s.en | [C0] italy [C1] approach [C2] increasing **[SEP]** [S0] [C1] [S1] [C0] [S2] [C2] [S3] **[SEP]** [S0] this [S1] , also adopted by [S2] , contributes to reducing costs and [S3] the overall volume of funds for beneficiaries .
t2s.zh | [C0] 意大利 [C1] 方式 [C2] 增加 **[SEP]** [T0] [C1] [T1] [C0] [T2] [C2] [T3] **[SEP]** [T0] 这种 [T1] 也 被 [T2] 所 采用 。 它 有助于 降低成本 , [T3] 受益人 收到 的 汇款 总额 。
t2s.infer.en | [C0] italy [C1] approach [C2] increasing **[SEP]** [S0] [C1] [S1] [C0] [S2] [C2] [S3] **[SEP]** [S0] this [S1] , also adopted by [S2] , contributes to reducing costs and [S3] the overall volume of funds for beneficiaries .
t2s.infer.zh | [C0] 意大利 [C1] 方式 [C2] 增加 **[SEP]**

### Training

#### Step 1: Binarize the training corpus
```
fairseq-preprocess \
    -s $src -t $tgt \
    --joined-dictionary --srcdict dict.${src}-${tgt}.txt \
    --trainpref train.bpe.t2s \
    --validpref valid.bpe.t2s \
    --destdir train-const-bin \
    --workers 128
```

#### Step 2: Model training
##### En-Zh \& Zh-En
```
CUDA_VISIBLE_DEVICES=0,1,2,3 fairseq-train train-const-bin \
    --fp16 --seed 32 --ddp-backend no_c10d \
    -s $src -t $tgt \
    --lr-scheduler inverse_sqrt --lr 0.0007 \
    --warmup-init-lr 1e-07 --warmup-updates 4000 \
    --max-update 200000 \
    --weight-decay 0.0 --clip-norm 0.0 --dropout 0.1 \
    --max-tokens 8192 --update-freq 1 \
    --arch transformer --share-all-embeddings \
    --optimizer adam --adam-betas '(0.9, 0.98)' \
    --save-dir ckpts \
    --tensorboard-logdir logs \
    --criterion label_smoothed_cross_entropy \
    --label-smoothing 0.1 \
    --no-progress-bar --log-format simple --log-interval 10 \
    --no-epoch-checkpoints \
    --save-interval-updates 1000 --keep-interval-updates 5 \
    |& tee -a logs/train.log
```
##### En-De \& De-En
```
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 fairseq-train train-const-bin \
    --fp16 --seed 32 --ddp-backend no_c10d \
    -s $src -t $tgt \
    --lr-scheduler inverse_sqrt --lr 0.0005 \
    --warmup-init-lr 1e-07 --warmup-updates 4000 \
    --max-update 300000 \
    --weight-decay 0.0 --clip-norm 0.0 --dropout 0.1 \
    --max-tokens 4096 --update-freq 1 \
    --arch transformer_vaswani_wmt_en_de_big --share-all-embeddings \
    --optimizer adam --adam-betas '(0.9, 0.98)' \
    --save-dir ckpts \
    --tensorboard-logdir logs \
    --criterion label_smoothed_cross_entropy \
    --label-smoothing 0.1 \
    --no-progress-bar --log-format simple --log-interval 10 \
    --no-epoch-checkpoints \
    --save-interval-updates 1000 --keep-interval-updates 5 \
    |& tee -a logs/train.log
```

### Inference

#### Step 1: Binarize the inference data
```
fairseq-preprocess \
    -s $src -t $tgt \
    --joined-dictionary --srcdict dict.${src}-${tgt}.txt \
    --testpref test.bpe.t2s.infer \
    --destdir infer-const-bin
```
#### Step 2: Model inference
```
genout=test
CUDA_VISIBLE_DEVICES=0 fairseq-generate infer-const-bin \
    -s $src -t $tgt \
    --gen-subset test \
    --path ${src}-${tgt}.pt \
    --lenpen 1.0 --beam 4 \
    --batch-size 128 \
    --prefix-size 1024 \
    > $genout
```

#### Step 3: Post-process
We use the script [restore_template.py](https://github.com/shuo-git/Template-NMT/blob/main/lexical_scripts/restore_template.py) to convert the template-based model output into natural language sentences.
```
grep ^H $genout |\
    sed 's/H-//g' | sort -k 1 -n -t ' ' | awk -F'\t' '{print $3}' > $genout.sort

python restore_template.py test.bpe.t2s.infer.$tgt $genout.sort $genout.bpe

cat $genout.bpe |\
    sed -r 's/(@@ )|(@@ ?$)//g' | tee $genout.tok |\
    perl mosesdecoder/scripts/tokenizer/detokenizer.perl -l $tgt > $genout.detok
```
#### Step 4: Evaluate
Calculate BLEU:
```
# English and German
cat $genout.detok | sacrebleu test.detok.$tgt | tee $genout.bleu
# Chinese
cat $genout.detok | sacrebleu -tok zh test.detok.$tgt | tee $genout.bleu
```
Calculate Exact Match, Window Overlap, and 1-TERm using [evaluate_term_plain.py](https://github.com/shuo-git/Template-NMT/blob/main/lexical_scripts/terminology_evaluation/evaluate_term_plain.py), which is adapted from [this repository](https://github.com/mahfuzibnalam/terminology_evaluation):
```
python terminology_evaluation/evaluate_term_plain.py \
    --language $tgt \
    --source test.$src \
    --target_reference test.$tgt \
    --const test.const.${src}-${tgt} \
    --hypothesis $genout.tok
```

## Structurally Constrained Translation

### Data

We conduct structurally constrained translation experiments on the dataset provided by [Hashimoto et al., (2019)](https://aclanthology.org/W19-5212).

### Build the templates

We use the script [prepare_template.py](https://github.com/shuo-git/Template-NMT/blob/main/structural_scripts/prepare_template.py) to convert natural language sentences into template-based ones.

Prepare the template-based training data:
```
python prepare_template.py en zh train.tag.spm t2s
```
Prepare the template-based inference data:
```
python prepare_template.py en zh dev.tag.spm t2s.infer
```

Here is an example:
Filename | Example
---|---
en | Let’s look at how faceting works with the number and chart widgets that we added to our \<ph\> classic designer \</ph\> \<ph\> dashboard \</ph\> .
zh | 让 我们 查看 多 面 化 如何 使用 添加到 \<ph\> 经 典 设计 器 \</ph\> \<ph\> 仪表板 \</ph\> 的 数字 和 图表 小部件 。
t2s.en | [S0] \<ph\> [S1] \</ph\> [S2] \<ph\> [S3] \</ph\> [S4] **[SEP]** [S0] Let’s look at how faceting works with the number and chart widgets that we added to our [S1] classic designer [S2] [S3] dashboard [S4] .
t2s.zh | [T0] \<ph\> [T1] \</ph\> [T2] \<ph\> [T3] \</ph\> [T4] **[SEP]** [T0] 让 我们 查看 多 面 化 如何 使用 添加到 [T1] 经 典 设计 器 [T2] [T3] 仪表板 [T4] 的 数字 和 图表 小部件 。
t2s.infer.en | [S0] \<ph\> [S1] \</ph\> [S2] \<ph\> [S3] \</ph\> [S4] **[SEP]** [S0] Let ’ s look at how faceting works with the number and chart widgets that we added to our [S1] classic designer [S2] [S3] dashboard [S4] .
t2s.infer.zh | [T0] \<ph\> [T1] \</ph\> [T2] \<ph\> [T3] \</ph\> [T4] **[SEP]**

### Training

#### Step 1: Binarize the training corpus

```
fairseq-preprocess \
    -s $src -t $tgt \
    --joined-dictionary --srcdict dict.${src}-${tgt}.txt \
    --trainpref train.tag.spm.t2s \
    --destdir train-bin \
    --workers 128
```

#### Step 2: Model training

```
CUDA_VISIBLE_DEVICES=0,1,2,3 fairseq-train train-bin \
    --fp16 --seed 32 --ddp-backend no_c10d \
    -s $src -t $tgt \
    --lr-scheduler cosine \
    --lr 1e-07 --max-lr 7e-4 \
    --warmup-init-lr 1e-07 --warmup-updates 8000 \
    --lr-shrink 1 --lr-period-updates 32000 \
    --max-update 40000 \
    --weight-decay 0.001 --clip-norm 0.0 \
    --dropout 0.2 --attention-dropout 0.2 --activation-dropout 0.2 \
    --max-tokens 8192 --update-freq 1 \
    --arch transformer --share-all-embeddings \
    --encoder-embed-dim 256 --decoder-embed-dim 256 \
    --encoder-ffn-embed-dim 1024 --decoder-ffn-embed-dim 1024 \
    --encoder-attention-heads 4 --decoder-attention-heads 4 \
    --encoder-layers 6 --decoder-layers 6 \
    --optimizer adam --adam-betas '(0.9, 0.98)' \
    --save-dir ckpts \
    --tensorboard-logdir logs \
    --criterion label_smoothed_cross_entropy \
    --label-smoothing 0.2 \
    --no-progress-bar --log-format simple --log-interval 10 \
    --no-epoch-checkpoints \
    --save-interval-updates 500 --keep-interval-updates 5 \
    |& tee -a $logs/train.log
```

### Inference

#### Step 1: Binarize the inference data

```
fairseq-preprocess \
    -s $src -t $tgt \
    --joined-dictionary --srcdict dict.${src}-${tgt}.txt \
    --testpref dev.tag.spm.t2s.infer \
    --destdir infer-bin
```

#### Step 2: Model inference
```
genout=output
CUDA_VISIBLE_DEVICES=0 fairseq-generate infer-bin \
    -s $src -t $tgt \
    --gen-subset test \
    --path ${src}-${tgt}.pt \
    --lenpen 1.0 --beam 4 \
    --prefix-size 1024 \
    --batch-size 128 > $genout
```

#### Step 3: Post-process

We use the script [restore_template.py](https://github.com/shuo-git/Template-NMT/blob/main/structural_scripts/restore_template.py) to convert the template-based model output into natural language sentences.
```
grep ^H $genout |\
    sed 's/H-//g' | sort -k 1 -n -t ' ' | awk -F'\t' '{print $3}' > $genout.sort
python restore_template.py $genout.sort $genout.spm
cat $genout.spm | spm_decode --model tag.spm.model > $genout.txt
```

#### Step 4: Evaluate

Prepare the json file using [convert2json.py](https://github.com/shuo-git/Template-NMT/blob/main/structural_scripts/convert2json.py), which is released by [this repository](https://github.com/salesforce/localization-xml-mt):
```
python convert2json.py \
    --input $genout.txt --output $genout.json \
    --lang $tgt --type translation --split dev 
```
Perform the evaluation using [evaluate.py](https://github.com/shuo-git/Template-NMT/blob/main/structural_scripts/evaluate.py), which is released by [this repository](https://github.com/salesforce/localization-xml-mt):
```
python evaluate.py --target ${src}${tgt}_${tgt}_dev.json \
    --translation $genout.json | tee $genout.res
```

## Contact

Please email [wangshuo.thu@gmail.com](mailto:wangshuo.thu@gmail.com) if you have any questions, suggestions, or bug reports :)

## Citation

Please cite as:
```
@inproceedings{Wang:2022:TemplateNMT,
  title = {A Template-based Method for Constrained Neural Machine Translation},
  author = {Wang, Shuo and Li, Peng and Tan, Zhixing and Tu, Zhaopeng and Sun, Maosong and Liu, Yang},
  booktitle = {Proceedings of EMNLP 2022},
  year = {2022},
}
```
