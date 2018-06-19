# Three Stream Action Recognition

### Prerequisites

* python2 or 3
* OpenCV 2.X or 3.X with ffmpeg
* CUDA + cuDNN (we used 9 and 7, respectively)
* OpenPose (and thus Caffe (all dependencies) + OpenCV, can be the previous one)
* Tensorflow (with Keras 2.15)
* Pillow
* numpy

### Custom Libraries

* gpu-flow (requires OpenCV 2.X)
* foveated-yolt (requires python2)

### Data

We made our own smaller split of the AVA dataset for quickly testing the architecture, you can download it
here:

For the AHA dataset you can download it here:
https://drive.google.com/drive/folders/11sfLyjtmtakF9kDzWEpAVwD5k4zjDkdV


For the UCF101 dataset you can get it here (only flow and pose are new, rgb has been generated by Feichtenhofer)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details