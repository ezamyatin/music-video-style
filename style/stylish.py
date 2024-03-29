from glob import glob
from time import time
import os
import numpy as np
import colorsys

from scipy.misc import imread, imsave
import theano
from tqdm import tqdm

from style.fast_neural_style.transformer_net import get_transformer_net
from style.utils import floatX, load_and_preprocess_img, deprocess_img_and_save, preprocess_img
from utils import load_and_resize


prefix_path = ""

if "nemchenko" in os.getcwd():
    prefix_path = "/home/evgeny/music-video-style/"

model_pool = {
    prefix_path + 'data/models/wave': None,
    prefix_path + 'data/models/stained-glass': None,
    prefix_path + 'data/models/flames': None,
    prefix_path + 'data/models/udnie': None,
    prefix_path + 'data/models/cossacks': None,
}

print('NET INITIALIZATION')
print('MULTITHREADING NOT SUPPORTED!!!!')
X_ = theano.shared(np.array([[[[]]]], dtype=floatX))
NET_ = get_transformer_net(X_)
FUN_ = theano.function([], NET_.output)
print('DONE')


class NeuralModel:
    def __init__(self, model_path, batch_size=1):
        #self.identity = False
        #if model_path is None:
        #    self.identity = True
        #    return
        self.weights = model_path
        self.batch_size = batch_size

    def magic(self, image_batch):
        #if self.identity:
        #    return image_batch
        image_batch = np.concatenate([preprocess_img(i) for i in image_batch], axis=0)
        result = np.zeros_like(image_batch)
        NET_.load_weights(self.weights)
        for i in range(0, len(image_batch), self.batch_size):
            batch = image_batch[i:i+self.batch_size]
            X_.set_value(batch)
            output_batch = FUN_()
            result[i:i+len(batch)] = output_batch
        deprocessed = []
        for img in result:
            img = deprocess_img_and_save(img)
            deprocessed.append(img)
        deprocessed = np.array(deprocessed)
        return deprocessed


class NeuralProcessor:
    def __init__(self, model_collection_path):
        model_paths = glob(model_collection_path + '/*')
        # models = [None] * (len(model_paths) + 1)
        # models[0] = NeuralModel(None)
        models = [None] * (len(model_paths))
        for model_path in model_paths:
            assert model_path.endswith('.h5')
            n = int(os.path.basename(model_path)[:-3])
            models[n] = NeuralModel(model_path)

        if len(model_paths) == 0:
            print("model_paths is emtpy, check path to model")

        self.models = models

    def process(self, images, audio_analyze, callback=None):
        result = np.zeros_like(images)
        batches = [None] * len(self.models)
        n = len(self.models)
        audio_analyze1 = [None] * len(audio_analyze)
        for i, a in enumerate(audio_analyze):
            k1 = int(np.floor(a * (n-1)))
            k2 = int(np.ceil(a * (n-1)))
            if batches[k1] is None:
                batches[k1] = []
            batches[k1].append(i)
            if k1 == k2:
                audio_analyze1[i] = True
                continue
            if batches[k2] is None:
                batches[k2] = []
            batches[k2].append(i)

        for i, batch in tqdm(enumerate(batches), total=len(batches)):
            if batch is None: continue
            result_batch = self.models[i].magic(np.array([images[j] for j in batch]))
            c = np.abs(audio_analyze[batch]*(n-1) - i)
            c[:] = 0.5
            for t, j in enumerate(batch):
                if audio_analyze1[j]:
                    result[j] = result_batch[t]
                else:
                    result[j] += np.uint8(c[t] * result_batch[t])
            callback((i+1)/len(batches) * 100)
        return result


for name in model_pool:
    model_pool[name] = NeuralProcessor(name)


def process(frames_dir, audio_analyze, size, neural=False, colorize=False, brightify=False, callback=None):
    if neural:
        neural_process(frames_dir, audio_analyze, neural, size, callback)
    if colorize:
        color_process(frames_dir, audio_analyze, size)
    if brightify:
        bright_process(frames_dir, audio_analyze)


def neural_process(frames_dir, audio_analyze, neural, size, callback=None):
    if neural not in model_pool:
        model_pool[neural] = NeuralProcessor(neural)
    neural_processor = model_pool[neural]

    frame_files = sorted(glob(frames_dir + '/*'))
    assert len(audio_analyze) == len(frame_files)
    images = []
    for frame_file in frame_files:
        images.append(load_and_resize(frame_file, size))
    images = np.array(images)
    result = neural_processor.process(images, audio_analyze, callback)
    for img, file in zip(result, frame_files):
        imsave(file, img)


def colorizer(img, s_f):
    rgb_to_hsv = np.vectorize(colorsys.rgb_to_hsv)
    hsv_to_rgb = np.vectorize(colorsys.hsv_to_rgb)
    r, g, b = np.rollaxis(img, axis=-1)
    h, s, v = rgb_to_hsv(r, g, b)
    s_shape = s.shape
    s = s.reshape([len(s_f), s.shape[0] // len(s_f)] + list(s.shape[1:]))
    s *= s_f[:, np.newaxis, np.newaxis]
    s = s.reshape(s_shape)
    r, g, b = hsv_to_rgb(h, s, v)
    img = np.dstack((r, g, b))
    return img


def brightifier(img, s_f):
    img_shape = img.shape
    img = img.reshape([len(s_f), img.shape[0] // len(s_f)] + list(img.shape[1:]))
    img = img * s_f[:, np.newaxis, np.newaxis, np.newaxis]
    img = img.reshape(img_shape)
    return np.uint8(img)


def color_process(frames_dir, audio_analyze, size=None):
    frame_files = sorted(glob(frames_dir + '/*'))
    assert len(audio_analyze) == len(frame_files)
    batch_size = 50
    for i in tqdm(range(0, len(audio_analyze), batch_size)):
        frame_batch = frame_files[i:i + batch_size]
        desc_batch = audio_analyze[i:i + batch_size]
        img = np.concatenate([load_and_resize(f, size) for f in frame_batch], axis=0)
        img = colorizer(img, desc_batch)
        n = len(desc_batch)
        img = img.reshape([n, img.shape[0] // n] + list(img.shape[1:]))
        for j in range(len(frame_batch)):
            imsave(frame_batch[j], img[j])


def bright_process(frames_dir, audio_analyze, size=None):
    frame_files = sorted(glob(frames_dir + '/*'))
    assert len(audio_analyze) == len(frame_files)
    batch_size = 50
    for i in tqdm(range(0, len(audio_analyze), batch_size)):
        frame_batch = frame_files[i:i + batch_size]
        desc_batch = audio_analyze[i:i + batch_size]
        img = np.concatenate([load_and_resize(f, size) for f in frame_batch], axis=0)
        img = brightifier(img, desc_batch)
        n = len(desc_batch)
        img = img.reshape([n, img.shape[0] // n] + list(img.shape[1:]))
        for j in range(len(frame_batch)):
            imsave(frame_batch[j], img[j])
