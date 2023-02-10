from patterns import (
    Parameter,
    State,
    Table,
    Connection,
)
from contextlib import contextmanager
import matplotlib.pyplot as plt
import traceback
from matplotlib.pyplot import _get_backend_mod
import io


@contextmanager
def monkey_patch_matplotlib():
    def _p():
        m = _get_backend_mod()
        
    og = plt.show
    plt.show = lambda self: print(self)
    yield
    plt.show = og


def get_plot_result(py: str, data):
    print(py)
    error = None
    result = None
    def get_data():
        return data
    try:
        exec(py, {"get_data": get_data})
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print(e)
        try:
            error = str(e.__dict__['orig'])
        except KeyError:
            error = str(e)
    return buf
    #return PlotResult(python=py, result=result, error=error)


code = """
# import the necessary libraries
import matplotlib.pyplot as plt
import pandas as pd

data = get_data()

plt.style.use(plt.style.library['ggplot'])

# plot the data
plt.plot(list(range(2)), [r["b"] for r in data])

# set the title and labels
plt.title('Trend in Series A Dollars Over Last Five Years')
plt.xlabel('Year')
plt.ylabel('Raised Amount (USD)')

# show the plot
plt.show()
"""

data = [{"a": 1, "b": 2}, {"a": 1, "b": 2}]

buf = get_plot_result(code, data)

img = "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII"

import io
from slack_sdk import WebClient

# buf = io.BytesIO()
# buf.write(img.encode())
# buf.seek(0)


auth = Parameter("slack", type=Connection("slackbot"))
aws_secret = Parameter("aws_secret")
import boto3

def upload_image_s3(buf):
    client = boto3.client('s3', region_name='us-west-2', aws_access_key_id="AKIA4YJBXR25XPDISZEV", aws_secret_access_key=aws_secret)
    resp = client.upload_fileobj(buf, 'patterns-files', 'chart2.jpg')
    print(resp)

# slack = WebClient(token=auth["token"])
# resp = slack.files_upload_v2(
#     #channel="C03J9KE9KE0",
#     file=buf,
#     title="Test upload",
#     filename="test.png"
# )
#print(resp["files"][0]["id"])
#resp = slack.files_sharedPublicURL(file=resp["files"][0]["id"])
#print(resp)
upload_image_s3(buf)

