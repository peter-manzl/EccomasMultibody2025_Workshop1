# Workshop on Machine Learning in Multibody System Dynamics

The workshop is a part of the [12th ECCOMAS Thematic Conference on Multibody Dynamics](https://www.uibk.ac.at/en/congress/multibody2025/). The conference will take place at the Technical Campus of the University of Innsbruck from July 13 to 18, 2025.

The [Workshop on machine learning in multibody systems](https://www.uibk.ac.at/en/congress/multibody2025/program/workshops/) will be held on **Sunday, July 13 (1:00 PM - 6:00 PM)**.

## Workshop Details

**Lecturers:**
[Grzegorz Orzechowski](https://www.lut.fi/en/profiles/grzegorz-orzechowski) ([LUT University](https://www.lut.fi/en)) and [Peter Manzl](https://www.uibk.ac.at/en/mechatronik/mekt/staff/) ([University of Innsbruck](https://www.uibk.ac.at/en/))

### Description

This hands-on workshop provides a comprehensive introduction to machine learning with a focus on deep learning applications for multibody systems. We give an overview and explore the available toolset for practitioners and researchers in the field of multibody dynamics, and practical applications are shown. This workshop is designed for interested researchers with little to no experience in machine learning and neural networks. Sessions will feature both theoretical information and individual coding for small tasks.

- **Session 1**: Get an introduction to machine learning with an overview of common problems and their associated standard solutions.
- **Session 2**: Explore supervised learning and how neural networks can be used to learn input-output mapping using labeled data from measurements or simulations.
- **Session 3**: Apply Reinforcement Learning (RL) to multibody systems and see how the need for labeled data is bypassed in RL by learning from the Interaction with the environment.
- **Session 4**: See the latest state-of-the-art Large Language Models (LLM), generative text-based models, and their application to the generation of multibody models. In context learning and prompt tuning are applied. The LLMs can be run either locally (if you have a strong laptop) or online using, e.g., ChatGPT or an online API.

### Requirements

Participants must bring their own laptop with Anaconda and Python (3.11) installed. We recommend using Python ≥ 3.10. Please note that some files will be distributed in Jupyter Notebook format.
Ideally, participants should have some basic experience with Python and the additional libraries like exudyn, matplotlib, jupyter, stable-baselines3, and pytorch already installed to get started quickly. 
Use ```pip install -r requirements.txt ``` to install all libraries required for the workshop. 

## Installation notes

For this workshop, we recommend that the participants have the current `Anaconda` distribution installed and configured. 

### Anaconda installation

[Anaconda](https://www.anaconda.com/) is one of the [Python](https://www.python.org/) distributions targeting data science and machine learning applications. To install `conda` in your system, we propose installing [Miniconda](https://docs.anaconda.com/miniconda/) – a minimal Anaconda distribution. To install it on your system, please follow the instructions at the official installation website [Installing Miniconda](https://docs.anaconda.com/miniconda/install/).

After successfully installing the Anaconda package, you should see a `(base)` prefix in your command line prompt, indicating that you are in the `base` virtual Python environment. With ```conda create -n py311 python=3.11``` you can create a new environment with the name _py311_ using Python 3.11 and  ```conda activate py311``` then activates the environment. Note that libraries are only installed for the current environment. 
In the file `requirements.txt` all libraries for this workshop and their respective versions are listed. Using ```pip install -r requirements.txt``` these libraries can be installed. 

<!--
not required anymore because this is part of the requirements
### Jupyter installation

We will install the [Jupyter](https://jupyter.org/) notebooks and lab interface in the `base` environment so that you can access them. 

Run the following in your `base` environment.

``` conda install jupyter conda install nb_conda_kernels ``` -->

