# terminology_evaluation

## Installation and Prerequisites

The script uses Python 3. You can simply run the following to clone this repository and install all of the above requirements:

~~~
git clone https://github.com/mahfuzibnalam/terminology_evaluation.git
cd terminology_evaluation
pip install -r requirements.txt
~~~

List of requirements:
  1. **stanza**
  2. **argparse**
  3. **sacrebleu**
  4. **bs4**
  5. **lxml** (need it for mac)

## Code
The main script is `evaluate_term_wmt.py` that receives the following arguments:

  1. --language - The language code (eg. fr for French) of the target language.
  2. --hypothesis - This is the hypothesis file. Example file: `data/en-fr.dev.txt.truecased.sgm`.
  3. --source - This is a file with the source references. An example file is provided at `data/dev.en-fr.en.sgm`
  4. --target_reference - This is a file with the target references. An example file is provided at `data/dev.en-fr.fr.sgm`
  5. --BLEU [True/False]. By default True. If True shows BLEU score.
  6. --EXACT_MATCH [True/False]. By default True. If True shows Exact Match score.
  7. --WINDOW_OVERLAP [True/False]. By default True. If True shows Window Overlap Score.
  8. --MOD_TER [True/False]. By default True. If True shows TERm score.
  9. --TER [True/False]. By default False. If True shows TER score.
  

## Example
You can test that your metrics work by running the following command on the sample data we provide.
~~~
python3 evaluate_term_wmt.py \
    --language fr \
    --hypothesis data/en-fr.dev.txt.truecased.sgm \
    --source data/dev.en-fr.en.sgm \
    --target_reference data/dev.en-fr.fr.sgm
~~~
Running the above command will:
* Download the French Stanza models, if they are not available locally already
* Compute four metrics and print the following:
~~~
BLEU score: 45.33867641150976
Exact-Match Statistics
        Total correct: 759
        Total wrong: 127
        Total correct (lemma): 15
        Total wrong (lemma): 0
Exact-Match Accuracy: 0.8590455049944506
Window Overlap Accuracy :
        Window 2:
        Exact Window Overlap Accuracy: 0.29693757867032844
        Window 3:
        Exact Window Overlap Accuracy: 0.2907071747339513
1 - TERm Score: 0.5976316319523398

~~~

Notes: 
* The computation of TER or TERm can take quite some time if your data has very long sentences.

# Publications
Please cite this papers:
~~~
@article{DBLP:journals/corr/abs-2106-11891,
  author    = {Md Mahfuz Ibn Alam and
               Antonios Anastasopoulos and
               Laurent Besacier and
               James Cross and
               Matthias Gall{\'{e}} and
               Philipp Koehn and
               Vassilina Nikoulina},
  title     = {On the Evaluation of Machine Translation for Terminology Consistency},
  journal   = {CoRR},
  volume    = {abs/2106.11891},
  year      = {2021},
  url       = {https://arxiv.org/abs/2106.11891},
  eprinttype = {arXiv},
  eprint    = {2106.11891},
  timestamp = {Wed, 30 Jun 2021 16:14:10 +0200},
  biburl    = {https://dblp.org/rec/journals/corr/abs-2106-11891.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}
~~~
