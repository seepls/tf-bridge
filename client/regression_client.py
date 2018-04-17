#!/usr/bin/env python2.7

"""A client that talks to tensorflow_model_server loaded with linear regression model.
The client generate random test data, queries the service with such data to get 
predictions, and calculates the inference error rate.
Typical usage example:
    python mnist_client.py --server=localhost:9000
"""

from __future__ import print_function

import sys
import threading

from grpc.beta import implementations
import requests
import numpy
import tensorflow as tf
from datetime import datetime 

from google.protobuf.json_format import MessageToDict, ParseDict
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2

tf.app.flags.DEFINE_string('server', 'tf-bridge.herokuapp.com:80', 'PredictionService host:port')
FLAGS = tf.app.flags.FLAGS

def do_inference(hostport):
  """Tests PredictionService with concurrent requests.
  Args:
    hostport: Host:port address of the PredictionService.
  Returns:
    pred values, ground truth labels, processing time 
  """
  # connect to server
  host, port = hostport.split(':')
  channel = implementations.insecure_channel(host, int(port))
  stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)

  # prepare request object 
  request = predict_pb2.PredictRequest()
  request.model_spec.name = 'default'
  request.model_spec.signature_name = 'prediction'

  # Randomly generate some test data 
  temp_data = numpy.random.randn(100, 3).astype(numpy.float32)
  data, label = temp_data, numpy.sum(temp_data * numpy.array([1,2,3]).astype(numpy.float32), 1)
  request.inputs['input'].CopyFrom(
      tf.contrib.util.make_tensor_proto(data, shape=data.shape))

  #get inference
  response = requests.post('http://' + hostport + '/tensor-bridge/v1/prediction',
                             json=MessageToDict(
                                 request,
                                 preserving_proto_field_name=True,
                                 including_default_value_fields=True))
  
  result = ParseDict(response.json(),
                       predict_pb2.PredictResponse(),
                       ignore_unknown_fields=True)


  # # make inference and clock the time 
  # now = datetime.now()
  # result = stub.Predict(request, 5.0)  # 5 seconds
  # waiting = datetime.now() - now

  return result, label

def main(_):

  if not FLAGS.server:
      print('please specify server host:port')
      return

  result, label = do_inference(FLAGS.server)
  print('Result is: ', result)
  print('Actual label is: ', label)

if __name__ == '__main__':
  tf.app.run()