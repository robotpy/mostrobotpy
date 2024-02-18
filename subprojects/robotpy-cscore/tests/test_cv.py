import cscore as cs
import numpy as np


def test_empty_img():
    img = np.zeros(shape=(0, 0, 3))
    sink = cs.CvSink("something")
    _, rimg = sink.grabFrame(img)
    assert (rimg == img).all()


def test_nonempty_img():
    img = np.zeros(shape=(480, 640, 3), dtype=np.uint8)
    img2 = np.zeros(shape=(480, 640, 3), dtype=np.uint8)
    sink = cs.CvSink("something")
    _, img = sink.grabFrame(img)
    _, img = sink.grabFrame(img)
    assert (img == img2).all()
