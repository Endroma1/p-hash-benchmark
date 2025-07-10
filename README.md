# Benchmark for perceptual hashes in face recognition systems

This is a project created for a thesis by the following creators.
- Martin Hafstad
- Henrik (Endroma, Heste)
- Simen
- Thias

## How to use
Run app.py. Generate a config with --generate-config option with -d to give a directory of images. The available modification and modification methods are shown by using the --get-methods option, which creates the config.toml file with default options. To see what hashing and modification methods that are available, use the --get-methods option. To see all available options, use --help.

## Features
- Modifies images based on a set of modifications.
- Hashes two sets of images, the ones that are given with -g -d /dir and the TEST_IMG_FOLDER variable.
- Compares hamming distance between the modifications and original images.
- Calculate results based on calculation functions.

## To do
- Create scatterplot for result calc.
