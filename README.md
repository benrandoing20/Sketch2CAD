# Sketch2CAD

A deep learning project for converting 2D sketches into 3D CAD representations. This project was originally developed as part of Stanford's CS231N course, exploring the application of convolutional neural networks to bridge the gap between hand-drawn sketches and parametric CAD models.

## Project Overview

Sketch2CAD aims to automate the process of translating 2D engineering sketches into fully parametric 3D CAD models. The system uses pre-trained convolutional neural networks (CNNs) combined with transformer-based decoders to learn the mapping from sketch images to CAD command sequences.

### Key Features

* Dual architecture implementation using both AlexNet and VGG11 as feature extractors
* Custom transformer decoder for generating CAD command sequences
* Integration with Autodesk Fusion 360 for data collection and validation
* Processing pipeline for extracting sketch and extrusion operations from CAD files
* Support for multiple geometric primitives: lines, circles, and arcs
* Handles both additive (NewBodyFeatureOperation) and subtractive (CutFeatureOperation) operations

## Architecture

### Model Components

The system consists of two main architectural variants:

**AlexNet-based Model**
* Uses a simplified AlexNet architecture for initial feature extraction
* Processes sketch images to extract spatial features
* Feeds extracted features into a custom decoder

**VGG11-based Model**
* Employs pre-trained VGG11 with frozen convolutional layers
* Custom fully connected layers for dimensionality reduction (4096 -> 512)
* BatchNorm and Dropout layers for regularization
* Transformer decoder with multi-head attention for sequence generation

### Decoder Architecture

The transformer decoder generates two types of outputs:
1. Command type predictions (6 classes): sketch plane selection, geometric primitives, extrusion operations
2. Command parameter predictions (16 parameters x 257 bins): coordinates, dimensions, and operation values

### Training Details

* Optimizer: Stochastic Gradient Descent (SGD) with momentum (0.9)
* Learning rate: 0.01
* Input image size: 224x224 (VGG), 100x100 (AlexNet)
* Batch size: 64
* Dataset split: 2000 samples for training, 1000 for validation, 1000 for testing
* Loss function: Cross-entropy for both command types and parameters

## Dataset

The dataset consists of CAD models extracted from Fusion 360 files:

* Total samples: 14,724 preprocessed CAD sequences (VGG) / 7,804 (AlexNet)
* Data format: CSV files mapping image filenames to CAD representations
* Images: PNG renders of 3D models from multiple viewpoints
* Labels: Structured CAD command sequences including:
  * Sketch plane (XY, XZ, YZ)
  * Geometric primitives (lines, circles, arcs)
  * Extrusion operations (distance, direction)

### Data Collection Pipeline

The data collection process uses custom Fusion 360 scripts:

1. **CollectData.py**: Processes JSON reconstruction files from CAD models
   * Extracts sketch and extrusion sequences
   * Filters invalid operations (ellipses, fitted splines)
   * Renders images at each construction step
   * Generates CSV metadata files

2. **LoadData.py**: Reconstructs CAD models from the processed representations
   * Creates sketches on appropriate construction planes
   * Generates geometric primitives with proper transformations
   * Applies extrusion operations
   * Exports validation images

## Project Structure

```
Sketch2CAD/
├── AlexNetSketch2CAD.ipynb       # AlexNet implementation notebook
├── VGGSketch2CAD.ipynb            # VGG11 implementation notebook
├── Data Creation Code/
│   ├── CollectData.py            # Fusion 360 data extraction script
│   └── LoadData.py               # Fusion 360 reconstruction script
├── proposal/
│   └── CS231N__Project_Proposal_2023.pdf
└── README.md
```

## Implementation Details

### Data Preprocessing

Images are normalized and transformed for the pre-trained VGG network:
* Resize to 256x256
* Center crop to 224x224
* Convert to tensor
* Invert pixel values (white background to black)
* Normalize using ImageNet statistics

### CAD Representation Format

Each CAD operation is encoded as a sequence of:
* Command type (one-hot encoded, 6 classes)
* Parameters (16 values, binned into 257 classes)
* Padding to fixed sequence length (60 operations)

Supported operations:
* Sketch plane selection (3 types)
* Line primitives (start/end coordinates)
* Circle primitives (center + radius)
* Arc primitives (start, center, sweep angle)
* Extrusion (operation type, extent type, distance)

## Requirements

### Python Dependencies
* PyTorch
* torchvision
* NumPy
* Pandas
* Pillow (PIL)
* Matplotlib

### External Software
* Autodesk Fusion 360 (for data collection and validation)
* Google Colab (recommended for training)

## Usage

### Training the Model

1. Mount Google Drive with dataset:
```python
from google.colab import drive
drive.mount('/content/drive')
```

2. Navigate to dataset directory and run either:
   * `AlexNetSketch2CAD.ipynb` for AlexNet-based model
   * `VGGSketch2CAD.ipynb` for VGG-based model

3. The trained decoder weights are saved as `decoder.pth`

### Data Collection

1. Install the Fusion 360 API scripts
2. Place CAD reconstruction JSON files in the `reconstruction/` directory
3. Run `CollectData.py` within Fusion 360 to:
   * Process JSON files
   * Generate renders at each step
   * Create CSV metadata files

4. Run `LoadData.py` to validate reconstructions

## Results and Performance

The model learns to:
* Identify appropriate sketch planes
* Generate geometric primitives (lines, circles, arcs)
* Predict extrusion parameters
* Sequence multiple operations correctly

Training metrics are tracked using cross-entropy loss for both command type and parameter prediction.

## Limitations

Current limitations include:
* Only processes first sketch-extrude pair from each CAD model
* Excludes ellipses and fitted splines
* Limited to simple extrusion operations (one-sided and symmetric)
* Fixed sequence length may truncate complex models
* Requires specific CAD file structure

## Future Work

Potential improvements:
* Support for multiple sketch-extrude sequences per model
* Additional geometric primitives (ellipses, splines)
* More complex extrusion operations (revolve, loft, sweep)
* Constraint prediction and enforcement
* End-to-end training without pre-binned parameters
* Real-time sketch-to-CAD conversion interface

## Acknowledgments

This project was developed as part of Stanford's CS231N: Convolutional Neural Networks for Visual Recognition course. The work builds upon research in sketch-based modeling, program synthesis, and neural CAD generation.

## License

This project was created for academic purposes as part of coursework at Stanford University.

## Repository Information

GitHub: https://github.com/benrandoing20/Sketch2CAD

For questions or collaboration opportunities, please refer to the original project proposal in the `proposal/` directory.
