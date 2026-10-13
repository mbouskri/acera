

## Overview
<p align="center">
  <img src="https://github.com/mbouskri/acera/blob/master/code/images/ACERAICON.png" alt="alt text" width="86" height="86">
</p>

**ACERA**: A DNA multiple sequence alignment tool that uses the actor of a trained Actor Critic with Experience Replay model.

Because MSA is NP-complete under common scoring schemes, traditional software like ClustalW relies heavily on heuristic approximations. While a human can align short sequences intuitively by shifting nucleotides back and forth by hand, ACERA mimics this manual process using a trained **Actor-Critic with Experience Replay (ACER)** agent.

This repository hosts the **standalone desktop application** and its documentation.

---

## RL Methodology (In Brief)

The agent was trained by modeling sequence alignment as an interactive environment:
* **State:** A sliding window centered around the nucleotide and its immediate context.
* **Action:** Shifting a nucleotide or gap one position to the left, right, or keeping it in place.
* **Reward:** Positive for improving the alignment score relative to the previous step; negative otherwise.
* **Data Augmentation:** Random mutations were added to training sequences to reduce overfitting.

---

## Desktop Application

This application allows you to run alignments directly using the pre-trained RL model.

**Current Limitations:**  
* **Inference Only:** This repository contains the alignment desktop tool (training scripts are not included).
* **Capacity:** Best suited for **up to 3 DNA sequences** under **100 nucleotides each**. Performance and execution time increase on larger sequences or protein data.

---

## Key Results

* **Competitive Accuracy:** Achieved alignment scores equal to or higher than **ClustalW2** in most benchmark test cases.
* **Generalization:** Successfully handles sequence lengths larger than those encountered during model training.

---

## Downloads & Getting Started

No code compilation or setup is required.

1. **Download the Desktop App:** Download the installer executable directly from the repository [acera-installer](../../installer/).
2. **User Guide:** For step-by-step instructions on using the interface, refer to the included file in this repository [User Guide](../../code/User_Guide/).
