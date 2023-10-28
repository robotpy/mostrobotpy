import cscore as cs
import numpy as np


def test_empty_img():
    img = np.zeros(shape=(0, 0, 3))
    sink = cs.CvSink("something")
    _, rimg = sink.grabFrame(img)
    assert (rimg == img).all()
