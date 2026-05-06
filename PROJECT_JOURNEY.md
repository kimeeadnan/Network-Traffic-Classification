# Use Case 1 — Network Traffic Classification (NTC) walkthrough

As an introduction to **network traffic classification (NTC)**, I worked through a small end-to-end project based on a public GitHub repository. The upstream repo (course-style mini project) is here:

**Upstream repository:** [https://github.com/shivmohith/Network-Traffic-Classification](https://github.com/shivmohith/Network-Traffic-Classification/tree/master)

**My fork (Linux paths, fixed `requirements.txt`, histogram + SVM updates, this journey doc):** [https://github.com/kimeeadnan/Network-Traffic-Classification](https://github.com/kimeeadnan/Network-Traffic-Classification)

This project is deliberately **simple and straightforward**: it is framed around **network anomaly / intrusion-style thinking**—traffic is observed and the model tries to tell **benign (normal)** traffic from **malware** traffic. The method is classic ML: turn captures into **images**, extract **histogram features**, then train a **Support Vector Machine (SVM)**. You get both **binary** (benign vs malware) and **multiclass** (which of the 10+10 families) experiments.

In this document I explain things **as simply and as thoroughly as I can**, for my own understanding and for anyone else walking the same path. It includes:

- **Description** — what the problem is and what the repo does  
- **Dataset** — USTC-TFC2016, classes, L7 vs all layers  
- **Process** — clone, environment, data, PCAP → image → features → SVM, and what broke along the way  
- **Result** — numbers from my runs, compared to the original README claims  
- **Reference** — papers and repos  

I hope this note helps **me and others** build intuition for NTC, not just “run a script once.”

---

## Description (from the repo)

**Traffic classification** is an early step for **network anomaly detection** and **network-based intrusion detection**. It matters because traffic on a real network is a mix of **normal (benign)** flows and **malware-related** flows. Malicious or unwanted traffic can waste bandwidth, contribute to DoS-style effects, or harm receivers; separating **normal** from **malware** (and ideally naming the family) supports security monitoring and response.

This particular project does **not** classify raw packets directly in the ML step. Instead it:

1. Starts from **packet captures** (e.g. from **Wireshark** / `.pcap`).  
2. Converts them into **grayscale images** (pixel values 0–255) using the USTC-style preprocessing pipeline.  
3. Treats each image as a signal and computes a **histogram** over pixel intensities—the histogram bins are the **feature vector**.  
4. Trains an **SVM** on those features.

There are **two classification tasks**:

| Task | What it predicts |
|------|------------------|
| **Binary classification** | Benign **or** malware (two labels). |
| **Multiclass classification** | **Which** application/malware family (many labels; in our setup, **24** indexed classes matching the toolkit layout). |

The original README also describes two **data variants**: traffic represented using only the **application layer (L7)** vs **all OSI layers**. You should treat those as **separate experiments**: you regenerate images with the toolkit for one mode, build a dataset, train, then repeat for the other.

---

## Dataset (from the repo)

The standard dataset name is **USTC-TFC2016**. It contains both **benign** and **malware** traffic. The README summarizes **10 benign** and **10 malware** families (naming); the **preprocessing toolkit** ends up with a **24-folder** class index layout under `4_Png/Train/0` … `23` (order defined by the tool—not always identical to a simple alphabetical table, so always use the **same** toolkit run for labels and images).

| **Benign classes** | **Malware classes** |
| --- | --- |
| BitTorrent | Cridex |
| Facetime | Geodo |
| FTP | Htbot |
| GMail | Miuref |
| MySQL | Neris |
| Outlook | Nsis-ay |
| Skype | Shifu |
| SMB | Tinba |
| Weibo | Virut |
| World of Craft | Zeus |

**Two representations (important):**

- **L7 only** — features derived from traffic that emphasizes the **application layer**.  
- **All layers** — features derived from traffic that includes **more of the stack**, not only L7.

The same classification code can run on both, but the **PNGs must be regenerated** with the matching mode in the USTC scripts. If you mix “AllLayers PNGs” with code that assumes L7 (or the opposite), your results will not mean what you think.

**Where to get the data**

The **Network-Traffic-Classification** repo **does not ship the PCAPs**; the README only names the dataset. You obtain captures yourself, for example from:

- **USTC-TFC2016 (hosting / layout):** [https://github.com/davidyslu/USTC-TFC2016](https://github.com/davidyslu/USTC-TFC2016)  

Clone or download into a folder you control (example layout I used: a `data/USTC-TFC2016/` tree with benign/malware PCAPs). You still need the **USTC-TK2016** preprocessing tools (next section) to turn PCAPs into **sessions** and then **PNG** images.

---

## Process

### 1. Clone the classification project

Use the **repository root** URL. GitHub web links that end in `/tree/master` or `/blob/...` are **for browsing in the browser**, not for `git clone`.

**Correct:**

```bash
git clone https://github.com/shivmohith/Network-Traffic-Classification.git
cd Network-Traffic-Classification
```

**Incorrect (will fail):**

```bash
# Do NOT paste a /blob/master or /tree/master link as if it were a repo URL
git clone https://github.com/shivmohith/Network-Traffic-Classification/blob/master.git
```

The same rule applies when cloning **DeepTraffic** or any other repo: always clone the **`.git` URL of the repo root**, e.g. `https://github.com/echowei/DeepTraffic.git`.

---

### 2. Python virtual environment and dependencies

A virtual environment keeps packages for this project separate from your system Python.

```bash
cd /path/to/Network-Traffic-Classification
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

> **Tip — `pip` flags people mix up**  
> - **`-U` (upgrade):** reinstalls the listed package so you get a **current** version within your constraints, e.g. `pip install -U pip` upgrades the **pip** tool itself.  
> **`-r`:** read a **requirements file** and install every line, e.g. `pip install -r requirements.txt`.

On my machine I happened to name the folder `.ven` instead of `.venv`; the idea is the same—**one venv per project**, activate before running scripts.

---

### 3. Fixing `requirements.txt` (old repo reality)

The upstream project is from **2019**. PyPI package names and ecosystems have moved on. Typical fixes:

| Wrong or fragile | Use instead | Why |
| --- | --- | --- |
| `skimage` as the install name | **`scikit-image`** | The import is `skimage`, but the **package** to install is `scikit-image`. A bare `skimage` on PyPI is not what you want. |
| `PIL` in requirements | **`Pillow`** | You `import PIL`, but the installable distribution is **Pillow**. |
| Missing SVM dependency | **`scikit-learn`** | Provides `sklearn`; the code uses it for `SVC`, metrics, splits, etc. |
| Optional experiment tracking | **`wandb`** | If you want logged metrics and run comparison (optional). |

A **minimal sane** requirements set for the fork I used looks like:

```text
opencv-python
numpy
tqdm
pandas
scikit-image
scikit-learn
wandb
```

After editing, reinstall:

```bash
python -m pip install -r requirements.txt
```

---

### 4. Data collection and preprocessing (PCAP → PNG)

**4.1 Obtain PCAPs** (see [Dataset](#dataset-from-the-repo)): place them where the USTC toolkit expects them (follow the **USTC-TK2016** README / script layout—often `1_Pcap/`).

**4.2 Use the official preprocessing toolkit** from the DeepTraffic / USTC tooling (ubuntu-oriented branch in practice). Reference from the original README:

- [DeepTraffic — PreprocessedTools (USTC-TK2016)](https://github.com/echowei/DeepTraffic/tree/master/1.malware_traffic_classification/2.PreprocessedTools(USTC-TK2016))

On **Linux**, the `.ps1` scripts are run with **PowerShell** (`pwsh`) after installing PowerShell for your distro.

Example flow (from the **`USTC-TK2016`** directory; flags must match **L7 vs AllLayers**):

```bash
cd /path/to/USTC-TK2016
pwsh ./1_Pcap2Session.ps1 -s
pwsh ./2_ProcessSession.ps1 -l -u    # example: L7-oriented run; see toolkit docs for -a (all layers)
python3 3_Session2Png.py
```

For **all layers**, use the toolkit’s **all-layers** options (e.g. `-a` where applicable), then **re-run** `3_Session2Png.py` so **`4_Png`** matches.

You should end up with greyscale PNGs under something like:

`USTC-TK2016/4_Png/Train/<class_index>/*.png`

**4.3 Point the course repo at those PNGs**

The original Windows code used hardcoded paths like `D:\...`. A practical layout is:

- Put / symlink **`USTC-TK2016`** next to **`Network-Traffic-Classification`**, or  
- Set environment variables the scripts understand (in our fork: `NTC_TRAIN_DIR`, `NTC_LAYER`, `NTC_OUTPUT_CSV`, `NTC_DATASET_CSV`, etc.).

---

### 5. Feature extraction (histogram) and labels

Histogram scripts live under **`Pre-processing/`**. They read PNGs, compute **32-bin** histograms (per image), flatten to a row, and append **`label`**.

- **Multiclass:** e.g. `hist_L7_all_classes.py` → CSV with 32 features + integer class.  
- **Binary:** e.g. `hist_binary_from_png.py` → same features + **benign=1 / malware=0** (mapping derived from class index and the benign/malware split).

Activate the venv, then examples:

```bash
cd /path/to/Network-Traffic-Classification
source .venv/bin/activate

# Multiclass, L7 (default layout)
python3 Pre-processing/hist_L7_all_classes.py
python3 Classification/svm_multi.py

# Multiclass, AllLayers (env overrides)
NTC_LAYER=AllLayers \
  NTC_OUTPUT_CSV=dataset_all_layers_multiclass_bin32.csv \
  python3 Pre-processing/hist_L7_all_classes.py

NTC_LAYER=AllLayers \
  NTC_DATASET_CSV=dataset_all_layers_multiclass_bin32.csv \
  NTC_WANDB_TRAIN_NAME=svm_multiclass_all_layers_bin32 \
  python3 Classification/svm_multi.py

# Binary, L7
python3 Pre-processing/hist_binary_from_png.py
python3 Classification/svm_binary.py

# Binary, AllLayers
NTC_LAYER=AllLayers \
  NTC_OUTPUT_CSV=dataset_all_layers_binary_bin32.csv \
  python3 Pre-processing/hist_binary_from_png.py

NTC_LAYER=AllLayers \
  NTC_DATASET_CSV=dataset_all_layers_binary_bin32.csv \
  NTC_WANDB_TRAIN_NAME=svm_binary_all_layers_bin32 \
  python3 Classification/svm_binary.py
```

Generated CSV names we used (examples):

| CSV | Meaning |
| --- | --- |
| `dataset_L7_multiclass_bin32.csv` | L7 PNGs, 24-way labels |
| `dataset_all_layers_multiclass_bin32.csv` | All-layers PNGs, 24-way |
| `dataset_L7_binary_bin32.csv` | L7 PNGs, benign vs malware |
| `dataset_all_layers_binary_bin32.csv` | All-layers PNGs, binary |

> **Git note:** Large CSVs are often **gitignored** so the repo stays small; regenerate them locally with the commands above.

---

### 6. Problems I actually hit (so you can skip the detours)

1. **`FileNotFoundError` for `D:\...`** — the upstream script assumed Windows. **Fix:** paths relative to `USTC-TK2016/4_Png` + env overrides.  
2. **`ModuleNotFoundError: sklearn`** — **Fix:** `pip install scikit-learn` and add it to `requirements.txt`.  
3. **`skimage` install confusion** — **Fix:** install **`scikit-image`**, import `skimage` in code.  
4. **Broken `git clone` URLs** — copying `/tree/...` or `/blob/...` links. **Fix:** clone the **repo root** `.git` URL only.  
5. **L7 vs AllLayers mismatch** — training on features from one mode while thinking it was the other. **Fix:** one full toolchain pass per mode; matching `NTC_LAYER` when building CSVs.  
6. **pandas 2.x** — some `drop` patterns needed updating to `df.drop(columns=['label'])`.  
7. **Multiclass metrics warnings** — sklearn may warn when a class has **no predictions** or tiny support; read per-class precision/recall, not only accuracy.

---

### 7. High-level pipeline (visual)

```mermaid
flowchart LR
  PCAP[PCAP captures] --> A[USTC: Pcap → Session]
  A --> B[USTC: Session → PNG]
  B --> PNG[Greyscale images]
  PNG --> H[Histogram 32 bins]
  H --> CSV[Feature CSV + label]
  CSV --> SVM[SVM train / test]
  SVM --> WB[Optional: Weights & Biases]
```

---

## Result

### What the original README claimed

The upstream README states very high accuracy (**100%** binary, **98%** multiclass). Those numbers depend on **exact data split, features, and environment** from the author’s 2019 run. When you **reproduce on modern Python, Linux paths, and the same public dataset**, you should expect **similar trends** but **not necessarily identical percentages**.

### What I measured (my runs, bin size 32, linear SVM on histograms)

Rough data scale:

- **Multiclass:** about **95,856** train / **23,965** test samples, **24** classes, **32** features.  
- **Binary:** about **107,838** train / **11,983** test (stratified split in the script I used).

| Task | Layer mode | Test accuracy | Notes |
| --- | --- | --- | --- |
| Binary | L7 | **~95.65%** | Strong benign vs malware separation. |
| Binary | AllLayers | **~95.31%** | Similar to L7 for this feature choice. |
| Multiclass | L7 | **~79.60%** | Harder task; some classes noisier. |
| Multiclass | AllLayers | **~79.34%** | Same ballpark as L7 here. |

**Binary classification detail (why “~95%” is meaningful, not a fluke)**  
Example **L7 binary** test report (malware = 0, benign = 1):

| Class | Precision | Recall | F1 | Support (test) |
| --- | --- | --- | --- | --- |
| 0 malware | **0.99** | **0.93** | **0.96** | 6312 |
| 1 benign | **0.92** | **0.99** | **0.96** | 5671 |

So the model is not only accurate overall: **when it flags malware, it is usually right**, and **most benign traffic is found** (high recall on benign). All-layers binary was in the same band (~95%).

**Multiclass caveat**  
With only **32 histogram features**, some families look similar or have **fewer samples**; you may see **per-class** precision/recall collapse for rare labels. That is a **feature / data** limitation, not a mystery—it motivates richer models (e.g. CNNs on the images) or richer features.

**Experiment tracking**  
I logged runs with **Weights & Biases** for transparency (dataset size, accuracy, etc.):  
[https://wandb.ai/ahmadhakimiadnan-other/network-traffic-classification](https://wandb.ai/ahmadhakimiadnan-other/network-traffic-classification)

---

## Reference

- **Paper:** Wei Wang, Ming Zhu, *Malware Traffic Classification Using Convolutional Neural Network for Representation Learning*.  
- **Course-style repo:** [shivmohith/Network-Traffic-Classification](https://github.com/shivmohith/Network-Traffic-Classification)  
- **Dataset pointer:** [davidyslu/USTC-TFC2016](https://github.com/davidyslu/USTC-TFC2016)  
- **Preprocessing tooling (context):** [echowei/DeepTraffic](https://github.com/echowei/DeepTraffic) (USTC-TK2016 / PreprocessedTools path as in original README)

---

*End of Use Case 1 notes. If you extend this work, a natural “Use Case 2” is replacing histogram+SVM with a small CNN on the same PNGs and comparing calibration and per-class confusion matrices.*
