import grpc
import protos.adapter_pb2
import protos.adapter_pb2_grpc


if __name__ == '__main__':
    channel = grpc.insecure_channel('localhost:50051')
    stub = protos.adapter_pb2_grpc.AdapterStub(channel)
    message = protos.adapter_pb2.Request(text="uci\n")
    response = stub.ExecuteEngineCommand(message)
    print(response.text)
