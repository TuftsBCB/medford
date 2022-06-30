# medford Parser

## The Medford Parser
This repository contains all source code for the Medford parser, written in Python (3.8) using the [Pydantic](https://github.com/samuelcolvin/pydantic/) library. The purpose of this parser is to either validate or compile all MEDFORD files to ensure they follow appropriate MEDFORD syntax (described below) such that they can accurately be converted into other output formats for transfer or submission to coral databases.

## Official Specification
Please see the official specification for further details, hosted on github [here](https://github.com/TuftsBCB/MEDFORD-Spec).

## Example MEDFORD Files
A repository of sample MEDFORD files is hosted [here](https://github.com/TuftsBCB/MEDFORD-examples). (Note: Out of date/Not compatible with current spec as of 04/13/22. Will be updated soon.)

## MEDFORD Abstract
The conference publication about the alpha version of MEDFORD is hosted on Polina Shpilker's personal site, [here](https://www.eecs.tufts.edu/~pshpil01/MEDFORD_CCIS.pdf). The abstract is also copied below.

Reproducibility of research is essential for science. However, in the way modern computational biology research is done, it is easy to lose track of small, but extremely critical, details. Key details, such as the specific version of a software used or iteration of a genome can easily be lost in the shuffle, or perhaps not noted at all. Much work is being done on the database and storage side of things, ensuring that there exists a space to store experiment-specific details, but current mechanisms for recording details are cumbersome for scientists to use. We propose a new metadata description language, named MEDFORD, in which scientists can record [or encode!] all details relevant to their research. Human-readable, easily-editable, and templatable, MEDFORD serves as a collection point for all notes that a researcher could find relevant to their research, be it for internal use or for future replication. MEDFORD has been applied to coral research, documenting research from RNA-seq analyses to photo collectionsHuman-readible metadata file format to consolidate research information such that it can be stored, updated, and submitted to databases without introducing a huge time investment overhead.

A preprint of a journal version of the MEDFORD paper is on the arXiv at https://arxiv.org/abs/2204.09610.

## Contributions & Thanks
Contributors to the development of MEDFORD are as follows:
Polina Shpilker (polina.shpilker@tufts.edu), John Freeman, Hailey McKelvie, Jill Ashey, Jay-Miguel Fonticella, Hollie Putnam, Jane Greenberg, Lenore Cowen (cowen@cs.tufts.edu), Alva Couch (couch@cs.tufts.edu) and Noah M. Daniels (noah_daniels@uri.edu)

Please contact Polina, Lenore, Alva, or Noah with any questions.

Thank you to initial seed funding from: NSF grant OAC-1939263.
