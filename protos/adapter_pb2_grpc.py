# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from . import adapter_pb2 as adapter__pb2


class AdapterStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.ExecuteEngineCommand = channel.unary_unary(
        '/Adapter/ExecuteEngineCommand',
        request_serializer=adapter__pb2.Request.SerializeToString,
        response_deserializer=adapter__pb2.Response.FromString,
        )


class AdapterServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def ExecuteEngineCommand(self, request, context):
    """
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_AdapterServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'ExecuteEngineCommand': grpc.unary_unary_rpc_method_handler(
          servicer.ExecuteEngineCommand,
          request_deserializer=adapter__pb2.Request.FromString,
          response_serializer=adapter__pb2.Response.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'Adapter', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
