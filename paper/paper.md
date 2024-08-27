---
title: 'pybeepop+: A Python wrapper for the BeePop+ honey bee colony model'
tags:
  - honey bees
  - pesticides
  - Python
  - colony simulation
  - agent-based model
authors:
  - name: Jeffrey Minucci
    orcid: 0000-0001-5571-2599
    affiliation: 1
affiliations:
 - name: U.S. EPA, Office of Research and Development, Center for Public Health and Environmental Assessment, USA
   index: 1
date: 7 August 2024
bibliography: paper.bib
---

# Summary

Honey bees (*Apis mellifera* L.) provide critical pollination services
for both natural and agricultural systems, with $50 billion USD of crops
completely dependent on pollination in the United Statates alone [@reilly:2020]. However, honey bees are facing a wide 
range of stressors resulting in elevated colony failure rates including
climate change [@zapata:2024], pathogens [@evans:2011], habitat loss and 
decreased food availability [@donkersley:2014; @goulson:2015], and exposure to 
pesticides [@goulson:2015; @woodcock:2017]. Agent-based colony simulation models, such as the `BeePop+` model
developed by US EPA and USDA [@garber:2022], offer the opportunity to explore how
these interacting stressors may impact colony dynamics such as colony size, 
honey production and overwintering success across a variety of scenarios. 
Agent-based models can also produce emergent behavior that is typical of complex
systems such as eusocial bee colonies. These models can also be used to predict 
colony-level pesticide impacts based on toxicological information gathered from 
laboratory tests on single bees. The `pybeepop+` package for Python provides a convenient 
and modern interface for running `BeePop+` that facilitates greater adoption and
application by the scientific, academic, conservation, and industry community.


# Statement of need

The `BeePop+` colony simulation model was published in 2022 by the US EPA and USDA
to support the pesticide risk assessment process [@garber:2022]. `BeePop+` was an update to the 
existing USDA model `VarroaPop` [@degrandi-hoffman:2005], which added pesticide exposure and effects modeling
capabilities. `BeePop+` is an agent-based model which simulates dynamics such as queen
egg-laying behavior, development and food consumption of brood and adult bees, and
foraging activity patterns based on weather. Queens are simulated as individual agents,
while other castes are simulated as collective 'day-cohort' agents. Pesticide exposure
occurs via collection of contaminated pollen and nectar, with pesticide residue levels
set by the user via a daily residue file. Interactions with parasitic *Varroa destructor* mites
can also be simulated simultaneously. A sensitivity analysis of `BeePop+` input parameters
is available in @kuan:2018.

The `pybeepop+` Python package wraps the C++-based `BeePop+` model in an
easy to use application programing interface (API). Previously, the `BeePop+` model was only accessible via
build-in C++ interface functions [@curry:2022], or a web-based 
graphical user interface [@usda:2023].
The `pybeepop+` package is designed to provide a fast and user-friendly method
for running BeePop+ in Python, a programing language which is widely used in 
scientific settings. It also allows for rapid modification of BeePop+ parameter values and input files,
which enables automated, high-throughput analyses that require many hundreds 
or thousands of model runs. Model results are output as `pandas` [@pandas:2020] `DataFrame`
objects (or `JSON` strings), which facilitates downstream analysis and plotting.

An early version of the `pybeepop+` package was used to fit `BeePop+` to empirical
data from a honey bee colony feeding study using Bayesian inference [@minucci:2021].
The Python-native interface of `pybeepop+` allowed for integration with the `pyABC`
package [@klinger:2018] for sampling and `dask` [@dask] for parallelization of over 10
million individual model runs. The `pybeepop+` package is currently being used by
the US EPA to fit `BeePop+` to a range of colony feeding study datasets across several pesticides to explore the generalizability of the model. 

The `pybeepop+` package includes pre-compiled binary verisons of `BeePop+` for Windows
(64-bit) and Linux (Ubuntu). The package will try to detect your
platform and architecture and use the correct library binary. For Linux verisions
other than Ubuntu, `pybeepop+` will attempt to use the 
Ubuntu binary, but compatibility issues may occur. Alternately, `BeePop+` can be built
from source on any Linux system and `pybeepop+` can connect to an alternate shared
library binary specified by the user.

# Acknowledgements

We thank Tom Purucker, Deron Smith, and several anonymous reviewers for manuscript and code review and edits.
This paper has been reviewed in accordance with Agency policy and approved for 
publication. The views expressed in this article are those of the authors and
do not necessarily represent the views or policies of the US EPA. Any mention of trade names, 
products, or services does not imply an endorsement by the US EPA.

# References